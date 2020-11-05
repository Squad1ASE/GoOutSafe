import os
from flask import Flask
from monolith.database import db, User, Restaurant, Table, WorkingDay
from monolith.database import Reservation, Like, Seat, Review, Photo
from monolith.database import Dish, Quarantine
from monolith.database import Notification
from monolith.views import blueprints
from monolith.auth import login_manager
from monolith.utilities import create_user_EP, user_login_EP, user_logout_EP, create_restaurant_EP, customers_example, restaurant_example, admin_example, health_authority_example, restaurant_owner_example
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
            example.is_admin = True
            db.session.add(example)
            db.session.commit()

    

    test_client = app.test_client()

    create_user_EP(app.test_client(),**health_authority_example)

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
    
    

if __name__ == '__main__':
    app = create_app()
    app.run()

