from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship, validates  # is Object map scheme
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.schema import CheckConstraint

db = SQLAlchemy()


# the following consist of tables inside the db tables are defined using model
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    email = db.Column(db.String, nullable=False, unique=True)  
    @validates('email')
    def validate_email(self, key, user):
        assert '@' and '.' in user  #min email possible: a@b.c
        return user

    firstname = db.Column(db.Unicode(128))
    lastname = db.Column(db.Unicode(128))
    password = db.Column(db.Unicode(128), nullable=False) 
    dateofbirth = db.Column(db.DateTime)

    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    is_anonymous = False
    role = db.Column(db.Unicode(128)) # 0=customer, 1=rest_owner, 2=Asl


    def __init__(self, *args, **kw):
        super(User, self).__init__(*args, **kw)
        self._authenticated = False

    def set_password(self, password):
        self.password = generate_password_hash(password)

    @property
    def is_authenticated(self):
        return self._authenticated

    def authenticate(self, password):
        checked = check_password_hash(self.password, password)
        self._authenticated = checked  # it is true if the user password is correct
        return self._authenticated

    def get_id(self):
        return self.id




class Restaurant(db.Model):
    __tablename__ = 'restaurant'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    owner = relationship('User', foreign_keys='Restaurant.owner_id')

    name = db.Column(db.Text(100))
    likes = db.Column(db.Integer)  # will store the number of likes, periodically updated in background
    lat = db.Column(db.Float)  # restaurant latitude
    lon = db.Column(db.Float)  # restaurant longitude
    phone = db.Column(db.Integer)

    capacity = db.Column(db.Integer)

    cuisine_type = db.Column(db.PickleType)

    prec_measures = db.Column(db.Text(200))
    tot_reviews = db.Column(db.Integer)
    avg_rating = db.Column(db.Float)



class Table(db.Model):
    __tablename__ = 'table'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'))
    restaurant = relationship('Restaurant', foreign_keys='Table.restaurant_id') 

    name = db.Column(db.Text(100))    
    capacity = db.Column(db.Integer)  # avoid neg numbers


class WorkingDay(db.Model):
    __tablename__ = 'working_day'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'))
    restaurant = relationship('Restaurant', foreign_keys='WorkingDay.restaurant_id')  

    work_shifts = db.Column(db.PickleType)  

    day = db.Column(db.Integer, db.CheckConstraint('day>=0' and 'day<=6'), nullable=False)  # 0=Mon, 1=Tue, ...
    # the constraint is on the value of the column


# is like a pretty rating implementation
class Like(db.Model):
    __tablename__ = 'like'

    liker_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    liker = relationship('User', foreign_keys='Like.liker_id')

    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), primary_key=True)
    restaurant = relationship('Restaurant', foreign_keys='Like.restaurant_id')

    marked = db.Column(db.Boolean, default=False)  # True iff it has been counted in Restaurant.likes


class Reservation(db.Model):
    __tablename__ = 'reservation'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    booker_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    booker = relationship('User', foreign_keys='Reservation.booker_id')

    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'))
    restaurant = relationship('Restaurant', foreign_keys='Reservation.restaurant_id')

    table_id = db.Column(db.Integer, db.ForeignKey('table.id'))
    table = relationship('Table', foreign_keys='Reservation.table_id')

    date = db.Column(db.DateTime)
    hour = db.Column(db.PickleType)
    cancelled = db.Column(db.Boolean, default=True)


class Seat(db.Model):
    __tablename__ = 'seat'

    reservation_id = db.Column(db.Integer, db.ForeignKey('reservation.id'), primary_key=True)
    reservation = relationship('Reservation', foreign_keys='Seat.reservation_id')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user= relationship('User', foreign_keys='Seat.user_id')

    confirmed = db.Column(db.Boolean, default=True)


class Review(db.Model):
    __tablename__ = 'review'

    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    reviewer = relationship('User', foreign_keys='Review.reviewer_id')

    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), primary_key=True)
    restaurant = relationship('Restaurant', foreign_keys='Review.restaurant_id')

    marked = db.Column(db.Boolean, default=True)
    rating = db.Column(db.Integer)
    comment = db.Column(db.Text(200))
    date = db.Column(db.DateTime)

class Photo(db.Model):
    __tablename__ = 'photo'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'))
    restaurant = relationship('Restaurant', foreign_keys='Photo.restaurant_id')

    path = db.Column(db.Unicode(128))
    description = db.Column(db.Unicode(128))


class Dishes(db.Model):
    __tablename__ = 'dishes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'))
    restaurant = relationship('Restaurant', foreign_keys='Dishes.restaurant_id')

    price = db.Column(db.Float)
    name = db.Column(db.Unicode(128))
    ingredients = db.Column(db.PickleType)


class ReportOfPositivity(db.Model):
    __tablename__  = 'report_of_positivity'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user = relationship('User', foreign_keys='ReportOfPositivity.user_id')

    date = db.Column(db.DateTime)


class Quarantine(db.Model):
    __tablename__ = 'quarantine'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user = relationship('User', foreign_keys='Quarantine.user_id')

    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)

    active = db.Column(db.Boolean, default=True)


class Notification(db.Model):
    __tablename__ = 'notification'

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user = relationship('User', foreign_keys='Notification.user_id')

    message = db.Column(db.Unicode(128))
    pending = db.Column(db.Boolean, default=True)
    type_ = db.Column(db.Integer)  # 0=through email, 1=phone, 2=app
    date = db.Column(db.DateTime)

#comment
