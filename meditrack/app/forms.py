from wtforms import FloatField, IntegerField
from wtforms.fields import DateTimeLocalField
from wtforms.validators import NumberRange
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional, Email


class LoginForm(FlaskForm):
    username = StringField("帳號", validators=[DataRequired(), Length(max=64)])
    password = PasswordField("密碼", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("登入")


class PatientForm(FlaskForm):
    mrn = StringField("病歷號", validators=[Optional(), Length(max=32)])
    name = StringField("姓名", validators=[DataRequired(), Length(max=80)])
    gender = SelectField("性別", choices=[
                         ("", "不指定"), ("M", "男"), ("F", "女"), ("Other", "其他")], validators=[Optional()])
    dob = DateField("生日(YYYY-MM-DD)", format="%Y-%m-%d",
                    validators=[Optional()])
    phone = StringField("電話", validators=[Optional(), Length(max=30)])
    email = StringField("Email", validators=[
                        Optional(), Email(), Length(max=120)])
    address = StringField("地址", validators=[Optional(), Length(max=255)])
    medical_history = TextAreaField(
        "病史摘要", validators=[Optional(), Length(max=5000)])
    note = TextAreaField("備註", validators=[Optional(), Length(max=5000)])
    submit = SubmitField("儲存")


class VitalForm(FlaskForm):
    systolic = IntegerField(
        "SBP", validators=[Optional(), NumberRange(min=50, max=300)])
    diastolic = IntegerField(
        "DBP", validators=[Optional(), NumberRange(min=30, max=200)])
    heart_rate = IntegerField(
        "HR", validators=[Optional(), NumberRange(min=20, max=250)])
    spo2 = IntegerField("SpO₂", validators=[
                        Optional(), NumberRange(min=50, max=100)])
    recorded_at = DateTimeLocalField(
        "測量時間", format="%Y-%m-%dT%H:%M", validators=[Optional()])
    submit = SubmitField("新增生命徵象")


class LabForm(FlaskForm):
    glucose = FloatField(
        "Glucose (mg/dL)", validators=[Optional(), NumberRange(min=0, max=1000)])
    hba1c = FloatField("HbA1c (%)", validators=[
                       Optional(), NumberRange(min=0, max=25)])
    recorded_at = DateTimeLocalField(
        "檢驗時間", format="%Y-%m-%dT%H:%M", validators=[Optional()])
    submit = SubmitField("新增檢驗值")
