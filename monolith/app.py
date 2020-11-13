import os
from flask import Flask
from monolith.database import db, User, Restaurant, Table, WorkingDay
from monolith.database import Reservation, Like, Seat, Review
from monolith.database import Dish, Quarantine
from monolith.database import Notification
from monolith.views import blueprints
from monolith.auth import login_manager
from monolith.utilities import insert_ha, create_user_EP, user_login_EP, user_logout_EP, create_restaurant_EP, customers_example
from monolith.utilities import restaurant_example, admin_example, health_authority_example, restaurant_owner_example 
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

    # TODO THIS SECTION MUST BE REMOVED, ONLY FOR DEMO
    # already tested EndPoints are used to create examples
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        
        q = db.session.query(User).filter(User.email == 'admin@admin.com')
        adm = q.first()
        if adm is None:
            # create a first admin user 
            # test for a user defined in database.db
            example = User()
            example.email = 'admin@admin.com'
            example.phone = '3333333333'
            example.firstname = 'Admin'
            example.lastname = 'Admin'
            example.set_password('admin')
            example.dateofbirth = datetime.date(2020, 10, 5)
            example.role = 'admin'           
            example.is_admin = True
            db.session.add(example)
            db.session.commit()

    

    test_client = app.test_client()

    insert_ha(db, app)
    
    for user in customers_example:
        create_user_EP(test_client,**user)

    for user in restaurant_owner_example:
        create_user_EP(test_client,**user)

    for usr_idx,restaurant in enumerate(restaurant_example):
        user_login_EP(test_client, restaurant_owner_example[usr_idx]['email'], 
                                    restaurant_owner_example[usr_idx]['password'])

        create_restaurant_EP(test_client,restaurant)

        user_logout_EP(test_client)

        

    app.config['WTF_CSRF_ENABLED'] = True

    

    return app

def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=os.environ['CELERY_BROKER_URL'],
        backend=os.environ['CELERY_BACKEND_URL']
        #backend='redis://localhost:6379',
        #broker='redis://localhost:6379'
    )
    celery.conf.update(app.config)
    celery.conf.beat_schedule = {'unmark-negative-users': {
        'task': 'monolith.app.unmark_negative_users',
        'schedule': 60.0
    }, 'compute-like-count': {
        'task': 'monolith.app.compute_like_count',
        'schedule': 30.0
    }, 'compute-review-count': {
        'task': 'monolith.app.compute_review_count',
        'schedule': 30.0
    }, 'compute-contact-tracing': {
        'task': 'monolith.app.send_notifications',
        'schedule': 60.0
    }, 'run-every-1-minute': {
        'task': 'monolith.app.print_hello',
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
    

@celery.task
def print_hello():
    print('Hello from Celery!')

@celery.task
def unmark_negative_users():
    inobservation = db.session.query(Quarantine).filter_by(in_observation=True).all()
    for quarantined in inobservation:
        if quarantined.end_date <= datetime.date.today():
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

