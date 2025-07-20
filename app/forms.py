# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, RadioField, MultipleFileField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User
from flask_wtf.file import FileAllowed

class RegistrationForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mật khẩu', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Xác nhận mật khẩu', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Đăng ký')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Tên đăng nhập đã tồn tại. Vui lòng chọn tên khác.')
            

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email đã được sử dụng. Vui lòng chọn email khác.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mật khẩu', validators=[DataRequired()])
    remember = BooleanField('Ghi nhớ đăng nhập')
    submit = SubmitField('Đăng nhập')

class TicketForm(FlaskForm):
    title = StringField('Tiêu đề', validators=[DataRequired(), Length(max=100)])
    # Thêm coerce=int vào category_id
    category_id = SelectField('Thể loại', coerce=int, validators=[DataRequired()])
    description = TextAreaField('Mô tả sự cố', validators=[DataRequired()])
    priority = SelectField('Độ ưu tiên', choices=[('low', 'Thấp'), ('medium', 'Trung bình'), ('high', 'Cao')], validators=[DataRequired()])
    attachments = MultipleFileField('File đính kèm', validators=[
        FileAllowed(['jpg', 'png', 'gif', 'jpeg', 'pdf', 'txt', 'doc', 'docx'], 'Chỉ cho phép file ảnh, pdf, văn bản!')
    ])
    submit = SubmitField('Gửi yêu cầu')

class UpdateTicketForm(FlaskForm):
    status = SelectField('Trạng thái', choices=[('open', 'Mới'), ('in_progress', 'Đang xử lý'), ('closed', 'Đã đóng')], validators=[DataRequired()])
    assigned_to = SelectField('Giao cho', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Cập nhật')

class UpdateUserForm(FlaskForm):
    username = StringField('Tên đăng nhập', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    # THÊM CÁC TRƯỜNG MỚI
    full_name = StringField('Họ và tên', validators=[DataRequired(), Length(max=100)])
    phone_number = StringField('Số điện thoại')
    department = StringField('Phòng ban')
    # ------------------
    role = SelectField('Quyền', choices=[('user', 'User'), ('support', 'Support'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Cập nhật')

    def __init__(self, original_username, original_email, *args, **kwargs):
        super(UpdateUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username
        self.original_email = original_email

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Tên đăng nhập này đã tồn tại.')

    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Email này đã được sử dụng.')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Mật khẩu hiện tại', validators=[DataRequired()])
    new_password = PasswordField('Mật khẩu mới', validators=[DataRequired(), Length(min=6)])
    confirm_new_password = PasswordField('Xác nhận mật khẩu mới', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Đổi mật khẩu')

# THÊM FORM MỚI
class CommentForm(FlaskForm):
    content = TextAreaField('Nội dung trả lời', validators=[DataRequired()])
    submit = SubmitField('Gửi')
    
        
# File: app/forms.py
# Thêm class này vào cuối file
class RatingForm(FlaskForm):
    rating = RadioField(
        'Đánh giá', 
        choices=[(5, 'Tuyệt vời'), (4, 'Tốt'), (3, 'Bình thường'), (2, 'Tệ'), (1, 'Rất tệ')],
        validators=[DataRequired()],
        coerce=int
    )
    feedback = TextAreaField('Góp ý của bạn')
    submit = SubmitField('Gửi đánh giá')

class AdminCreateUserForm(RegistrationForm):
    # THÊM CÁC TRƯỜNG MỚI
    full_name = StringField('Họ và tên', validators=[DataRequired(), Length(max=100)])
    phone_number = StringField('Số điện thoại')
    department = StringField('Phòng ban')
    # ------------------
    role = SelectField('Quyền', 
                       choices=[('user', 'User'), ('support', 'Support'), ('admin', 'Admin')], 
                       validators=[DataRequired()])
    submit = SubmitField('Tạo người dùng')