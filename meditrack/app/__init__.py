from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from .utils import register_template_filters

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"   # 未登入導去 login


def create_app():
    from config import Config
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    # 藍圖註冊（⚠️ 只在這裡註冊一次，不要重複在外面註冊）
    from .routes import auth_bp, patient_bp, core_bp, reports_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(core_bp)
    app.register_blueprint(reports_bp)

    # Jinja filters / globals
    register_template_filters(app)

    return app
