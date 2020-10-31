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

class RestaurantForm(FlaskForm):
    name = f.StringField('name', validators=[DataRequired()])
    lat = f.StringField('lat', validators=[DataRequired()])
    lon = f.StringField('lon', validators=[DataRequired()])
    phone = f.StringField('phone', validators=[DataRequired()])
    # maybe owner has to complete the tables descritions and capacity is 
    # automatically derived from tables settings
    # capacity = f.StringField('capacity', validators=[DataRequired()])
    cuisine_type = f.SelectMultipleField('cuisine_type',choices=[('1','cinese'),('2','italiana'),('3','messicana')],validators=[DataRequired()])
    prec_measures = f.TextAreaField('prec_measures',validators=[DataRequired()])
    display = ['name', 'lat', 'lon', 'phone', 'cuisine_type', 'prec_measures']

class GetPatientInformationsForm(FlaskForm):
    email = f.StringField('email', validators=[DataRequired(), Length(1, 64), Email()])
    display = ['email']

