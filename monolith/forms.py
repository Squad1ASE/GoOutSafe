from flask_wtf import FlaskForm
import wtforms as f
from wtforms.validators import DataRequired, Length, Email


class LoginForm(FlaskForm):
    email = f.StringField('email', validators=[DataRequired(), Length(1, 64), Email()])    
    password = f.PasswordField('password', validators=[DataRequired(), Length(1,8)])
    display = ['email', 'password']


class UserForm(FlaskForm):
    email = f.StringField('email', validators=[DataRequired(), Length(1, 64), Email()])    
    firstname = f.StringField('firstname', validators=[DataRequired()])
    lastname = f.StringField('lastname', validators=[DataRequired()])
    password = f.PasswordField('password', validators=[DataRequired(), Length(1,8)])
    dateofbirth = f.DateField('dateofbirth', format='%d/%m/%Y')
    display = ['email', 'firstname', 'lastname', 'password', 'dateofbirth']


