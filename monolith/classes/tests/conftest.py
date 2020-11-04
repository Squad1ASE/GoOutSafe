import pytest
from monolith.database import db, Restaurant, WorkingDay
from monolith.app import create_app
import tempfile
import os
import datetime


# --- UTILITIES USER ---
user_example = dict(
    email='userexample@test.com',
    phone='3333333333',
    firstname='firstname_test',
    lastname='lastname_test',
    password='passw',
    dateofbirth='05/10/2000'
)

def create_user_EP(
        test_client, email=user_example['email'], phone=user_example['phone'],firstname=user_example['firstname'], 
        lastname=user_example['lastname'], password=user_example['password'], dateofbirth=user_example['dateofbirth']
    ):
    data = dict(
        email=email,
        phone=phone,
        firstname=firstname,
        lastname=lastname,
        password=password,
        dateofbirth=dateofbirth
    )
    return test_client.post('/create_user', data=data, follow_redirects=True)


def user_login_EP(test_client, email=user_example['email'], password=user_example['password']):
    data = dict(
        email=email,
        password=password
    )
    return test_client.post('/login', data=data, follow_redirects=True)

def edit_user_EP(
    test_client, phone, old_passw, new_passw
):
    data = dict(
        phone=phone,
        old_password=old_passw,
        new_password=new_passw
    )
    return test_client.post('/edit_user_informations', data=data, follow_redirects=True)

# --- UTILITIES RESTAURANT  ---
restaurant_example = { 
    'name':'RestaurantExample', 'lat':22, 'lon':22, 'phone':'3346734121', 
    'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
    'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
    'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro',
    'workingdays-0-day': WorkingDay.WEEK_DAYS(1), 'workingdays-0-work_shifts':"('12:00','15:00'),('19:00','23:00')"
}

# recall: to call this function you must be logged in
def create_restaurant_EP(test_client, data_dict=restaurant_example):
    return test_client.post('/create_restaurant', data=data_dict, follow_redirects=True)


@pytest.fixture
def test_app():
    app = create_app()

    app.config['WTF_CSRF_ENABLED'] = False  #this has been disabled to allows testing of forms
    temp_db, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+app.config['DATABASE']
    
    db.create_all(app=app)
    db.init_app(app=app)

    yield app, app.test_client()

    os.close(temp_db)