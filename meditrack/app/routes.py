from flask import Blueprint, render_template, redirect, url_for, request, flash, Response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_

from .forms import LoginForm, PatientForm, VitalForm, LabForm
from .models import User, Patient, VitalSign, LabResult
from .utils import role_required, BP_SYS_HIGH, BP_DIA_HIGH, GLU_HIGH, HBA1C_HIGH
from . import db

# ---- Blueprints ----
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")
patient_bp = Blueprint("patient", __name__, url_prefix="/patients")
core_bp = Blueprint("core", __name__)
reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

# ---- Core ----


@core_bp.route("/")
@login_required
def index():
    # 你也可以改成 redirect 到 dashboard
    return redirect(url_for("patient.list_patients"))


@core_bp.route("/dashboard")
@login_required
def dashboard():
    # 1) 總病患數
    total_patients = db.session.query(func.count(Patient.id)).scalar() or 0

    # 2) 最新一次血壓 → 高血壓人數
    vs_sub = (
        db.session.query(
            VitalSign.patient_id,
            func.max(VitalSign.recorded_at).label("max_time")
        ).group_by(VitalSign.patient_id).subquery()
    )
    latest_vs = (
        db.session.query(VitalSign)
        .join(vs_sub, and_(
            VitalSign.patient_id == vs_sub.c.patient_id,
            VitalSign.recorded_at == vs_sub.c.max_time
        )).subquery()
    )
    hyper_count = (
        db.session.query(func.count())
        .select_from(latest_vs)
        .filter(or_(latest_vs.c.systolic >= BP_SYS_HIGH,
                    latest_vs.c.diastolic >= BP_DIA_HIGH))
        .scalar() or 0
    )

    # 3) 最新一次 Lab → 血糖異常人數
    lab_sub = (
        db.session.query(
            LabResult.patient_id,
            func.max(LabResult.recorded_at).label("max_time")
        ).group_by(LabResult.patient_id).subquery()
    )
    latest_lab = (
        db.session.query(LabResult)
        .join(lab_sub, and_(
            LabResult.patient_id == lab_sub.c.patient_id,
            LabResult.recorded_at == lab_sub.c.max_time
        )).subquery()
    )
    gly_count = (
        db.session.query(func.count())
        .select_from(latest_lab)
        .filter(or_(latest_lab.c.glucose >= GLU_HIGH,
                    latest_lab.c.hba1c >= HBA1C_HIGH))
        .scalar() or 0
    )

    hyper_pct = round(hyper_count / total_patients *
                      100, 1) if total_patients else 0.0
    gly_pct = round(gly_count / total_patients * 100,
                    1) if total_patients else 0.0

    # 4) 每週新增病患（近 10 週）— SQLite 寫法
    weekly_rows = (
        db.session.query(
            func.strftime('%Y-%W', Patient.created_at).label('year_week'),
            func.count(Patient.id)
        )
        .group_by('year_week')
        .order_by('year_week')
        .all()
    )
    labels = [r[0] for r in weekly_rows][-10:]
    values = [r[1] for r in weekly_rows][-10:]

    return render_template(
        "overview.html",
        total_patients=total_patients,
        hyper_count=hyper_count, hyper_pct=hyper_pct,
        gly_count=gly_count, gly_pct=gly_pct,
        labels=labels, values=values
    )

# ---- Auth ----


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("core.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
            username=form.username.data.strip()).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash("登入成功", "success")
            next_page = request.args.get("next") or url_for("core.index")
            return redirect(next_page)
        flash("帳號或密碼錯誤", "danger")
    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("已登出", "info")
    return redirect(url_for("auth.login"))

# ---- Patients ----


@patient_bp.route("/")
@login_required
def list_patients():
    q = request.args.get("q", "").strip()
    query = Patient.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Patient.name.ilike(
            like), Patient.mrn.ilike(like), Patient.phone.ilike(like)))
    patients = query.order_by(Patient.created_at.desc()).all()
    return render_template("dashboard.html", patients=patients, q=q)


