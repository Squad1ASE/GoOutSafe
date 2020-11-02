from monolith.database import db, User, Restaurant, Table
from monolith.classes.tests.conftest import test_app
from monolith.classes.tests.test_user import user_example_credentials as user_test_dict
from monolith.classes.tests.test_user import create_user_EP
import json
from sqlalchemy import exc


def check_tables(table_to_check, table):
    assert table_to_check.restaurant_id  == table.restaurant_id 
    assert table_to_check.capacity == table.capacity
    assert table_to_check.table_name == table.table_name


def test_insert_table(test_app):
    app, test_client = test_app

    # --- UNIT TESTS ---
    with app.app_context():
        # create a user and a restaurant to testing table insertions
        # create_user_EP(test_client, user_test_dict)
        user_test = db.session.query(User).filter(User.email == user_test_dict.get('email')).first()
        assert user_test is not None
        restaurant_dict = dict(
            owner_id = user_test.id,
            name = 'Trial Restaurant',
            lat = 22,
            lon = 22, 
            phone = '3346734121',
            cuisine_type = [Restaurant.CUISINE_TYPES(1)],
            capacity = 10,
            prec_measures = 'leggeX',
            avg_time_of_stay = 30
        )
        restaurant = Restaurant(**restaurant_dict)
        db.session.add(restaurant)
        db.session.commit()
        restaurant = db.session.query(Restaurant).first()
        assert restaurant is not None

        # incorrect mandatory fields with validators
        incorrect_tables = [
            dict(restaurant_id = None, capacity = 1, table_name = 'table'),
            dict(restaurant_id = 0, capacity = 1, table_name = 'table'),
            dict(restaurant_id = -1, capacity = 1, table_name = 'table'),
            dict(restaurant_id = restaurant.id, capacity = None, table_name = 'table'),
            dict(restaurant_id = restaurant.id, capacity = 0, table_name = 'table'),
            dict(restaurant_id = restaurant.id, capacity = -1, table_name = 'table'),
            dict(restaurant_id = restaurant.id, capacity = 1, table_name = None),
            dict(restaurant_id = restaurant.id, capacity = 1, table_name = '')
        ]
        for t in incorrect_tables:
            try:
                table = Table(**t)
                assert False
            except ValueError:
                assert True
            except Exception:
                assert False

        # missing fields
        incorrect_tables = [
            dict(capacity = 1, table_name = 'table'),
            dict(restaurant_id = restaurant.id, table_name = 'table'),
            dict(restaurant_id = restaurant.id, capacity = 1)
        ]
        for t in incorrect_tables:
            table = Table(**t)
            try:
                db.session.add(table)
                db.session.commit()
                assert False
            except (exc.IntegrityError, exc.InvalidRequestError):
                db.session.rollback()
                assert True
            except Exception:
                assert False

        # correct tables
        correct_tables = [
            dict(restaurant_id = restaurant.id, capacity = 1, table_name = 'c'),
            dict(restaurant_id = restaurant.id, capacity = 30, table_name = 'big table'),
        ]
        for t in correct_tables:
            table = Table(**t)
            db.session.add(table)
            db.session.commit()
            table_to_check = db.session.query(Table).filter(Table.id == table.id).first()
            assert table_to_check is not None
            check_tables(table_to_check, table)

        # check total tables
        tables = db.session.query(Table).all()
        assert len(tables) == len(correct_tables)