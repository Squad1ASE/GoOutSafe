import os
from flask import Flask
from monolith.database import db, User, Restaurant, Table, WorkingDay
from monolith.database import Reservation, Like, Seat, Review, Photo
from monolith.database import Dishes, ReportOfPositivity, Quarantine
from monolith.database import Notification
from monolith.views import blueprints
from monolith.auth import login_manager
import datetime
import time

def create_app():
    app = Flask(__name__)
    app.config['WTF_CSRF_SECRET_KEY'] = 'A SECRET KEY'
    app.config['SECRET_KEY'] = 'ANOTHER ONE'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gooutsafe.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    for bp in blueprints:
        app.register_blueprint(bp)
        bp.app = app

    db.init_app(app)
    login_manager.init_app(app)
    db.create_all(app=app)

    # create a first admin user
    with app.app_context():

        q = db.session.query(User).filter(User.email == 'example@example.com')
        user = q.first()
        if user is None:

            # test for a user defined in database.db
            example = User()
            example.email = 'example@example.com'
            example.firstname = 'Admin'
            example.lastname = 'Admin'
            example.set_password('admin')
            example.dateofbirth = datetime.datetime(2020, 10, 5)            
            example.is_admin = True
            db.session.add(example)
            db.session.commit()

        q = db.session.query(User).filter(User.email == 'example@example.com')
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
            example.cuisine_type= ['ciao','pippo']
            example.prec_measures = ''
            example.tot_reviews = 2
            example.avg_rating = 2.0

            db.session.add(example)
            db.session.commit()
        '''
        q = db.session.query(Restaurant).filter(Restaurant.id == 1)
        restaurant = q.first()
        print(restaurant)
        print(restaurant.cuisine_type)
        print(restaurant.owner_id)
        print(restaurant.owner)


        q = db.session.query(Table).filter(Table.id == 1)
        table = q.first()
        if table is None:
            example = Table()
            example.restaurant_id = restaurant.id
            example.name = 'table'
            example.capacity = 10        

            db.session.add(example)
            db.session.commit()
        
        q = db.session.query(Table).filter(Table.id == 1)
        table = q.first()
        print(table)
        print(table.name)
        print(table.restaurant_id)
        


        q = db.session.query(WorkingDay).filter(WorkingDay.id == 1)
        wd = q.first()
        if wd is None:
            example = WorkingDay()
            example.restaurant_id = restaurant.id
            example.work_shifts = [('12:00','15:00'), ('19:00','23:00')]
            example.day = 1       

            db.session.add(example)
            db.session.commit()

        q = db.session.query(WorkingDay).filter(WorkingDay.id == 1)
        wd = q.first()
        print(wd)
        print(wd.work_shifts)
        print(wd.day)


        q = db.session.query(Reservation).filter(Reservation.id == 1)
        r = q.first()
        if r is None:
            example = Reservation()
            example.booker_id = user.id
            example.restaurant_id = restaurant.id
            example.table_id = table.id
            example.date = datetime.datetime(2020, 10, 5)            
            example.hour =  ('19:00','20:00')
            example.cancelled = False        

            db.session.add(example)
            db.session.commit()

        q = db.session.query(Reservation).filter(Reservation.id == 1)
        r = q.first()
        print(r)
        print(r.hour)
        print(r.restaurant_id)


        q = db.session.query(Like)
        l = q.first()
        if l is None:
            example = Like()
            example.liker_id = user.id
            example.restaurant_id = restaurant.id
            example.marked = True        

            db.session.add(example)
            db.session.commit()

        q = db.session.query(Like)
        l = q.first()
        print(l)
        print(l.marked)
        print(l.liker_id)

        q = db.session.query(Seat).filter(Seat.reservation_id == 1, Seat.user_id==1)
        s = q.first()
        if s is None:
            example = Seat()
            example.reservation_id = r.id
            example.user_id = user.id
            example.confirmed = True        

            db.session.add(example)
            db.session.commit()

        q = db.session.query(Seat).filter(Seat.reservation_id == 1, Seat.user_id==1)
        s = q.first()
        print(s)
        print(s.confirmed)
        print(s.user_id)


        q = db.session.query(Review)
        rev = q.first()
        if rev is None:
            example = Review()
            example.reviewer_id = user.id
            example.restaurant_id = restaurant.id
            example.marked = True        
            example.rating = 2
            example.comment = "ciao"
            example.date = datetime.datetime(2002,10,5)

            db.session.add(example)
            db.session.commit()

        q = db.session.query(Review)
        rev = q.first()
        print(rev)
        print(rev.marked)
        print(rev.comment)


        q = db.session.query(Photo).filter(Photo.id == 1)
        ph = q.first()
        if ph is None:
            example = Photo()
            example.restaurant_id = restaurant.id
            example.path = 'http://...'
            example.description = 'abc'

            db.session.add(example)
            db.session.commit()

        q = db.session.query(Photo).filter(Photo.id == 1)
        ph = q.first()
        print(ph)
        print(ph.path)
        print(ph.restaurant_id)


        q = db.session.query(Dishes).filter(Dishes.id == 1)
        d = q.first()
        if d is None:
            example = Dishes()
            example.restaurant_id = restaurant.id
            example.price = 1.50
            example.name = 'pizza'
            example.ingredients = ('tomato', 'flour')            

            db.session.add(example)
            db.session.commit()

        q = db.session.query(Dishes).filter(Dishes.id == 1)
        d = q.first()
        print(d)
        print(d.name)
        print(d.ingredients)


        q = db.session.query(ReportOfPositivity).filter(ReportOfPositivity.user_id == 1)
        rop = q.first()
        if rop is None:
            example = ReportOfPositivity()
            example.user_id = user.id
            example.date = datetime.datetime(2020, 10, 5)            

            db.session.add(example)
            db.session.commit()

        q = db.session.query(ReportOfPositivity).filter(ReportOfPositivity.user_id == 1)
        rop = q.first()
        print(rop)
        print(rop.user_id)
        print(rop.date)



        q = db.session.query(Quarantine).filter(Quarantine.user_id == 1)
        quar = q.first()
        if quar is None:
            example = Quarantine()
            example.user_id = user.id
            example.start_date = datetime.datetime(2020, 10, 5)            
            example.end_date = datetime.datetime(2020, 10, 6)            
            example.active = False

            db.session.add(example)
            db.session.commit()

        q = db.session.query(Quarantine).filter(Quarantine.user_id == 1)
        quar = q.first()
        print(quar)
        print(quar.user_id)
        print(quar.active)


        q = db.session.query(Notification).filter(Notification.user_id == 1)
        note = q.first()
        if note is None:
            example = Notification()
            example.user_id = user.id
            example.message = 'You are infected'
            example.pending = True
            example.type_ = 0
            example.date = datetime.datetime(2020, 10, 5)            

            db.session.add(example)
            db.session.commit()

        q = db.session.query(Notification).filter(Notification.user_id == 1)
        note = q.first()
        print(note)
        print(note.user_id)
        print(note.message)
        '''

    return app
    


if __name__ == '__main__':
    app = create_app()
    app.run()