@patient_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required("admin", "clinician")
def create_patient():
    form = PatientForm()
    if form.validate_on_submit():
        p = Patient(
            mrn=form.mrn.data or None,
            name=form.name.data,
            gender=form.gender.data or None,
            dob=form.dob.data,
            phone=form.phone.data or None,
            email=form.email.data or None,
            address=form.address.data or None,
            medical_history=form.medical_history.data or None,
            note=form.note.data or None,
        )
        db.session.add(p)
        db.session.commit()
        flash("已新增病患", "success")
        return redirect(url_for("patient.list_patients"))
    return render_template("patient_form.html", form=form, mode="create")


@patient_bp.route("/<int:pid>")
@login_required
def patient_detail(pid):
    p = Patient.query.get_or_404(pid)
    vitals = (VitalSign.query.filter_by(patient_id=pid).order_by(
        VitalSign.recorded_at.asc()).all())
    labs = (LabResult.query.filter_by(patient_id=pid).order_by(
        LabResult.recorded_at.asc()).all())

    bp_labels = [v.recorded_at.strftime("%Y-%m-%d %H:%M") for v in vitals]
    sbp_series = [v.systolic for v in vitals]
    dbp_series = [v.diastolic for v in vitals]
    hr_series = [v.heart_rate for v in vitals]
    spo2_series = [v.spo2 for v in vitals]

    lab_labels = [l.recorded_at.strftime("%Y-%m-%d %H:%M") for l in labs]
    glu_series = [l.glucose for l in labs]
    a1c_series = [l.hba1c for l in labs]

    return render_template(
        "patient_detail.html",
        patient=p,
        bp_labels=bp_labels, sbp_series=sbp_series, dbp_series=dbp_series,
        hr_series=hr_series, spo2_series=spo2_series,
        lab_labels=lab_labels, glu_series=glu_series, a1c_series=a1c_series,
        vitals=vitals, labs=labs,
        vital_form=VitalForm(), lab_form=LabForm()
    )


@patient_bp.route("/<int:pid>/vitals/new", methods=["POST"])
@login_required
@role_required("admin", "clinician")
def create_vital(pid):
    p = Patient.query.get_or_404(pid)
    form = VitalForm()
    if form.validate_on_submit():
        v = VitalSign(
            patient_id=p.id,
            systolic=form.systolic.data,
            diastolic=form.diastolic.data,
            heart_rate=form.heart_rate.data,
            spo2=form.spo2.data,
            recorded_at=form.recorded_at.data or datetime.utcnow(),
        )
        db.session.add(v)
        db.session.commit()
        flash("已新增生命徵象", "success")
    else:
        flash("生命徵象資料格式有誤，請確認。", "danger")
    return redirect(url_for("patient.patient_detail", pid=pid))


@patient_bp.route("/<int:pid>/labs/new", methods=["POST"])
@login_required
@role_required("admin", "clinician")
def create_lab(pid):
    p = Patient.query.get_or_404(pid)
    form = LabForm()
    if form.validate_on_submit():
        l = LabResult(
            patient_id=p.id,
            glucose=form.glucose.data,
            hba1c=form.hba1c.data,
            recorded_at=form.recorded_at.data or datetime.utcnow(),
        )
        db.session.add(l)
        db.session.commit()
        flash("已新增檢驗值", "success")
    else:
        flash("檢驗值資料格式有誤，請確認。", "danger")
    return redirect(url_for("patient.patient_detail", pid=pid))


@patient_bp.route("/<int:pid>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin", "clinician")
def edit_patient(pid):
    p = Patient.query.get_or_404(pid)
    form = PatientForm(obj=p)
    if form.validate_on_submit():
        form.populate_obj(p)
        db.session.commit()
        flash("已更新病患資料", "success")
        return redirect(url_for("patient.list_patients"))
    return render_template("patient_form.html", form=form, mode="edit", patient=p)


