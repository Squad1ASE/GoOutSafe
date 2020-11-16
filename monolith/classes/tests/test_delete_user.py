# from monolith.database import Table, Dish, 

from monolith.database import (db, User, Quarantine, Notification,
                                Restaurant, WorkingDay,
                                Reservation, Seat, 
                                Like, Review )

from monolith.classes.tests.conftest import test_app
from monolith.utilities import (create_user_EP, user_login_EP, user_logout_EP,
                                create_restaurant_EP, restaurant_reservation_EP, 
                                restaurant_reservation_POST_EP, create_review_EP,
                                insert_ha, mark_patient_as_positive)
from monolith.app import del_inactive_users
import json
from sqlalchemy import exc
import datetime

#import unittest
from monolith.app import del_inactive_users 
#from datetime import datetime, timedelta
#import datetime as dt



correct_restaurant = { 
    'name':'Trial01-EP' , 'lat':22, 'lon':22, 'phone':'3346734121', 
    'cuisine_type':[Restaurant.CUISINE_TYPES(1)], 'prec_measures':'leggeX', 'avg_time_of_stay':30,
    'tables-0-table_name':'yellow', 'tables-0-capacity':5, 
    'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro',
    'workingdays-0-day': WorkingDay.WEEK_DAYS(1), 'workingdays-0-work_shifts':"('12:00','15:00'),('19:00','23:00')"
}

correct_reservation = {
    'date':'28/12/2020', #in the future 
    'time':'14:00',
    'guests':2
}

correct_email = [
    'user_customer2_example@test.com',
    'user_customer3_example@test.com'
]

correct_review = dict(
    rating=4,
    comment='Good quality restaurant',
    date=datetime.date.today()
)


