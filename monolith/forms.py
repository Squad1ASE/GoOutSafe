from flask_wtf import FlaskForm
import wtforms as f
from wtforms import Form
from wtforms.validators import DataRequired, Length, Email, NumberRange
from monolith.database import Restaurant


class LoginForm(FlaskForm):
    email = f.StringField('email', validators=[DataRequired(), Length(1, 64), Email()])    
    password = f.PasswordField('password', validators=[DataRequired(), Length(1,8)])
    display = ['email', 'password']


class UserForm(FlaskForm):
    email = f.StringField('email', validators=[DataRequired(), Length(1, 64), Email()])    
    phone = f.StringField('phone', validators=[DataRequired()])
    firstname = f.StringField('firstname', validators=[DataRequired()])
    lastname = f.StringField('lastname', validators=[DataRequired()])
    password = f.PasswordField('password', validators=[DataRequired(), Length(1,8)])
    dateofbirth = f.DateField('dateofbirth', format='%d/%m/%Y')
    display = ['email', 'firstname', 'lastname', 'password', 'dateofbirth']

class EditUserForm(FlaskForm):
    phone = f.StringField('phone', validators=[DataRequired()])
    old_password = f.PasswordField('old_password', validators=[DataRequired(), Length(1,8)])
    new_password = f.PasswordField('new_password', validators=[DataRequired(), Length(1,8)])
    display = ['phone', 'old_password', 'new_password']
    
class DishForm(Form):
    """Subform.

    CSRF is disabled for this subform (using `Form` as parent class) because
    it is never used by itself.
    """
    dish_name = f.StringField('Name', validators=[DataRequired()])
    price = f.FloatField('Price', validators=[DataRequired()])
    ingredients = f.StringField('Ingredients', validators=[DataRequired()])


class TableForm(Form):
    """Subform.

    CSRF is disabled for this subform (using `Form` as parent class) because
    it is never used by itself.
    """
    table_name = f.StringField('Name', validators=[DataRequired()])
    capacity = f.IntegerField('Capacity', validators=[DataRequired(), NumberRange(min=1)])


class RestaurantForm(FlaskForm):
    name = f.StringField('Name', validators=[DataRequired()])
    lat = f.FloatField('Latitude', validators=[DataRequired()])
    lon = f.FloatField('Longitude', validators=[DataRequired()])
    phone = f.StringField('Phone', validators=[DataRequired()])

    # Note: the capacity is automatically derived from tables settings

    cuisine_type = f.SelectMultipleField(
        'Cuisine types', 
        choices = Restaurant.CUISINE_TYPES.choices(),
        coerce = Restaurant.CUISINE_TYPES.coerce, 
        validators=[DataRequired()]
    )
    prec_measures = f.TextAreaField('Precautionary measures',validators=[DataRequired()])
    avg_time_of_stay = f.IntegerField('Average time of stay (in minutes)', validators=[DataRequired(), NumberRange(min=15)])

    tables = f.FieldList(f.FormField(TableForm), min_entries=1, max_entries=100)
    dishes = f.FieldList(f.FormField(DishForm), min_entries=1, max_entries=100)

    display = ['name', 'lat', 'lon', 'phone', 'cuisine_type', 'prec_measures', 'avg_time_of_stay']



class GetPatientInformationsForm(FlaskForm):
    email = f.StringField('email', validators=[DataRequired(), Length(1, 64), Email()])
    display = ['email']

class RestaurantSearch(FlaskForm):
    name = f.StringField('Name')
    lat = f.StringField('Latitude')
    lon = f.StringField('Longitude')

    cuisine_type = f.SelectMultipleField(
        'Cuisine types', 
        choices = Restaurant.CUISINE_TYPES.choices(),
        coerce = Restaurant.CUISINE_TYPES.coerce
    )

    display = ['name', 'lat', 'lon', 'cuisine_type']