@patient_bp.route("/<int:pid>/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_patient(pid):
    p = Patient.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    flash("已刪除病患", "warning")
    return redirect(url_for("patient.list_patients"))

# ---- Reports ----


@reports_bp.route("/")
@login_required
def reports_index():
    return render_template("reports_index.html")


@reports_bp.route("/hypertension")
@login_required
def report_hypertension():
    q = request.args.get("q", "").strip()
    start = request.args.get("start")
    end = request.args.get("end")
    min_sys = request.args.get("min_sys", type=int) or BP_SYS_HIGH
    min_dia = request.args.get("min_dia", type=int) or BP_DIA_HIGH

    sub = (
        db.session.query(
            VitalSign.patient_id,
            func.max(VitalSign.recorded_at).label("max_time")
        ).group_by(VitalSign.patient_id).subquery()
    )
    latest = (
        db.session.query(VitalSign)
        .join(sub, and_(
            VitalSign.patient_id == sub.c.patient_id,
            VitalSign.recorded_at == sub.c.max_time
        )).subquery()
    )
    query = (
        db.session.query(Patient, latest.c.systolic, latest.c.diastolic, latest.c.heart_rate,
                         latest.c.spo2, latest.c.recorded_at)
        .join(latest, latest.c.patient_id == Patient.id)
        .filter(or_(latest.c.systolic >= min_sys, latest.c.diastolic >= min_dia))
    )

    if q:
        like = f"%{q}%"
        query = query.filter(or_(Patient.name.ilike(
            like), Patient.mrn.ilike(like), Patient.phone.ilike(like)))

    def to_dt(s):
        try:
            return datetime.strptime(s, "%Y-%m-%d")
        except Exception:
            return None

    if start and to_dt(start):
        query = query.filter(latest.c.recorded_at >= to_dt(start))
    if end and to_dt(end):
        query = query.filter(latest.c.recorded_at < to_dt(
            end).replace(hour=23, minute=59, second=59))

    rows = query.order_by(latest.c.recorded_at.desc()).all()

    return render_template(
        "report_hypertension.html",
        rows=rows, q=q, start=start or "", end=end or "", min_sys=min_sys, min_dia=min_dia
    )


@reports_bp.route("/hypertension.csv")
@login_required
def report_hypertension_csv():
    q = request.args.get("q", "").strip()
    start = request.args.get("start")
    end = request.args.get("end")
    min_sys = request.args.get("min_sys", type=int) or BP_SYS_HIGH
    min_dia = request.args.get("min_dia", type=int) or BP_DIA_HIGH

    sub = (
        db.session.query(
            VitalSign.patient_id,
            func.max(VitalSign.recorded_at).label("max_time")
        ).group_by(VitalSign.patient_id).subquery()
    )
    latest = (
        db.session.query(VitalSign)
        .join(sub, and_(
            VitalSign.patient_id == sub.c.patient_id,
            VitalSign.recorded_at == sub.c.max_time
        )).subquery()
    )
    query = (
        db.session.query(Patient, latest.c.systolic, latest.c.diastolic, latest.c.heart_rate,
                         latest.c.spo2, latest.c.recorded_at)
        .join(latest, latest.c.patient_id == Patient.id)
        .filter(or_(latest.c.systolic >= min_sys, latest.c.diastolic >= min_dia))
    )

    if q:
        like = f"%{q}%"
        query = query.filter(or_(Patient.name.ilike(
            like), Patient.mrn.ilike(like), Patient.phone.ilike(like)))

    def to_dt(s):
        try:
            return datetime.strptime(s, "%Y-%m-%d")
        except Exception:
            return None

    if start and to_dt(start):
        query = query.filter(latest.c.recorded_at >= to_dt(start))
    if end and to_dt(end):
        query = query.filter(latest.c.recorded_at < to_dt(
            end).replace(hour=23, minute=59, second=59))

    rows = query.order_by(latest.c.recorded_at.desc()).all()

    import csv
    import io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["建立時間", "病歷號", "姓名", "電話", "SBP",
                    "DBP", "HR", "SpO2", "測量時間"])
    for p, sbp, dbp, hr, sp, t in rows:
        writer.writerow([
            p.created_at.strftime("%Y-%m-%d %H:%M"),
            p.mrn or "", p.name, p.phone or "",
            sbp or "", dbp or "", hr or "", sp or "",
            t.strftime("%Y-%m-%d %H:%M") if t else ""
        ])
    return Response(
        buf.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=hypertension.csv"}
    )