def test_delete_user(test_app):
    app, test_client = test_app

    # unregister without a previous log-in 
    assert test_client.delete('/delete_user', follow_redirects=True).status_code == 401

    # unregister HA
    insert_ha(db, app)
    assert user_login_EP(test_client, 'healthauthority@ha.com', 'ha').status_code == 200
    assert test_client.delete('/delete_user', follow_redirects=True).status_code == 403
    assert user_logout_EP(test_client).status_code == 200


    # unregister a user without reservations
    with app.app_context(): 
        # bad access from not active users
        assert create_user_EP(test_client, email='user_customer_example@test.com', password='passw', role='customer').status_code == 200

        user_test = db.session.query(User).filter(User.email == 'user_customer_example@test.com').first() 
        assert user_test != None
        user_test.is_active = False
        db.session.commit()
        assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 401  # fails the login

        user_test.is_active = True
        db.session.commit()
        assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 200 # OK the login

        user_test.is_active = False
        db.session.commit()
        assert test_client.delete('/delete_user', follow_redirects=True).status_code == 403  # fails the delete
        assert user_logout_EP(test_client).status_code == 200

        user_test.is_active = True
        db.session.commit()    


        # good access from active users, from here tests also the celery task part (inside with!!!)
        # unregister an active user
        assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 200
        assert test_client.delete('/delete_user', follow_redirects=True).status_code == 200
        del_inactive_users()

        # check customer absence in the db        
        assert db.session.query(User).filter(User.email == 'user_customer_example@test.com').first() == None
        assert user_logout_EP(test_client).status_code == 200
        assert user_logout_EP(test_client).status_code == 401
        assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 401


 
 
 
    # register a owner
    assert create_user_EP(test_client, email='user_owner_example@test.com', password='passw', role='owner').status_code == 200

    # register a restaurant
    assert user_login_EP(test_client, 'user_owner_example@test.com', 'passw').status_code == 200
    assert create_restaurant_EP(test_client, correct_restaurant).status_code == 200
    assert user_logout_EP(test_client).status_code == 200

    # register two guests
    assert create_user_EP(test_client, email='user_customer2_example@test.com', password='passw', role='customer').status_code == 200
    assert create_user_EP(test_client, email='user_customer3_example@test.com', password='passw', role='customer').status_code == 200




    # unregister a user with only future reservations 
    with app.app_context(): 


        assert create_user_EP(test_client, email='user_customer_example@test.com', password='passw', role='customer').status_code == 200
        assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 200    
    
        # register a reservation with 2 guests

        # check all them present in the db
        #user_test = db.session.query(User).filter(User.email == 'user_customer_example@test.com').first()
        #owner_test = db.session.query(User).filter(User.email == 'user_owner_example@test.com').first()
        #restaurant_test = db.session.query(Restaurant).filter(Restaurant.owner_id == owner_test.id).first()        

        # look for a table in a correct date and time
        assert restaurant_reservation_EP(test_client, 
                                            restaurant_id='1', #restaurant_test.id, 
                                            date=correct_reservation['date'], 
                                            time=correct_reservation['time'], 
                                            guests=correct_reservation['guests'] + 1).status_code == 200
        # placing a reservation
        reservation_date_str = correct_reservation['date'] + " " + correct_reservation['time']
        reservation_datetime = datetime.datetime.strptime(reservation_date_str, "%d/%m/%Y %H:%M")        
        guests_email_dict = dict()
        for i in range(correct_reservation['guests']):
            key = 'guest-'+str(i)+'-email'
            guests_email_dict[key] = correct_email[i]  
        assert restaurant_reservation_POST_EP(test_client,
                                            restaurant_id='1',
                                            table_id_reservation=1,#8,
                                            date = reservation_date_str,
                                            guests=correct_reservation['guests'] + 1,
                                            data=guests_email_dict).status_code == 666
        # checking via db if reservation has been added
        reservation_test = db.session.query(Reservation).filter(
            Reservation.restaurant_id == '1',
            Reservation.table_id == 1,#8, 
            Reservation.date == reservation_datetime
        ).first() 
        assert reservation_test != None
        """        
        #check also seat has been added
        seats = db.session.query(Seat).filter_by(reservation_id=restaurant_test.id).all()
        assert len(seats) == correct_reservation['guests'] + 1 
        assert seats[0].guests_email ==  'user_customer2_example@test.com' 
        assert seats[1].guests_email ==  'user_customer3_example@test.com' 
        assert seats[2].guests_email ==  'user_customer_example@test.com' 
        """
        
        # unregister the customer, also all its future reservations 
        assert test_client.delete('/delete_user', follow_redirects=True).status_code == 200    
        del_inactive_users()

        # check the changes in db
        
        """ 
        # TODO will be needed after the realization of notifcations in delete_reservation(reservation_id) ??
        # check notification present for the guests        
        info = db.session.query(Notification).filter_by(email='user_customer2_example@test.com').first()
        assert info.email == 'user_customer2_example@test.com'
        assert info.type_ == Notification.TYPE(2)
        info = db.session.query(Notification).filter_by(email='user_customer3_example@test.com').first()
        assert info.email == 'user_customer3_example@test.com'
        assert info.type_ == Notification.TYPE(2)
        # notification not present for customer itself
        info = db.session.query(Notification).filter_by(email='user_customer_example@test.com').first()
        assert info is None  
        # notification present for the owner
        info = db.session.query(Notification).filter_by(email='user_owner_example@test.com').first()
        assert info.email == 'user_owner_example@test.com'        
        assert info.message == str(reservation_test.id)
        assert info.type_ == Notification.TYPE(2)
        #assert db.session.query(Reservation).filter_by(restaurant_id=restaurant_test.id).first() == None
        rs = db.session.query(Reservation).filter(
            Reservation.booker_id==user_test.id, 
            Reservation.date>datetime.datetime.today(), 
            Reservation.cancelled==False).all() 
        for r in rs: 
            assert r == None
        """

        us = db.session.query(User).filter(User.email == 'user_customer_example@test.com').first()        
        assert us == None 
        
        assert user_logout_EP(test_client).status_code == 200
        assert user_logout_EP(test_client).status_code == 401
        assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 401


    # unregister a user with a computed reservation but are not passed 14 days from this last
    with app.app_context(): 
        assert create_user_EP(test_client, email='user_customer_example@test.com', password='passw', role='customer').status_code == 200
        assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 200    
        user_test = db.session.query(User).filter(User.email == 'user_customer_example@test.com').first()

        # look for a table in a correct date and time
        startdate = datetime.date.today()
        enddate = startdate + datetime.timedelta(days=-1) # placing for yesterday
        assert restaurant_reservation_EP(test_client, 
                                            restaurant_id='1', #restaurant_test.id, 
                                            date=enddate, 
                                            time=correct_reservation['time'], 
                                            guests=correct_reservation['guests'] + 1).status_code == 200
        # placing a reservation
        reservation_date_str = str(enddate.strftime("%d/%m/%Y")) + " " + correct_reservation['time']
        reservation_datetime = datetime.datetime.strptime(reservation_date_str, "%d/%m/%Y %H:%M")        
        guests_email_dict = dict()
        for i in range(correct_reservation['guests']):
            key = 'guest-'+str(i)+'-email'
            guests_email_dict[key] = correct_email[i]  
        assert restaurant_reservation_POST_EP(test_client,
                                            restaurant_id='1',
                                            table_id_reservation=2,#8,
                                            date = reservation_date_str,
                                            guests=correct_reservation['guests'] + 1,
                                            data=guests_email_dict).status_code == 666
        # checking via db if reservation has been added        
        reservation_test = db.session.query(Reservation).filter(
            Reservation.restaurant_id == '1',
            Reservation.table_id == 2,#8, 
            Reservation.date == reservation_datetime
        ).first() 
        assert reservation_test != None
        
        # unregister the customer, also all its future reservations 
        #assert user_test.id == 1
        assert test_client.delete('/delete_user', follow_redirects=True).status_code == 200    
        del_inactive_users()

        # check the changes in db not happened since are not passed the days
        us = db.session.query(User).filter(User.email == 'user_customer_example@test.com').first()        
        assert us != None 
        
        assert user_logout_EP(test_client).status_code == 200
        assert user_logout_EP(test_client).status_code == 401
        assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 401



    # unregister a user with a computed reservation but are passed exactly 14 days from this last
    # we don't care for them that happened more than 14 days ago
    with app.app_context(): 
        assert create_user_EP(test_client, email='user_customer4_example@test.com', password='passw', role='customer').status_code == 200
        assert user_login_EP(test_client, 'user_customer4_example@test.com', 'passw').status_code == 200    
        user_test = db.session.query(User).filter(User.email == 'user_customer4_example@test.com').first()

        # look for a table in a correct date and time
        startdate = datetime.date.today()
        enddate = startdate + datetime.timedelta(days=-14) # placing for 14 days ago
        assert restaurant_reservation_EP(test_client, 
                                            restaurant_id='1', #restaurant_test.id, 
                                            date=enddate, 
                                            time=correct_reservation['time'], 
                                            guests=correct_reservation['guests'] + 1).status_code == 200
        # placing a reservation
        reservation_date_str = str(enddate.strftime("%d/%m/%Y")) + " " + correct_reservation['time']
        reservation_datetime = datetime.datetime.strptime(reservation_date_str, "%d/%m/%Y %H:%M")        
        guests_email_dict = dict()
        for i in range(correct_reservation['guests']):
            key = 'guest-'+str(i)+'-email'
            guests_email_dict[key] = correct_email[i]  
        assert restaurant_reservation_POST_EP(test_client,
                                            restaurant_id='1',
                                            table_id_reservation=2,#8,
                                            date = reservation_date_str,
                                            guests=correct_reservation['guests'] + 1,
                                            data=guests_email_dict).status_code == 666
        # checking via db if reservation has been added        
        reservation_test = db.session.query(Reservation).filter(
            Reservation.restaurant_id == '1',
            Reservation.table_id == 2,#8, 
            Reservation.date == reservation_datetime
        ).first() 
        assert reservation_test != None
        
        # unregister the customer, also all its reservations 
        assert test_client.delete('/delete_user', follow_redirects=True).status_code == 200    
        del_inactive_users()

        # check the changes in db happened since now are passed excatly the days
        us = db.session.query(User).filter(User.email == 'user_customer4_example@test.com').first()        
        assert us == None         
        assert user_logout_EP(test_client).status_code == 200
        assert user_logout_EP(test_client).status_code == 401
        assert user_login_EP(test_client, 'user_customer4_example@test.com', 'passw').status_code == 401




