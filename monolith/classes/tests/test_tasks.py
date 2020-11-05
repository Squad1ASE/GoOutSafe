import unittest
from monolith.background import mail, compute_review_count
from monolith.background import send_email, get_mail_object, compute_like_count
from monolith.classes.tests.conftest import test_app
import datetime

from monolith.database import User, db, Restaurant, Like, Review


def test_send_email(test_app):
    app, test_client = test_app
    # --- UNIT TESTS ---
    with app.app_context():
        with get_mail_object().record_messages() as outbox:
            send_email('testing', 'test1', ["jackpeps@gmail.com"])
            assert len(outbox) == 1
            assert outbox[0].subject == "testing"


def test_compute_like_count(test_app):
    app, test_client = test_app
    with app.app_context():
        def add_user(email, phone, firstname, lastname, password, date):
            new_user = User()
            new_user.email = email
            new_user.phone = phone
            new_user.firstname = firstname
            new_user.lastname = lastname
            new_user.password = password
            new_user.dateofbirth = date

            db.session.add(new_user)
            db.session.commit()
            return db.session.query(User).filter(User.email == email).first()

        user_test = add_user("likecountuser@test.com", '3333333333', "firstname", "lastname", "passwo",
                             datetime.date(2020, 10, 5))
        user_test1 = add_user("likecountuser1@test.com", '3333333333', "firstname", "lastname", "passwo",
                              datetime.date(2020, 10, 5))
        user_test2 = add_user("likecountuser2@test.com", '3333333333', "firstname", "lastname", "passwo",
                              datetime.date(2020, 10, 5))

        restaurants = [
            dict(owner_id=user_test.id, name='ciccio', lat=22, lon=22, phone='3346734121',
                 cuisine_type=[Restaurant.CUISINE_TYPES(1)],
                 capacity=10, prec_measures='leggeX', avg_time_of_stay=30
                 ),
            dict(owner_id=user_test.id, name='pluto', lat=22, lon=22, phone='3346734121',
                 cuisine_type=[Restaurant.CUISINE_TYPES(1), Restaurant.CUISINE_TYPES(2)],
                 capacity=1, prec_measures='', avg_time_of_stay=15, tot_reviews=None, avg_rating=None, likes=None
                 )
        ]

        for r in restaurants:
            restaurant = Restaurant(**r)
            db.session.add(restaurant)
            db.session.commit()

        ciccio_restaurant = db.session.query(Restaurant).filter_by(name="ciccio").first()
        pluto_restaurant = db.session.query(Restaurant).filter_by(name="pluto").first()

        def putLike(user_id, restaurant_id):
            new_like = Like()
            new_like.liker_id = user_id
            new_like.restaurant_id = restaurant_id
            db.session.add(new_like)
            db.session.commit()

        assert (ciccio_restaurant.likes is not None)
        assert (pluto_restaurant.likes is not None)
        assert (ciccio_restaurant.likes == 0)
        assert (pluto_restaurant.likes == 0)

        putLike(user_test.id, ciccio_restaurant.id)
        compute_like_count()
        assert (ciccio_restaurant.likes == 1)
        assert (pluto_restaurant.likes == 0)

        putLike(user_test.id, pluto_restaurant.id)
        putLike(user_test1.id, pluto_restaurant.id)
        putLike(user_test2.id, pluto_restaurant.id)
        compute_like_count()

        assert (ciccio_restaurant.likes == 1)
        assert (pluto_restaurant.likes == 3)
        compute_like_count()

        putLike(user_test1.id, ciccio_restaurant.id)
        putLike(user_test2.id, ciccio_restaurant.id)
        compute_like_count()
        assert (ciccio_restaurant.likes == 3)
        assert (pluto_restaurant.likes == 3)


def test_compute_review_count(test_app):
    app, test_client = test_app
    with app.app_context():
        def add_user(email, phone, firstname, lastname, password, date):
            new_user = User()
            new_user.email = email
            new_user.phone = phone
            new_user.firstname = firstname
            new_user.lastname = lastname
            new_user.password = password
            new_user.dateofbirth = date

            db.session.add(new_user)
            db.session.commit()
            return db.session.query(User).filter(User.email == email).first()

        user_test = add_user("likecountuser@test.com", '3333333333', "firstname", "lastname", "passwo",
                             datetime.date(2020, 10, 5))
        user_test1 = add_user("likecountuser1@test.com", '3333333333', "firstname", "lastname", "passwo",
                              datetime.date(2020, 10, 5))
        user_test2 = add_user("likecountuser2@test.com", '3333333333', "firstname", "lastname", "passwo",
                              datetime.date(2020, 10, 5))

        restaurants = [
            dict(owner_id=user_test.id, name='ciccio', lat=22, lon=22, phone='3346734121',
                 cuisine_type=[Restaurant.CUISINE_TYPES(1)],
                 capacity=10, prec_measures='leggeX', avg_time_of_stay=30
                 ),
            dict(owner_id=user_test.id, name='pluto', lat=22, lon=22, phone='3346734121',
                 cuisine_type=[Restaurant.CUISINE_TYPES(1), Restaurant.CUISINE_TYPES(2)],
                 capacity=1, prec_measures='', avg_time_of_stay=15, tot_reviews=None, avg_rating=None, likes=None
                 )
        ]

        for r in restaurants:
            restaurant = Restaurant(**r)
            db.session.add(restaurant)
            db.session.commit()

        ciccio_restaurant = db.session.query(Restaurant).filter_by(name="ciccio").first()
        pluto_restaurant = db.session.query(Restaurant).filter_by(name="pluto").first()

        def putReview(user_id, restaurant_id, rating):
            new_review = Review()
            new_review.marked = False
            new_review.comment = 'Good quality restaurant'
            new_review.rating = rating
            new_review.date = datetime.date.today()
            new_review.restaurant_id = restaurant_id
            new_review.reviewer_id = user_id
            db.session.add(new_review)
            db.session.commit()

        assert (ciccio_restaurant.avg_rating is not None)
        assert (pluto_restaurant.avg_rating is not None)
        assert (ciccio_restaurant.avg_rating == 0)
        assert (pluto_restaurant.avg_rating == 0)

        putReview(user_test.id, ciccio_restaurant.id, 3)
        compute_review_count()
        assert (ciccio_restaurant.avg_rating == 3)
        assert (pluto_restaurant.avg_rating == 0)

        putReview(user_test.id, pluto_restaurant.id, 0)
        putReview(user_test1.id, pluto_restaurant.id, 4)
        putReview(user_test2.id, pluto_restaurant.id, 5)
        compute_review_count()

        assert (ciccio_restaurant.avg_rating == 3)
        assert (pluto_restaurant.avg_rating == 3)
        compute_review_count()

        putReview(user_test1.id, ciccio_restaurant.id,2)
        compute_review_count()
        assert (ciccio_restaurant.avg_rating == 2,5)
        assert (pluto_restaurant.avg_rating == 3)

