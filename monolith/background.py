import datetime

from celery import Celery
from flask_mail import Message, Mail

from monolith.database import db, Restaurant, Like, Review, Quarantine, User, Notification

BACKEND = BROKER = 'redis://localhost:6379'
celery = Celery(__name__, backend=BACKEND, broker=BROKER)

# _APP = None

mail = None

application = None

celery.conf.beat_schedule = {'unmark-negative-users': {
    'task': 'tasks.unmark_negative_users',
    'schedule': 30.0
}, 'compute-like-count': {
    'task': 'tasks.compute_like_count',
    'schedule': 30.0
}, 'compute-review-count': {
    'task': 'tasks.compute_review_count',
    'schedule': 30.0
}, 'compute-contact-tracing': {
    'task': 'tasks.send_notifications',
    'schedule': 30.0
}

}


@celery.task
def unmark_negative_users():
    inobservation = db.session.query(Quarantine).filter_by(in_observation=True).all()
    for quarantined in inobservation:
        if quarantined.end_date <= datetime.date.today():
            user = db.session.query(User).filter_by(id=quarantined.user_id).first()
            user.is_active = True  # todo necessario?
            quarantined.in_observation = False
            db.session.commit()


@celery.task
def compute_like_count():
    likes = db.session.query(Like).filter_by(marked=False)
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
        new_rev = db.session.query(Review).filter_by(marked=False, restaurant_id=new_review.restaurant_id, reviewer_id= new_review.reviewer_id).all()
        count_new_reviews = 0
        sum_new_reviews = 0
        for rev in new_rev:
            sum_new_reviews += rev.rating
            count_new_reviews += 1
            rev.marked = False
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
        user.is_active = False
        db.session.commit()
        send_email('notifica di quarantena', notification.message, [user.email])

    return count


def send_email(subject, body, recv):
    """Background task to send an email with Flask-Mail."""
    try:
        msg = Message(subject,
                      sender=application.config['MAIL_DEFAULT_SENDER'],
                      recipients=recv)
        msg.body = body
        with application.app_context():
            get_mail_object().send(msg)
    except Exception as ex:
        print('impossibile spedire mail a: ' + str(recv) + str(ex))


def get_mail_object():
    global mail
    if mail is None:
        mail = Mail(application)
    return mail


def set_app(app):
    global application
    application = app


@celery.task
def do_task():
    global _APP
    # lazy init
    if _APP is None:
        from monolith.app import create_app
        app = create_app()
        db.init_app(app)
    else:
        app = _APP

    return []

# set pythonpath
# celery -A background beat --loglevel=INFO
# celery -A background worker --loglevel=INFO
