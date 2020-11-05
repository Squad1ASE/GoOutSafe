from flask import Blueprint, render_template, redirect

from monolith.database import db, Restaurant, Like
from monolith.auth import current_user


home = Blueprint('home', __name__)


@home.route('/')
def index():
    if current_user is not None and hasattr(current_user, 'id'):
        if current_user.role == 'admin':
            #TODO
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
            #TODO: after merge -> return render_template("restaurant_informations_edit.html", restaurants=restaurants)
            return render_template('restaurants.html', restaurants=restaurants)
        #return render_template('error.html', message="You are not a valid user! Redirecting to create a new one", redirect_url="/create_user"), 404
    else:
        return redirect('/login')
