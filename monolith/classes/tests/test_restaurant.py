from monolith.database import db, User, Restaurant, Table, Dish
from monolith.classes.tests.conftest import test_app
from monolith.classes.tests.test_user import user_example_credentials as user_test_dict
from monolith.classes.tests.test_user import create_user_EP, user_login_EP
import json
from sqlalchemy import exc


def create_restaurant_EP(test_client, data_dict):
    return test_client.post('/create_restaurant', data=data_dict, follow_redirects=True)


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


def test_create_restaurant(test_app):
    app, test_client = test_app

    user_test_id = None
    tot_correct_restaurants = 0
    tot_correct_tables = 0
    tot_correct_dishes = 0

    # --- UNIT TESTS ---
    with app.app_context():
        # create a user for testing the restaurant creation
        create_user_EP(test_client, user_test_dict)
        user_test = db.session.query(User).filter(User.email == user_test_dict.get('email')).first()
        assert user_test is not None
        user_test_id = user_test.id

        # correct restaurants pt1
        correct_restaurants = [
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'T', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1),Restaurant.CUISINE_TYPES(2)],
                capacity = 1, prec_measures = '',avg_time_of_stay = 15, tot_reviews = 0, avg_rating = 0, likes = 0
            )
        ]
        for r in correct_restaurants:
            restaurant = Restaurant(**r)
            db.session.add(restaurant)
            db.session.commit()

            restaurant_to_check = db.session.query(Restaurant).filter(Restaurant.id == restaurant.id).first()
            assert restaurant_to_check is not None
            check_restaurants(restaurant_to_check, restaurant)

        tot_correct_restaurants += len(correct_restaurants)


        # correct restaurants pt2 - missing optional fields
        correct_restaurants = [
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30
            ),
            dict(owner_id = user_test.id, name = 'T', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1),Restaurant.CUISINE_TYPES(2)],
                capacity = 1, prec_measures = '',avg_time_of_stay = 15, tot_reviews = None, avg_rating = None, likes = None
            )
        ]
        for r in correct_restaurants:
            restaurant = Restaurant(**r)
            db.session.add(restaurant)
            db.session.commit()

            restaurant_to_check = db.session.query(Restaurant).filter(Restaurant.id == restaurant.id).first()
            assert restaurant_to_check is not None
            assert restaurant_to_check.tot_reviews == 0
            assert restaurant_to_check.avg_rating == 0
            assert restaurant_to_check.likes == 0

        tot_correct_restaurants += len(correct_restaurants)


        # incorrect restaurants pt1 - fail check validators (owner_id and cuisine_type)
        incorrect_restaurants = [
            dict(owner_id = None, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = 0, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = -1, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = Restaurant.CUISINE_TYPES(1),
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [1,2],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = None,
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = 4
            )
        ]
        for r in incorrect_restaurants:
            try:
                restaurant = Restaurant(**r)
                assert False
            except ValueError:
                assert True
            except Exception:
                assert False
        

        # incorrect restaurants pt2 - incorrect fields or missing mandatory fields
        incorrect_restaurants = [
            dict(owner_id = user_test.id, name = None, lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = None, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = None, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = None, cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = None, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = None, avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = None, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = '', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 0, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = -1, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 14, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = -1, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 0, tot_reviews = 5, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = -1, avg_rating = 3.5, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = -1, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 5.1, likes = 4
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30, tot_reviews = 5, avg_rating = 3.5, likes = -1
            ),
            #missing mandatory fields:
            dict(name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30
            ),
            dict(owner_id = user_test.id, lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30
            ),
            dict(owner_id = user_test.id, name = 'Trial', lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121',
                capacity = 10, prec_measures = 'leggeX',avg_time_of_stay = 30
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                prec_measures = 'leggeX',avg_time_of_stay = 30
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, avg_time_of_stay = 30
            ),
            dict(owner_id = user_test.id, name = 'Trial', lat = 22, lon = 22, phone = '3346734121', cuisine_type = [Restaurant.CUISINE_TYPES(1)],
                capacity = 10, prec_measures = 'leggeX'
            )
        ]
        for r in incorrect_restaurants:
            restaurant = Restaurant(**r)
            try:
                db.session.add(restaurant)
                db.session.commit()
                assert False
            except (exc.IntegrityError, exc.InvalidRequestError):
                db.session.rollback()
                assert True
            except Exception as e:
                assert False

        #check total restaurants
        restaurants = db.session.query(Restaurant).all()
        assert len(restaurants) == tot_correct_restaurants
        
    
    # --- COMPONENTS TESTS ---

    # get and post should fail without login
    assert test_client.get('/create_restaurant', follow_redirects=True).status_code == 403
    assert create_restaurant_EP(test_client, dict()).status_code == 403 

    # authentication with correct credentials
    assert user_login_EP(test_client, user_test_dict.get('email'), user_test_dict.get('password')).status_code == 200

    # correct restaurant - pt1
    correct_restaurant = { 
        'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
        'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
        'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
        'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
    }
    tot_correct_restaurants += 1
    tot_correct_tables += 1
    tot_correct_dishes += 1
    assert create_restaurant_EP(test_client, correct_restaurant).status_code == 200
    with app.app_context():
        restaurant_to_check = db.session.query(Restaurant).filter(Restaurant.name == 'Trial01-EP').first()
        assert restaurant_to_check is not None
        assert restaurant_to_check.owner_id  == user_test_id 
        assert restaurant_to_check.name == 'Trial01-EP'
        assert restaurant_to_check.lat == 22
        assert restaurant_to_check.lon == 22
        assert restaurant_to_check.phone == '3346734121'
        assert restaurant_to_check.cuisine_type == [Restaurant.CUISINE_TYPES(1)]
        assert restaurant_to_check.capacity == 5
        assert restaurant_to_check.prec_measures == 'leggeX'
        assert restaurant_to_check.avg_time_of_stay == 30
        assert restaurant_to_check.tot_reviews == 0
        assert restaurant_to_check.avg_rating == 0
        assert restaurant_to_check.likes == 0

        tables = db.session.query(Table).filter(Table.restaurant_id == restaurant_to_check.id).all()
        assert len(tables) == 1
        table_to_check = db.session.query(Table).filter(Table.table_name == 'yellow').first()
        assert table_to_check is not None
        assert table_to_check.restaurant_id  == restaurant_to_check.id 
        assert table_to_check.table_name == 'yellow'
        assert table_to_check.capacity == 5

        dishes = db.session.query(Dish).filter(Dish.restaurant_id == restaurant_to_check.id).all()
        assert len(dishes) == 1
        dish_to_check = db.session.query(Dish).filter(Dish.dish_name == 'pizza').first()
        assert dish_to_check is not None
        assert dish_to_check.restaurant_id  == restaurant_to_check.id 
        assert dish_to_check.dish_name == 'pizza'
        assert dish_to_check.price == 4
        assert dish_to_check.ingredients == 'pomodoro'


    # correct restaurant - pt2
    correct_restaurant = { 
        'name':'Trial02-EP' , 'lat':22, 'lon':22, 'phone':'3', 
        'cuisine_type':[Restaurant.CUISINE_TYPES(1), Restaurant.CUISINE_TYPES(2)], 'prec_measures':'l', 'avg_time_of_stay':15,
        'tables-0-table_name':'yellow02', 'tables-0-capacity':5, 
        'tables-1-table_name':'green02', 'tables-1-capacity':1, 
        'tables-2-table_name':'blue02', 'tables-2-capacity':11, 
        'dishes-0-dish_name':'pizza02', 'dishes-0-price':4, 'dishes-0-ingredients':'p',
        'dishes-1-dish_name':'pasta02', 'dishes-1-price':0.1, 'dishes-1-ingredients':'pomodoro,pasta'
    }
    tot_correct_restaurants += 1
    tot_correct_tables += 3
    tot_correct_dishes += 2
    assert create_restaurant_EP(test_client, correct_restaurant).status_code == 200
    with app.app_context():
        restaurant_to_check = db.session.query(Restaurant).filter(Restaurant.name == 'Trial02-EP').first()
        assert restaurant_to_check is not None
        assert restaurant_to_check.owner_id  == user_test_id 
        assert restaurant_to_check.name == 'Trial02-EP'
        assert restaurant_to_check.lat == 22
        assert restaurant_to_check.lon == 22
        assert restaurant_to_check.phone == '3'
        assert restaurant_to_check.cuisine_type == [Restaurant.CUISINE_TYPES(1), Restaurant.CUISINE_TYPES(2)]
        assert restaurant_to_check.capacity == 17
        assert restaurant_to_check.prec_measures == 'l'
        assert restaurant_to_check.avg_time_of_stay == 15
        assert restaurant_to_check.tot_reviews == 0
        assert restaurant_to_check.avg_rating == 0
        assert restaurant_to_check.likes == 0

        tables = db.session.query(Table).filter(Table.restaurant_id == restaurant_to_check.id).all()
        assert len(tables) == 3
        table_to_check = db.session.query(Table).filter(Table.table_name == 'yellow02').first()
        assert table_to_check is not None
        assert table_to_check.restaurant_id  == restaurant_to_check.id 
        assert table_to_check.table_name == 'yellow02'
        assert table_to_check.capacity == 5
        table_to_check = db.session.query(Table).filter(Table.table_name == 'green02').first()
        assert table_to_check is not None
        assert table_to_check.restaurant_id  == restaurant_to_check.id 
        assert table_to_check.table_name == 'green02'
        assert table_to_check.capacity == 1
        table_to_check = db.session.query(Table).filter(Table.table_name == 'blue02').first()
        assert table_to_check is not None
        assert table_to_check.restaurant_id  == restaurant_to_check.id 
        assert table_to_check.table_name == 'blue02'
        assert table_to_check.capacity == 11

        dishes = db.session.query(Dish).filter(Dish.restaurant_id == restaurant_to_check.id).all()
        assert len(dishes) == 2
        dish_to_check = db.session.query(Dish).filter(Dish.dish_name == 'pizza02').first()
        assert dish_to_check is not None
        assert dish_to_check.restaurant_id  == restaurant_to_check.id 
        assert dish_to_check.dish_name == 'pizza02'
        assert dish_to_check.price == 4
        assert dish_to_check.ingredients == 'p'
        dish_to_check = db.session.query(Dish).filter(Dish.dish_name == 'pasta02').first()
        assert dish_to_check is not None
        assert dish_to_check.restaurant_id  == restaurant_to_check.id 
        assert dish_to_check.dish_name == 'pasta02'
        assert dish_to_check.price == 0.1
        assert dish_to_check.ingredients == 'pomodoro,pasta'

    # incorrect restaurants
    incorrect_restaurants = [
        # fields that must not be present are
        { 
            'owner_id':1, 'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'capacity':1, 'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'tot_reviews':1, 'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'avg_rating':1, 'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'likes':1, 'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        # incorrect restaurant fields
        # name
        { 
            'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':None , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        # lat
        { 
            'name':'Trial01-EP', 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP', 'lat':None, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        # lon
        { 
            'name':'Trial01-EP' , 'lat':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':None, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        # phone
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22,
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':None, 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        # cuisine_type
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':None, 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        # avg_time_of_stay
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX',
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':None,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':14,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':0,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':-1,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        # prec_measures
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':None, 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        # incorrect tables fields
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow',
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':None, 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':None, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':0, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':-1, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        # incorrect dishes fields
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5,
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':0, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':-1, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':''
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':None, 'dishes-0-ingredients':'pomodoro'
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':None
        },
        { 
            'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
            'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
            'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
            'dishes-0-dish_name':None, 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro'
        }
    ]
    for r in incorrect_restaurants:
        assert create_restaurant_EP(test_client, r).status_code == 400


    #check total restaurants/tables/dishes
    with app.app_context():
        
        restaurants = db.session.query(Restaurant).all()
        assert len(restaurants) == tot_correct_restaurants

        tables = db.session.query(Table).all()
        assert len(tables) == tot_correct_tables

        dishes = db.session.query(Dish).all()
        assert len(dishes) == tot_correct_dishes