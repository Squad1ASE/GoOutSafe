from monolith.database import db, User, Restaurant, Review
from monolith.classes.tests.conftest import test_app, create_user_EP, user_login_EP, create_restaurant_EP, create_review_EP,user_example, restaurant_example
import json
from sqlalchemy import exc
import datetime

def test_unit_reviews(test_app):
    app, test_client = test_app

    assert create_user_EP(test_client).status_code == 200
    assert user_login_EP(test_client).status_code == 200
    assert create_restaurant_EP(test_client).status_code == 200

    with app.app_context():

        # get a restaurant
        restaurant = db.session.query(Restaurant).filter_by(name = restaurant_example['name']).first()
        #get a user
        user = db.session.query(User).filter_by(email=user_example['email']).first()

        new_review = Review()
        new_review.marked = False
        new_review.comment = 'Good quality restaurant'
        new_review.rating = 3
        new_review.date = datetime.date.today()
        new_review.restaurant_id = restaurant.id
        new_review.reviewer_id = user.id
        db.session.add(new_review)
        db.session.commit()

        review = Review.query.filter_by(restaurant_id = int(restaurant.id)).first()

        assert review.marked == False
        assert review.comment == 'Good quality restaurant'
        assert review.rating == 3
        assert review.date == datetime.date.today()
        assert review.restaurant_id == restaurant.id
        assert review.reviewer_id == user.id

def test_component_reviews(test_app):
    app, test_client = test_app
    assert create_user_EP(test_client).status_code == 200
    assert user_login_EP(test_client).status_code == 200
    assert create_restaurant_EP(test_client).status_code == 200

    review = dict(
        rating=4,
        comment='Good quality restaurant',
        date=datetime.date.today()
    )

    with app.app_context():
        # get a restaurant
        restaurant = db.session.query(Restaurant).filter_by(name = restaurant_example['name']).first()
        #get a user, the owner
        user = db.session.query(User).filter_by(email=user_example['email']).first()

    # try to get as a owner (555)
    assert test_client.get('/restaurants/'+str(restaurant.id)).status_code == 555

    # try to review a place when i'm the owner (403)
    assert create_review_EP(test_client, restaurant.id, review).status_code == 403

    # try to get as customer without a reservation (555)
    assert test_client.get('/restaurants/'+str(restaurant.id)).status_code == 555

    # try to review a restaurant when i never been there (403)
    assert create_review_EP(test_client, restaurant.id, review).status_code == 403

    # logout with the owner (200)

    # login with other user (200)

    # create a reservation (200)

    # try to send an invalid form (400)

    # try to get as a customer who has a reservation (200)

    # try to double review the same restaurant (403)

    # logout
    assert test_client.get('/logout', follow_redirects=True).status_code == 200

    ha = dict(
        email='healthauthority@ha.com',
        phone='3333333333',
        firstname='Ha',
        lastname='Ha',
        password='ha',
        dateofbirth='05/10/2000'
    )

    # create health authority
    assert create_user_EP(test_client, **ha).status_code == 200

    # login as health authority
    assert user_login_EP(test_client, "healthauthority@ha.com", "ha").status_code == 200

    # try to get as health authority (555)
    assert test_client.get('/restaurants/'+str(restaurant.id)).status_code == 555

    # try to post as health authority (403)
    assert create_review_EP(test_client, restaurant.id, review).status_code == 403

        