# TODO check if the followings are uselful
# ---------------------------------------------------------------------------------------- unregister a positive user

"""

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
       

    #------------------------------------------------------------------------------------------------ DELETE FROM LIKE
    #the restaurant is the previous

    # register again a customer
    assert create_user_EP(test_client, email='user_customer_example@test.com', password='passw', role='customer').status_code == 200
    assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 200

    # register again a reservation on the previous restaurant
    with app.app_context(): # check all them present in the db
        user_test = db.session.query(User).filter(User.email == 'user_customer_example@test.com').first()
        owner_test = db.session.query(User).filter(User.email == 'user_owner_example@test.com').first()
        restaurant_test = db.session.query(Restaurant).filter(Restaurant.owner_id == owner_test.id).first()
        
        # look for a table in a correct date and time
        assert restaurant_reservation_EP(test_client, 
                                            restaurant_id='1', #restaurant_test.id, 
                                            date=correct_reservation['date'], 
                                            time=correct_reservation['time'], 
                                            guests=correct_reservation['guests']).status_code == 200
        # placing a reservation
        reservation_date_str = correct_reservation['date'] + " " + correct_reservation['time']
        reservation_datetime = datetime.datetime.strptime(reservation_date_str, "%d/%m/%Y %H:%M")
        guests_email_dict = dict()
        for i in range(correct_reservation['guests']):
            key = 'guest-'+str(i)+'-email'
            guests_email_dict[key] = correct_email[i]        
        assert restaurant_reservation_POST_EP(test_client,
                                            restaurant_id='1',
                                            table_id_reservation=8,
                                            date = reservation_date_str,
                                            guests=correct_reservation['guests'],
                                            data=guests_email_dict).status_code == 666
        # checking via db if reservation has been added
        assert db.session.query(Reservation).filter(
            Reservation.restaurant_id == '1',
            Reservation.table_id == 8, 
            Reservation.date == reservation_datetime
        ).first() != None

        #assign a like on a previous registration
        assert test_client.get('/restaurants/like/'+str(restaurant_test.id)).status_code == 200
        assert db.session.query(Like).filter(Like.liker_id == user_test.id and Like.restaurant_id==restaurant_test.id).first() != None

    # unregister the customer, also from reservation, seat, like
    assert test_client.delete('/delete_user', follow_redirects=True).status_code == 200    
    with app.app_context(): # check all them absent in the db, that is gained because there is the user absence too        
        assert db.session.query(User).filter(User.email == 'user_customer_example@test.com').first() == None
    assert user_logout_EP(test_client).status_code == 401
    assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 401

    #------------------------------------------------------------------------------------------- DELETE FROM REVIEW
    #the restaurant is the previous

    # register again a customer
    assert create_user_EP(test_client, email='user_customer_example@test.com', password='passw', role='customer').status_code == 200
    assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 200

    # register again a reservation on the previous restaurant
    with app.app_context(): # check all them present in the db
        user_test = db.session.query(User).filter(User.email == 'user_customer_example@test.com').first()
        owner_test = db.session.query(User).filter(User.email == 'user_owner_example@test.com').first()
        restaurant_test = db.session.query(Restaurant).filter(Restaurant.owner_id == owner_test.id).first()
        
        # look for a table in a correct date and time
        assert restaurant_reservation_EP(test_client, 
                                            restaurant_id='1', #restaurant_test.id, 
                                            date=correct_reservation['date'], 
                                            time=correct_reservation['time'], 
                                            guests=correct_reservation['guests']).status_code == 200
        # placing a reservation
        reservation_date_str = correct_reservation['date'] + " " + correct_reservation['time']
        reservation_datetime = datetime.datetime.strptime(reservation_date_str, "%d/%m/%Y %H:%M")
        guests_email_dict = dict()
        for i in range(correct_reservation['guests']):
            key = 'guest-'+str(i)+'-email'
            guests_email_dict[key] = correct_email[i]        
        assert restaurant_reservation_POST_EP(test_client,
                                            restaurant_id='1',
                                            table_id_reservation=8,
                                            date = reservation_date_str,
                                            guests=correct_reservation['guests'],
                                            data=guests_email_dict).status_code == 666
        # checking via db if reservation has been added
        assert db.session.query(Reservation).filter(
            Reservation.restaurant_id == str(restaurant_test.id),
            Reservation.table_id == 8, 
            Reservation.date == reservation_datetime
        ).first() != None

        #assign a review on a previous registration
        new_review = Review()
        new_review.marked = False
        new_review.comment = 'Good quality restaurant'
        new_review.rating = 3
        new_review.date = datetime.date.today()
        new_review.restaurant_id = restaurant_test.id
        new_review.reviewer_id = user_test.id
        db.session.add(new_review)
        db.session.commit()
        assert db.session.query(Review).filter(Review.reviewer_id == user_test.id,Review.restaurant_id == restaurant_test.id).first() != None

    # unregister the customer, also from reservation, seat, review
    assert test_client.delete('/delete_user', follow_redirects=True).status_code == 200    
    with app.app_context(): # check all them absent in the db, that is gained because there is the user absence too        
        assert db.session.query(User).filter(User.email == 'user_customer_example@test.com').first() == None
    assert user_logout_EP(test_client).status_code == 401
    assert user_login_EP(test_client, 'user_customer_example@test.com', 'passw').status_code == 401


    """
