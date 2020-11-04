from flask import Blueprint, redirect, render_template, request, make_response
from monolith.database import db, Restaurant, Like, Table, Dish
from monolith.auth import admin_required, current_user
from flask_login import (current_user, login_user, logout_user,
                         login_required)
from monolith.forms import UserForm
from monolith.forms import RestaurantForm
from monolith.forms import EditRestaurantForm
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
        raise ValueError('At least one table with capacity > 0 must be provided')

    return tables_to_add, tot_capacity


def _check_dishes(form_dishes):
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
                    db.session.commit()
                except:
                    db.session.rollback()
                    db.session.delete(new_restaurant)
                    db.session.commit()
                    return make_response(render_template('create_restaurant.html', form=RestaurantForm()), 400)

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


@restaurants.route('/edit_restaurant_informations', methods=['GET'])
def restaurant_informations_edit():
    if current_user is not None and hasattr(current_user, 'id'):

        restaurants = db.session.query(Restaurant).filter(Restaurant.owner_id == current_user.id)
        if restaurants.first() is None:
            print('sono qui')
            return make_response(render_template('error.html', message="You have not restaurants! Redirecting to create a new one", redirect_url="/create_restaurant"), 403)

        # in a GET I list all my restaurants
        return render_template("restaurant_informations_edit.html", restaurants=restaurants)

    # user not logged
    return make_response(render_template('error.html', message="You are not logged! Redirecting to login page", redirect_url="/login"), 403)







@restaurants.route('/edit_restaurant_informations/<restaurant_id>', methods=['GET','POST'])
def restaurant_edit(restaurant_id):    
    if current_user is not None and hasattr(current_user, 'id'):

        record = db.session.query(Restaurant).filter_by(id = int(restaurant_id)).all()[0]        
        if record is None:
            return make_response(
                render_template('error.html', 
                    message="You have not restaurants! Redirecting to create a new one", 
                    redirect_url="/create_restaurant"
                ), 403)


        form = EditRestaurantForm()

        if request.method == 'POST':
            print('sono nella post')

            if form.validate_on_submit():
                print('sono nella form')

                phone_changed = form.data['phone']                
                tables_changed = []
                tot_capacity_changed = -1
                dishes_changed = []
                # check that phone and all tables/dishes fields are correct
                try:
                    phone_changed is not None
                    # the changing of tables changes also the overall capacity
                    tables_changed, tot_capacity_changed = _check_tables(form.tables.data)
                    del form.tables

                    dishes_changed = _check_dishes(form.dishes.data)
                    del form.dishes
                except:
                    print('errors during acquiring the element of the form')
                    return make_response(render_template('restaurant_edit.html', form=EditRestaurantForm(), base_url="http://127.0.0.1:5000/edit_restaurant_informations/"+restaurant_id), 400)

                # the try was good, insert changes on a commit of the db
                try:                   
                    record.phone = phone_changed
                    record.capacity = tot_capacity_changed
                    #db.session.commit()
                except:
                    print('errors in the commit of db')
                    return make_response(render_template('restaurant_edit.html', form=EditRestaurantForm(), base_url="http://127.0.0.1:5000/edit_restaurant_informations/"+restaurant_id), 400)

                try: 
                    tables_to_edit = db.session.query(Table).filter(Table.restaurant_id == int(restaurant_id))
                    if tables_to_edit is not None:                    
                        for t in tables_to_edit:
                            db.session.delete(t)
                    dishes_to_edit = db.session.query(Dish).filter(Dish.restaurant_id == int(restaurant_id))
                    if dishes_to_edit is not None:    
                        for d in dishes_to_edit:
                            db.session.delete(t)

                    for l in [tables_changed, dishes_changed]:
                        for el in l:
                            el.restaurant_id = int(restaurant_id)
                            db.session.add(el)
                    #db.session.commit()
                except:
                    print('errors in the delete/add/commit of db')
                    return make_response(render_template('restaurant_edit.html', form=EditRestaurantForm(), base_url="http://127.0.0.1:5000/edit_restaurant_informations/"+restaurant_id), 400)

                db.session.commit()
                return make_response(render_template('error.html', message="You have correctly edited! Redirecting to your restaurants", redirect_url="/edit_restaurant_informations"), 403)


            else:
                print('non sono nella form')
                # invalid form
                return make_response(render_template('restaurant_edit.html', form=form, base_url="http://127.0.0.1:5000/edit_restaurant_informations/"+restaurant_id), 400)
        else: 
            # in the GET we fill all the fields
            form.phone.data = record.phone

            # will not be empty since from the creation of the restaurant at least one table was added            
            tables_to_edit = db.session.query(Table).filter(Table.restaurant_id == int(restaurant_id))
            i=0
            for t in tables_to_edit:
                form.tables[i].table_name.data = t.table_name
                #print(t.table_name)
                form.tables[i].capacity.data = t.capacity
                #print(t.capacity)
                i = i+1

            # will not be empty since from the creation of the restaurant at least one dish was added
            dishes_to_edit = db.session.query(Dish).filter(Dish.restaurant_id == int(restaurant_id))
            i=0
            for d in dishes_to_edit:
                form.dishes[i].dish_name.data = d.dish_name
                form.dishes[i].price.data = d.price
                form.dishes[i].ingredients.data = d.ingredients
                i=i+1

            return render_template('restaurant_edit.html', form=form, base_url="http://127.0.0.1:5000/edit_restaurant_informations/"+restaurant_id)


    # user not logged
    return make_response(
        render_template('error.html', 
            message="You are not logged! Redirecting to login page", 
            redirect_url="/login"
        ), 403)
