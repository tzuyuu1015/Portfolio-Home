# seed_demo.py
"""
建立 12 位示範病患，並為每位塞入 2~4 筆血壓(vitals)與 1~2 筆血糖(labs)，
其中會刻意放幾筆超過門檻（SBP>=140 或 DBP>=90；GLU>=126 或 HbA1c>=6.5）
方便你直接在 Reports 看到結果。
"""
from datetime import datetime, timedelta
import random
from faker import Faker

from app import create_app, db
from app.models import Patient, VitalSign, LabResult

fake = Faker("zh_TW")  # 產生台灣格式的名字、地址、電話

def upsert_patients(n=12):
    # 若已經有資料就跳過建立，以免重複
    if Patient.query.count() >= n:
        print(f"已存在 {Patient.query.count()} 位病患，跳過建立。")
        return

    for _ in range(n):
        p = Patient(
            mrn=str(fake.random_number(digits=8, fix_len=True)),
            name=fake.name(),
            gender=random.choice(["M", "F", None]),
            dob=fake.date_of_birth(minimum_age=18, maximum_age=90),
            phone=fake.phone_number(),
            email=fake.email(),
            address=fake.address().replace("\n", " "),
            medical_history=random.choice(["HTN", "DM", "HTN + DM", ""]),
            note=""
        )
        db.session.add(p)
    db.session.commit()
    print(f"建立 {n} 位病患完成。")

def seed_vitals():
    patients = Patient.query.all()
    now = datetime.utcnow()
    total = 0
    for p in patients:
        k = random.randint(2, 4)  # 每人 2~4 筆
        for i in range(k):
            # 正常值周邊，隨機給幾筆異常
            if random.random() < 0.35:
                sbp = random.randint(145, 170)  # 故意高
                dbp = random.randint(92, 105)
            else:
                sbp = random.randint(110, 138)
                dbp = random.randint(70, 88)
            vs = VitalSign(
                patient_id=p.id,
                systolic=sbp,
                diastolic=dbp,
                heart_rate=random.randint(60, 100),
                spo2=random.randint(95, 100),
                recorded_at=now - timedelta(days=random.randint(0, 20), hours=random.randint(0, 23))
            )
            db.session.add(vs)
            total += 1
    db.session.commit()
    print(f"已新增 {total} 筆 VitalSign。")

def seed_labs():
    patients = Patient.query.all()
    now = datetime.utcnow()
    total = 0
    for p in patients:
        k = random.randint(1, 2)  # 每人 1~2 筆
        for i in range(k):
            if random.random() < 0.35:
                glu = random.uniform(128, 180)   # 故意高
                a1c = random.uniform(6.6, 8.2)
            else:
                glu = random.uniform(90, 119)
                a1c = random.uniform(5.4, 6.2)
            lr = LabResult(
                patient_id=p.id,
                glucose=round(glu, 1),
                hba1c=round(a1c, 1),
                recorded_at=now - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
            )
            db.session.add(lr)
            total += 1
    db.session.commit()
    print(f"已新增 {total} 筆 LabResult。")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
        upsert_patients(12)
        seed_vitals()
        seed_labs()
        print("✅ Demo 資料建立完成！可以到 /reports 檢視")
