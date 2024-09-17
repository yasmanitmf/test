import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from app.models import User


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

    def validate_password(self, field):
        password = field.data
        errors = []

        if len(password) < 8:
            errors.append('Password must be at least 8 characters long.')
        if not re.search(r"[A-Z]", password):
            errors.append('Password must contain at least one uppercase letter.')
        if not re.search(r"[a-z]", password):
            errors.append('Password must contain at least one uppercase letter.')
        if not re.search(r"\d", password):
            errors.append('Password must contain at least one digit.')
        if not re.search(r"\W", password):
            errors.append('Password must contain at least one special character.')

        if errors:
            raise ValidationError(errors)


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')