@reports_bp.route("/glycemia")
@login_required
def report_glycemia():
    q = request.args.get("q", "").strip()
    start = request.args.get("start")
    end = request.args.get("end")
    min_glu = request.args.get("min_glu", type=float) or GLU_HIGH
    min_hba1c = request.args.get("min_hba1c", type=float) or HBA1C_HIGH

    sub = (
        db.session.query(
            LabResult.patient_id,
            func.max(LabResult.recorded_at).label("max_time")
        ).group_by(LabResult.patient_id).subquery()
    )
    latest = (
        db.session.query(LabResult)
        .join(sub, and_(
            LabResult.patient_id == sub.c.patient_id,
            LabResult.recorded_at == sub.c.max_time
        )).subquery()
    )
    query = (
        db.session.query(Patient, latest.c.glucose,
                         latest.c.hba1c, latest.c.recorded_at)
        .join(latest, latest.c.patient_id == Patient.id)
        .filter(or_(latest.c.glucose >= min_glu, latest.c.hba1c >= min_hba1c))
    )

    if q:
        like = f"%{q}%"
        query = query.filter(or_(Patient.name.ilike(
            like), Patient.mrn.ilike(like), Patient.phone.ilike(like)))

    def to_dt(s):
        try:
            return datetime.strptime(s, "%Y-%m-%d")
        except Exception:
            return None

    if start and to_dt(start):
        query = query.filter(latest.c.recorded_at >= to_dt(start))
    if end and to_dt(end):
        query = query.filter(latest.c.recorded_at < to_dt(
            end).replace(hour=23, minute=59, second=59))

    rows = query.order_by(latest.c.recorded_at.desc()).all()

    return render_template(
        "report_glycemia.html",
        rows=rows, q=q, start=start or "", end=end or "",
        min_glu=min_glu, min_hba1c=min_hba1c
    )


@reports_bp.route("/glycemia.csv")
@login_required
def report_glycemia_csv():
    q = request.args.get("q", "").strip()
    start = request.args.get("start")
    end = request.args.get("end")
    min_glu = request.args.get("min_glu", type=float) or GLU_HIGH
    min_hba1c = request.args.get("min_hba1c", type=float) or HBA1C_HIGH

    sub = (
        db.session.query(
            LabResult.patient_id,
            func.max(LabResult.recorded_at).label("max_time")
        ).group_by(LabResult.patient_id).subquery()
    )
    latest = (
        db.session.query(LabResult)
        .join(sub, and_(
            LabResult.patient_id == sub.c.patient_id,
            LabResult.recorded_at == sub.c.max_time
        )).subquery()
    )
    query = (
        db.session.query(Patient, latest.c.glucose,
                         latest.c.hba1c, latest.c.recorded_at)
        .join(latest, latest.c.patient_id == Patient.id)
        .filter(or_(latest.c.glucose >= min_glu, latest.c.hba1c >= min_hba1c))
    )

    if q:
        like = f"%{q}%"
        query = query.filter(or_(Patient.name.ilike(
            like), Patient.mrn.ilike(like), Patient.phone.ilike(like)))

    def to_dt(s):
        try:
            return datetime.strptime(s, "%Y-%m-%d")
        except Exception:
            return None

    if start and to_dt(start):
        query = query.filter(latest.c.recorded_at >= to_dt(start))
    if end and to_dt(end):
        query = query.filter(latest.c.recorded_at < to_dt(
            end).replace(hour=23, minute=59, second=59))

    rows = query.order_by(latest.c.recorded_at.desc()).all()

    import csv
    import io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["建立時間", "病歷號", "姓名", "電話",
                    "Glucose(mg/dL)", "HbA1c(%)", "檢驗時間"])
    for p, glu, a1c, t in rows:
        writer.writerow([
            p.created_at.strftime("%Y-%m-%d %H:%M"),
            p.mrn or "", p.name, p.phone or "",
            glu if glu is not None else "",
            a1c if a1c is not None else "",
            t.strftime("%Y-%m-%d %H:%M") if t else ""
        ])
    return Response(
        buf.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=glycemia.csv"}
    )
