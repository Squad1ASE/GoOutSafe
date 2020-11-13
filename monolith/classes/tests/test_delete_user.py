# from monolith.database import Table, Dish, 

from monolith.database import (db, User, Quarantine, Notification,
                                Restaurant, WorkingDay,
                                Reservation, Seat, 
                                Like, Review )

from monolith.classes.tests.conftest import test_app
from monolith.utilities import (create_user_EP, user_login_EP, user_logout_EP,
                                create_restaurant_EP, restaurant_reservation_EP, 
                                insert_ha, mark_patient_as_positive)
import json
from sqlalchemy import exc
import datetime


correct_restaurant = { 
    'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
    'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
    'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
    'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro',
    'workingdays-0-day': WorkingDay.WEEK_DAYS(1), 'workingdays-0-work_shifts':"('12:00','15:00'),('19:00','23:00')"
}

correct_reservation = {
    'date':'27/10/2020',
    'time':'14:00',
    'guests':2
}



def test_delete_user(test_app):
    app, test_client = test_app

    # unregister without a previous log-in 
    assert test_client.delete('/delete_user', follow_redirects=True).status_code == 401

    # unregister the HA
    insert_ha(db, app)
    assert user_login_EP(test_client, 'healthauthority@ha.com', 'ha').status_code == 200
    assert test_client.delete('/delete_user', follow_redirects=True).status_code == 403
    assert user_logout_EP(test_client).status_code == 200

    # register a customer user
    assert create_user_EP(test_client, email='user_customer_example@test.com', password='passw', role='customer').status_code == 200
    with app.app_context(): # check customer presence in the db        
        assert db.session.query(User).filter(User.email == 'user_customer_example@test.com').first() != None
    # unregister a customer user
    assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 200
    assert test_client.delete('/delete_user', follow_redirects=True).status_code == 200
    with app.app_context(): # check customer absence in the db        
        assert db.session.query(User).filter(User.email == 'user_customer_example@test.com').first() == None
    assert user_logout_EP(test_client).status_code == 401
    assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 401

    # ----------------------------------------------------------------------------------------------------- DELETE FROM QUARANTINE
    # register again a customer
    assert create_user_EP(test_client, email='user_customer_example@test.com', password='passw', role='customer').status_code == 200
    assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 200
    assert user_logout_EP(test_client).status_code == 200
    # HA mark as positive the previous customer
    assert user_login_EP(test_client, 'healthauthority@ha.com', 'ha').status_code == 200
    assert test_client.get('/patient_informations', follow_redirects=True).status_code == 200
    assert test_client.post('/patient_informations', data=dict(email="user_customer_example@test.com"), follow_redirects=True).status_code == 200    
    assert mark_patient_as_positive(test_client, 'user_customer_example@test.com').status_code == 555
    with app.app_context(): # check quarantine presence in the db        
        user_test = db.session.query(User).filter(User.email == 'user_customer_example@test.com').first()
        assert db.session.query(Quarantine).filter(Quarantine.user_id == user_test.id).first() != None
    assert user_logout_EP(test_client).status_code == 200
    # unregister a positive customer, gives a failure    
    assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 200
    assert test_client.delete('/delete_user', follow_redirects=True).status_code == 403
    assert user_logout_EP(test_client).status_code == 200
    # mark as negative the previous customer
    with app.app_context(): # check quarantine presence in the db        
        user_test = db.session.query(User).filter(User.email == 'user_customer_example@test.com').first()
        quarantine_test = db.session.query(Quarantine).filter(Quarantine.user_id == user_test.id).first() 
        assert quarantine_test is not None
        quarantine_test.in_observation = False        
        db.session.commit()
    # unregister the negatve customer, also from Quarantine
    assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 200
    assert test_client.delete('/delete_user', follow_redirects=True).status_code == 200
    with app.app_context(): # check quarantine absence in the db, that is gained because there is the user absence too        
        assert db.session.query(User).filter(User.email == 'user_customer_example@test.com').first() == None
    assert user_logout_EP(test_client).status_code == 401
    assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 401

    # ----------------------------------------------------------------------------------------------------- DELETE FROM NOTIFICATION
    # register again a customer
    assert create_user_EP(test_client, email='user_customer_example@test.com', password='passw', role='customer').status_code == 200
    assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 200
    assert user_logout_EP(test_client).status_code == 200
    with app.app_context(): # check notification presence in the db
        user_test = db.session.query(User).filter(User.email == 'user_customer_example@test.com').first()
        notification_test = Notification()
        notification_test.user_id = user_test.id
        notification_test.email = user_test.email 
        notification_test.message = 'hello'
        notification_test.pending = True
        notification_test.type_ = Notification.TYPE(1)
        notification_test.date = datetime.date(2020, 10, 5)
        db.session.add(notification_test)
        db.session.commit()
    # unregister the customer, also from Notification
    assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 200
    assert test_client.delete('/delete_user', follow_redirects=True).status_code == 200
    with app.app_context(): # check notification absence in the db, that is gained because there is the user absence too        
        assert db.session.query(User).filter(User.email == 'user_customer_example@test.com').first() == None
    assert user_logout_EP(test_client).status_code == 401
    assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 401
    
    # ----------------------------------------------------------------------------------------------------- DELETE FROM RESERVATION
    # register a owner

    # FROM HERE --> build first relations with restaurant
    """    
    assert create_user_EP(test_client, email='user_owner_example@test.com', password='passw', role='owner').status_code == 200

    # register a restaurant
    assert user_login_EP(test_client, 'user_owner_example@test.com', 'passw').status_code == 200
    assert create_restaurant_EP(test_client, correct_restaurant).status_code == 200
    assert user_logout_EP(test_client).status_code == 200

    # register again a customer
    assert create_user_EP(test_client, email='user_customer_example@test.com', password='passw', role='customer').status_code == 200
    assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 200
    # register a reservation on the previous restaurant
    with app.app_context(): # check restaurant presence in the db
        user_test = db.session.query(User).filter(User.email == 'user_customer_example@test.com').first()
        owner_test = db.session.query(User).filter(User.email == 'user_owner_example@test.com').first()
        restaurant_test = db.session.query(Restaurant).filter(Restaurant.owner_id == owner_test.id).first()
        
        assert restaurant_reservation_EP(test_client, 
                                            restaurant_id=restaurant_test.id, 
                                            date=correct_reservation['date'], 
                                            time=correct_reservation['time'], 
                                            guests=correct_reservation['guests']).status_code == 200


    assert user_logout_EP(test_client).status_code == 200
    """

    """
    #------------------------------


    # unregister a owner user
    assert user_login_EP(test_client, email='user_owner_example@test.com', password='passw').status_code == 200
    assert test_client.delete('/delete_user', follow_redirects=True).status_code == 200
    user_test = db.session.query(User).filter(User.email == 'user_owner_example@test.com').first()
    assert user_test is None
    assert test_client.get('/logout', follow_redirects=True).status_code == 200
    #------------------------------
    """
