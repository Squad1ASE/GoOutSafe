from flask_wtf import FlaskForm
import wtforms as f
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    email = f.StringField('email', validators=[DataRequired()])
    password = f.PasswordField('password', validators=[DataRequired()])
    display = ['email', 'password']


class UserForm(FlaskForm):
    email = f.StringField('email', validators=[DataRequired()])
    firstname = f.StringField('firstname', validators=[DataRequired()])
    lastname = f.StringField('lastname', validators=[DataRequired()])
    password = f.PasswordField('password', validators=[DataRequired()])
    dateofbirth = f.DateField('dateofbirth', format='%d/%m/%Y')
    display = ['email', 'firstname', 'lastname', 'password', 'dateofbirth']

class RestaurantForm(FlaskForm):
    name = f.StringField('name', validators=[DataRequired()])
    lat = f.StringField('lat', validators=[DataRequired()])
    lon = f.StringField('lon', validators=[DataRequired()])
    phone = f.StringField('phone', validators=[DataRequired()])
    # maybe owner has to complete the tables descritions and capacity is 
    # automatically derived from tables settings
    capacity = f.StringField('capacity', validators=[DataRequired()])
    prec_measures = f.StringField('prec_measures', validators=[DataRequired()])
    display = ['name', 'lat', 'lon', 'phone', 'capacity','prec_measures']