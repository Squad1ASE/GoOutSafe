from flask import Blueprint, redirect, render_template, request
from monolith.database import db, Restaurant, Like
from monolith.auth import admin_required, current_user
from flask_login import (current_user, login_user, logout_user,
                         login_required)
from monolith.forms import UserForm
from monolith.forms import RestaurantForm
from monolith.views import auth

restaurants = Blueprint('restaurants', __name__)

@restaurants.route('/create_restaurant', methods=['GET','POST']) # why GET?
def create_restaurant():
    if current_user is not None and hasattr(current_user, 'id'):

        form = RestaurantForm()    
        if request.method == 'POST':

            if form.validate_on_submit():
                new_restaurant = Restaurant()
                form.populate_obj(new_restaurant)
               
                new_restaurant.owner_id = current_user.id
                new_restaurant.likes = 0 
                new_restaurant.cuisine_type = [Restaurant.CUISINE_TYPES[int(i)-1] for i in form.cuisine_type.data]
                new_restaurant.prec_measures = form.prec_measures.data
                
                db.session.add(new_restaurant)
                db.session.commit()
                return redirect('/restaurants')

        return render_template('create_restaurant.html', form=form)

    else:

        return redirect('/login')
        



@restaurants.route('/restaurants')
def _restaurants(message=''):
    allrestaurants = db.session.query(Restaurant)
    return render_template("restaurants.html", message=message, restaurants=allrestaurants, base_url="http://127.0.0.1:5000/restaurants")

@restaurants.route('/restaurants/<restaurant_id>')
def restaurant_sheet(restaurant_id):
    record = db.session.query(Restaurant).filter_by(id = int(restaurant_id)).all()[0]
    return render_template("restaurantsheet.html", name=record.name, likes=record.likes, lat=record.lat, lon=record.lon, phone=record.phone)

@restaurants.route('/restaurants/like/<restaurant_id>')
@login_required
def _like(restaurant_id):
    q = Like.query.filter_by(liker_id=current_user.id, restaurant_id=restaurant_id)
    if q.first() != None:
        new_like = Like()
        new_like.liker_id = current_user.id
        new_like.restaurant_id = restaurant_id
        db.session.add(new_like)
        db.session.commit()
        message = ''
    else:
        message = 'You\'ve already liked this place!'
    return _restaurants(message)
