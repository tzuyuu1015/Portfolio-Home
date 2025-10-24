from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(*roles):
    def wrapper(view):
        @wraps(view)
        def inner(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if roles and current_user.role not in roles:
                abort(403)
            return view(*args, **kwargs)
        return inner
    return wrapper


def register_template_filters(app):
    @app.template_filter("default_if_none")
    def default_if_none(val, default="—"):
        return default if val is None or val == "" else val


# 報表用預設門檻（可之後做成系統設定）
BP_SYS_HIGH = 140
BP_DIA_HIGH = 90

# Lab 門檻
GLU_HIGH = 126.0     # 空腹血糖 異常 (mg/dL)
HBA1C_HIGH = 6.5     # 糖化血色素 異常 (%)