@reports_bp.route("/overdue")
@login_required
def report_overdue():
    """
    未回診清單：計算每位病患最近一次活動時間
    (max(最新Vital時間, 最新Lab時間, 病患建立時間))，超過 days 天未更新者列出。
    支援參數：days(預設30), q(關鍵字: 姓名/病歷號/電話)
    """
    q = request.args.get("q", "").strip()
    days = request.args.get("days", type=int) or 30
    cutoff = datetime.utcnow() - timedelta(days=days)

    # 最新 Vital / Lab 的子查詢
    vsub = (
        db.session.query(
            VitalSign.patient_id.label("pid"),
            func.max(VitalSign.recorded_at).label("vtime")
        ).group_by(VitalSign.patient_id).subquery()
    )
    lsub = (
        db.session.query(
            LabResult.patient_id.label("pid"),
            func.max(LabResult.recorded_at).label("ltime")
        ).group_by(LabResult.patient_id).subquery()
    )

    # 取每人最後活動時間：SQLite 的 MAX(x,y,...) 會回傳較晚的那個
    last_activity_expr = func.max(
        func.coalesce(vsub.c.vtime, Patient.created_at),
        func.coalesce(lsub.c.ltime, Patient.created_at),
        Patient.created_at
    ).label("last_activity")

    query = (
        db.session.query(Patient, last_activity_expr)
        .outerjoin(vsub, vsub.c.pid == Patient.id)
        .outerjoin(lsub, lsub.c.pid == Patient.id)
        .group_by(Patient.id)
    )

    if q:
        like = f"%{q}%"
        query = query.filter(or_(Patient.name.ilike(like), Patient.mrn.ilike(like), Patient.phone.ilike(like)))

    # 過濾超過 cutoff 未更新
    rows = (
        query
        .having(last_activity_expr < cutoff)
        .order_by(last_activity_expr.asc())
        .all()
    )

    # 計算天數
    def days_since(dt):
        return (datetime.utcnow() - dt).days if dt else None

    items = [
        {
            "patient": p,
            "last_activity": la,
            "days_since": days_since(la)
        }
        for p, la in rows
    ]

    return render_template("report_overdue.html", items=items, q=q, days=days)

@reports_bp.route("/overdue.csv")
@login_required
def report_overdue_csv():
    q = request.args.get("q", "").strip()
    days = request.args.get("days", type=int) or 30
    cutoff = datetime.utcnow() - timedelta(days=days)

    vsub = (
        db.session.query(
            VitalSign.patient_id.label("pid"),
            func.max(VitalSign.recorded_at).label("vtime")
        ).group_by(VitalSign.patient_id).subquery()
    )
    lsub = (
        db.session.query(
            LabResult.patient_id.label("pid"),
            func.max(LabResult.recorded_at).label("ltime")
        ).group_by(LabResult.patient_id).subquery()
    )

    last_activity_expr = func.max(
        func.coalesce(vsub.c.vtime, Patient.created_at),
        func.coalesce(lsub.c.ltime, Patient.created_at),
        Patient.created_at
    ).label("last_activity")

    query = (
        db.session.query(Patient, last_activity_expr)
        .outerjoin(vsub, vsub.c.pid == Patient.id)
        .outerjoin(lsub, lsub.c.pid == Patient.id)
        .group_by(Patient.id)
    )

    if q:
        like = f"%{q}%"
        query = query.filter(or_(Patient.name.ilike(like), Patient.mrn.ilike(like), Patient.phone.ilike(like)))

    rows = (
        query
        .having(last_activity_expr < cutoff)
        .order_by(last_activity_expr.asc())
        .all()
    )

    # 輸出 CSV
    import csv, io
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["病歷號", "姓名", "電話", "最後活動時間", f"未更新天數(>{days})"])
    now = datetime.utcnow()
    for p, la in rows:
        writer.writerow([
            p.mrn or "", p.name, p.phone or "",
            la.strftime("%Y-%m-%d %H:%M") if la else "",
            (now - la).days if la else ""
        ])
    return Response(
        buf.getvalue(),
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=overdue_{days}d.csv"}
    )
