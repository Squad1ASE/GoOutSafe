from flask import Blueprint, render_template, redirect

from monolith.database import db, Restaurant, Like, Notification
from monolith.auth import current_user


home = Blueprint('home', __name__)


@home.route('/')
def index():
    if current_user is not None and hasattr(current_user, 'id'):
        if current_user.role == 'admin':
            restaurants = db.session.query(Restaurant)
            return render_template("homepage_info.html", restaurants=restaurants, base_url="http://127.0.0.1:5000/restaurants") 

        if current_user.role == 'ha':
            return render_template("homepage_info.html") 

        if current_user.role == 'customer':
            notifications = db.session.query(Notification).filter(Notification.user_id == current_user.id).all()
            return render_template("homepage_info.html", notifications=notifications) 

        if current_user.role == 'owner':
            restaurants = db.session.query(Restaurant).filter(Restaurant.owner_id == current_user.id)
            notifications = db.session.query(Notification).filter(Notification.user_id == current_user.id).all()
            return render_template("homepage_info.html", notifications=notifications, restaurants=restaurants, base_url="http://127.0.0.1:5000/edit_restaurant_informations") 
    else:
        return render_template("homepage.html") 

'''
@home.route('/')
def index():
    if current_user is not None and hasattr(current_user, 'id'):
        if current_user.role == 'admin':
            restaurants = db.session.query(Restaurant)
            return render_template("index.html", restaurants=restaurants) 

        if current_user.role == 'ha':
            return redirect('/patient_informations')

        if current_user.role == 'customer':
            restaurants = db.session.query(Restaurant)
            return render_template("restaurants.html", restaurants=restaurants, base_url="http://127.0.0.1:5000/restaurants")

        if current_user.role == 'owner':
            restaurants = db.session.query(Restaurant).filter(Restaurant.owner_id == current_user.id)
            if restaurants.first() is None:
                return render_template('error.html', message="You have not restaurants! Redirecting to create a new one", redirect_url="/create_restaurant")
            return render_template("restaurant_informations_edit.html", restaurants=restaurants)
    else:
        return render_template("homepage.html") 
'''