from datetime import datetime, date
from flask_login import UserMixin
from . import db, login_manager
from sqlalchemy import func

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="clinician")  # 'admin' or 'clinician'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mrn = db.Column(db.String(32), unique=True, index=True)  # 病歷號(可選)
    name = db.Column(db.String(80), nullable=False)
    gender = db.Column(db.String(10))  # 'M'/'F'/'Other'
    dob = db.Column(db.Date)
    phone = db.Column(db.String(30))
    email = db.Column(db.String(120))
    address = db.Column(db.String(255))
    medical_history = db.Column(db.Text)  # 病史摘要
    note = db.Column(db.Text)             # 備註
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def age(self) -> int | None:
        if not self.dob:
            return None
        today = date.today()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

class VitalSign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), index=True, nullable=False)
    systolic = db.Column(db.Integer)     # 收縮壓 SBP
    diastolic = db.Column(db.Integer)    # 舒張壓 DBP
    heart_rate = db.Column(db.Integer)   # 心跳 HR
    spo2 = db.Column(db.Integer)         # 血氧 SpO2
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    patient = db.relationship("Patient", backref=db.backref("vitals", lazy="dynamic"))

class LabResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"), index=True, nullable=False)
    glucose = db.Column(db.Float)      # mg/dL
    hba1c = db.Column(db.Float)        # %
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    patient = db.relationship("Patient", backref=db.backref("labs", lazy="dynamic"))
