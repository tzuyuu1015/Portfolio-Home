# seed_labs.py
from app import create_app, db
from app.models import Patient, LabResult
from datetime import datetime, timedelta
import random

app = create_app()
with app.app_context():
    patients = Patient.query.all()
    if not patients:
        print("請先建立幾位病患再執行本腳本。")
    else:
        now = datetime.utcnow()
        for p in patients:
            lr = LabResult(
                patient_id=p.id,
                glucose=random.choice([110, 118, 125, 130, 142]),
                hba1c=random.choice([5.9, 6.2, 6.7, 7.1]),
                recorded_at=now - timedelta(days=random.randint(0, 14))
            )
            db.session.add(lr)
        db.session.commit()
        print("已為每位病患新增一筆隨機 Lab 資料")
