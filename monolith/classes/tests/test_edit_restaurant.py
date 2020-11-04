from monolith.database import db, User, Restaurant, Table, Dish, WorkingDay
from monolith.classes.tests.conftest import test_app, create_user_EP, user_login_EP, create_restaurant_EP
import json
from sqlalchemy import exc


# same of the test_restuarant.py
def check_restaurants(restaurant_to_check, restaurant):
    assert restaurant_to_check.owner_id  == restaurant.owner_id 
    assert restaurant_to_check.name == restaurant.name
    assert restaurant_to_check.lat == restaurant.lat
    assert restaurant_to_check.lon == restaurant.lon
    assert restaurant_to_check.phone == restaurant.phone
    assert restaurant_to_check.cuisine_type == restaurant.cuisine_type
    assert restaurant_to_check.capacity == restaurant.capacity
    assert restaurant_to_check.prec_measures == restaurant.prec_measures
    assert restaurant_to_check.avg_time_of_stay == restaurant.avg_time_of_stay
    assert restaurant_to_check.tot_reviews == restaurant.tot_reviews
    assert restaurant_to_check.avg_rating == restaurant.avg_rating
    assert restaurant_to_check.likes == restaurant.likes


def test_unit_edit_restaurant(test_app):
    app, test_client = test_app

    # --- UNIT TESTS ---
    with app.app_context():

        #---------------------------------------------------------- building the starting conditions
        # create a user
        assert create_user_EP(test_client, email='userexamplerestaurant@test.com', password='passw').status_code == 200
        user_test = db.session.query(User).filter(User.email == 'userexamplerestaurant@test.com').first()
        assert user_test is not None
        user_test_id = user_test.id

        #create a restaurant
        body_restaurant = dict(
            owner_id = user_test.id, 
            name = 'Trial', 
            lat = 22, 
            lon = 22, 
            phone = '3346734121', 
            cuisine_type = [Restaurant.CUISINE_TYPES(1)],
            capacity = 10, 
            prec_measures = 'leggeX',
            avg_time_of_stay = 30, 
            tot_reviews = 5, 
            avg_rating = 5, 
            likes = 4
        )
        restaurant = Restaurant(**body_restaurant)
        db.session.add(restaurant)
        db.session.commit()

        #test if the restaurant was created
        restaurant_to_check = db.session.query(Restaurant).filter(Restaurant.id == restaurant.id).first()
        assert restaurant_to_check is not None
        check_restaurants(restaurant_to_check, restaurant)
        #----------------------------------------------------------


def test_component_edit_restaurant(test_app):
    app, test_client = test_app
    assert create_user_EP(test_client, email='userexamplerestaurant@test.com', password='passw').status_code == 200
    with app.app_context():
        user_test = db.session.query(User).filter(User.email == 'userexamplerestaurant@test.com').first()
    assert user_test is not None
    user_test_id = user_test.id
    # --- COMPONENTS TESTS ---
    #---------------------------------------------------------- building the starting conditions
    # log the user
    assert user_login_EP(test_client, email='userexamplerestaurant@test.com', password='passw').status_code == 200

    # create a restaurant by the logged user 
    correct_restaurant = { 
        'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
        'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
        'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
        'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro',
        'workingdays-0-day': WorkingDay.WEEK_DAYS(1), 'workingdays-0-work_shifts':"('12:00','15:00'),('19:00','23:00')"
    }
    assert create_restaurant_EP(test_client, correct_restaurant).status_code == 200