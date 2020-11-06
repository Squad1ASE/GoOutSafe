import os
from flask import Flask

from monolith.database import db, User, Restaurant, Table, WorkingDay
from monolith.database import Reservation, Like, Seat, Review, Photo
from monolith.database import Dish, Quarantine
from monolith.database import Notification
from monolith.views import blueprints
from monolith.auth import login_manager
import datetime
import time


from celery import Celery
from flask_mail import Message, Mail

mail = None


def create_app():
    app = Flask(__name__)
    app.config['WTF_CSRF_SECRET_KEY'] = 'A SECRET KEY'
    app.config['SECRET_KEY'] = 'ANOTHER ONE'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gooutsafe.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Flask-Mail configuration
    app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'gooutsafe1@gmail.com'
    app.config['MAIL_PASSWORD'] = 'Admin123.'
    app.config['MAIL_DEFAULT_SENDER'] = 'gooutsafe@gmail.com'

    for bp in blueprints:
        app.register_blueprint(bp)
        bp.app = app

    db.init_app(app)
    login_manager.init_app(app)
    db.create_all(app=app)

    with app.app_context():

        q = db.session.query(User).filter(User.email == 'admin@admin.com')
        user = q.first()
        if user is None:
            # create a first admin user
            # test for a user defined in database.db
            example = User()
            example.email = 'admin@admin.com'
            example.phone = '3333333333'
            example.firstname = 'Admin'
            example.lastname = 'Admin'
            example.set_password('admin')
            example.dateofbirth = datetime.date(2020, 10, 5)
            example.is_admin = True
            db.session.add(example)
            db.session.commit()

        q = db.session.query(User).filter(User.email == 'healthauthority@ha.com')
        user = q.first()
        if user is None:
            # test for a user defined in database.db
            example = User()
            example.email = 'healthauthority@ha.com'
            example.phone = '3333333333'
            example.firstname = 'Ha'
            example.lastname = 'Ha'
            example.set_password('ha')
            example.dateofbirth = datetime.date(2020, 10, 5)
            example.is_admin = False
            db.session.add(example)
            db.session.commit()

        q = db.session.query(User).filter(User.email == 'test@test.com')
        user = q.first()
        if user is None:
            # test for a user defined in database.db
            example = User()
            example.email = 'test@test.com'
            example.phone = '3333333333'
            example.firstname = 'Testfirstname'
            example.lastname = 'Testlastname'
            example.set_password('test')
            example.dateofbirth = datetime.date(2020, 10, 5)
            example.is_admin = False
            db.session.add(example)
            db.session.commit()

        q = db.session.query(User).filter(User.email == 'admin@admin.com')
        user = q.first()
        q = db.session.query(Restaurant).filter(Restaurant.id == 1)
        restaurant = q.first()
        if restaurant is None:
            example = Restaurant()

            example.owner_id = user.id

            example.name = 'Trial Restaurant'
            example.likes = 42
            example.phone = 555123456
            example.lat = 43.720586
            example.lon = 10.408347

            example.capacity = 30
            example.cuisine_type = [Restaurant.CUISINE_TYPES(1), Restaurant.CUISINE_TYPES(2)]
            example.prec_measures = 'leggeX'
            example.tot_reviews = 2
            example.avg_rating = 2.0
            example.avg_time_of_stay = 15

            db.session.add(example)
            db.session.commit()


    return app


def make_celery(app):
    celery = Celery(
        app.import_name,
        backend='redis://localhost:6379',
        broker='redis://localhost:6379'
    )
    celery.conf.update(app.config)
    celery.conf.beat_schedule = {'unmark-negative-users': {
        'task': 'app.unmark_negative_users',
        'schedule': 60.0
    }, 'compute-like-count': {
        'task': 'app.compute_like_count',
        'schedule': 30.0
    }, 'compute-review-count': {
        'task': 'app.compute_review_count',
        'schedule': 30.0
    }, 'compute-contact-tracing': {
        'task': 'app.send_notifications',
        'schedule': 60.0
    }, 'run-every-1-minute': {
        'task': 'app.print_hello',
        'schedule': 3.0
    }

    }

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


app = create_app()
celery = make_celery(app)

mail = None



@celery.task
def print_hello():
    print('Hello from Celery!')

@celery.task
def unmark_negative_users():
    inobservation = db.session.query(Quarantine).filter_by(in_observation=True).all()
    for quarantined in inobservation:
        if quarantined.end_date <= datetime.datetime.now():
            user = db.session.query(User).filter_by(id=quarantined.user_id).first()
            user.is_active = True  # todo necessario?
            quarantined.in_observation = False
            db.session.commit()


@celery.task
def compute_like_count():
    likes = db.session.query(Like).filter(Like.marked == False).all()
    for like in likes:
        restaurant = db.session.query(Restaurant).filter_by(id=like.restaurant_id).first()
        restaurant.likes += 1
        like.marked = True
        db.session.commit()




@celery.task
def compute_review_count():
    # new avg reviews= (new reviews+avg old*tot old)/(tot old + tot new)
    all_new_reviews = db.session.query(Review).filter_by(marked=False).all()
    for new_review in all_new_reviews:
        new_rev = db.session.query(Review).filter_by(marked=False, restaurant_id=new_review.restaurant_id,
                                                     reviewer_id=new_review.reviewer_id).all()
        count_new_reviews = 0
        sum_new_reviews = 0
        for rev in new_rev:
            sum_new_reviews += rev.rating
            count_new_reviews += 1
            rev.marked = True
            db.session.commit()

        if count_new_reviews == 0:
            continue

        restaurant = db.session.query(Restaurant).filter_by(id=new_review.restaurant_id).first()
        restaurant.avg_rating = (sum_new_reviews + (restaurant.avg_rating * restaurant.tot_reviews)) / (
                restaurant.tot_reviews + count_new_reviews)
        restaurant.tot_reviews += count_new_reviews
        db.session.commit()


@celery.task
def send_notifications():
    notifications = db.session.query(Notification).filter_by(pending=True).all()
    for notification in notifications:
        notification.pending = False
        db.session.commit()

    count = 0
    for notification in notifications:
        count += 1
        user = db.session.query(User).filter_by(id=notification.user_id).first()
        db.session.commit()
        send_email('notifica di quarantena', notification.message, [user.email])

    return count


def send_email(subject, body, recv):
    """Background task to send an email with Flask-Mail."""
    try:
        msg = Message(subject,
                      sender=app.config['MAIL_DEFAULT_SENDER'],
                      recipients=recv)
        msg.body = body
        with app.app_context():
            get_mail_object().send(msg)
    except Exception as ex:
        print('impossibile spedire mail a: ' + str(recv) + str(ex))




def get_mail_object():
    global mail
    if mail is None:
        mail = Mail(app)
    return mail

