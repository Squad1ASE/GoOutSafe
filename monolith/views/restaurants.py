from flask import Blueprint, redirect, render_template, request, make_response
from monolith.database import db, Restaurant, Like, Table, Dish
from monolith.auth import admin_required, current_user
from flask_login import (current_user, login_user, logout_user,
                         login_required)
from monolith.forms import UserForm
from monolith.forms import RestaurantForm
from monolith.views import auth

restaurants = Blueprint('restaurants', __name__)


def _check_tables(form_tables):
    tables_to_add = []
    tot_capacity = 0
    must_be_present = ['capacity', 'table_name']

    for table in form_tables:
        if 'restaurant_id' in table:
            raise ValueError()

        if not all(k in table for k in must_be_present):
            raise ValueError()

        new_table = Table(**table)
        tot_capacity += new_table.capacity
        tables_to_add.append(new_table)

    if tot_capacity == 0: 
        raise ValueError('At least one table with capacity> 0 must be provided')

    return tables_to_add, tot_capacity


def _check_dishes(form_dishes):
    if form_dishes is None: 
        raise ValueError()
    dishes_to_add = []
    must_be_present = ['dish_name', 'price', 'ingredients']
    for dish in form_dishes:

        if 'restaurant_id' in dish:
            raise ValueError()

        if not all(k in dish for k in must_be_present):
            raise ValueError()

        new_dish = Dish(**dish)
        dishes_to_add.append(new_dish)

    if len(dishes_to_add) == 0: 
        raise ValueError('At least one dish must be provided')

    return dishes_to_add


@restaurants.route('/create_restaurant', methods=['GET','POST'])
def create_restaurant():
    if current_user is not None and hasattr(current_user, 'id'):
        
        form = RestaurantForm()    

        if request.method == 'POST':

            if form.validate_on_submit():
                # if one or more fields that must not be present are
                must_not_be_present = ['owner_id', 'capacity', 'tot_reviews', 'avg_rating', 'likes']
                if any(k in must_not_be_present for k in request.form):
                    return make_response(render_template('create_restaurant.html', form=RestaurantForm()), 400)

                tables_to_add = []
                dishes_to_add = []
                new_restaurant = Restaurant()

                # check that all restaurant/tables/dishes fields are correct
                try:
                    tables_to_add, tot_capacity = _check_tables(form.tables.data)
                    del form.tables

                    dishes_to_add = _check_dishes(form.dishes.data)
                    del form.dishes

                    form.populate_obj(new_restaurant)
                    new_restaurant.owner_id = current_user.id
                    new_restaurant.capacity = tot_capacity
                except:
                    return make_response(render_template('create_restaurant.html', form=RestaurantForm()), 400)

                # database check when insert the new restaurant
                try:
                    db.session.add(new_restaurant)
                    db.session.commit()
                except:
                    db.session.rollback()
                    return make_response(render_template('create_restaurant.html', form=RestaurantForm()), 400)

                # database check when insert the tables and dishes
                try: 
                    for l in [tables_to_add, dishes_to_add]:
                        for el in l:
                            el.restaurant_id = new_restaurant.id
                            db.session.add(el)
                    db.session.commit() #TODO: delete restaurant=? 
                except:
                    db.session.rollback()
                    db.session.delete(new_restaurant)
                    db.session.commit()
                    return make_response(render_template('create_restaurant.html', form=RestaurantForm()), 400)
                
                '''
                for q in db.session.query(Table):
                    print(q.table_name)
                for q in db.session.query(Dish):
                    print(q.dish_name)
                '''

                return redirect('/restaurants')

            else:
                # invalid form
                return make_response(render_template('create_restaurant.html', form=form), 400)

        return render_template('create_restaurant.html', form=form)

    else:
        return make_response(render_template('error.html', message="You are not logged! Redirecting to login page", redirect_url="/login"), 403)



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
