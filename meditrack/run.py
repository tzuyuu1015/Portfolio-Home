from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash
import os

app = create_app()

# 第一次啟動自動建 DB 與預設管理者（admin/admin123）
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            role="admin",
            password_hash=generate_password_hash("admin123")
        )
        db.session.add(admin)
        db.session.commit()
        print(">> Seeded default admin (username=admin, password=admin123)")

if __name__ == "__main__":
    app.run(debug=True)
