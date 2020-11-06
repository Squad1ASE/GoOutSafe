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