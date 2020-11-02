from flask import Blueprint, redirect, render_template, request, make_response
from monolith.database import db, Restaurant, Like, Table, Dish, Reservation, Seat
from monolith.auth import admin_required, current_user
from flask_login import (current_user, login_user, logout_user,
                         login_required)
from monolith.forms import UserForm
from monolith.forms import RestaurantForm, ReservationPeopleEmail, SubReservationPeopleEmail
from monolith.views import auth
import datetime
from flask_wtf import FlaskForm
import wtforms as f
from wtforms import Form
from wtforms.validators import DataRequired, Length, Email, NumberRange

restaurants = Blueprint('restaurants', __name__)


@restaurants.route('/create_restaurant', methods=['GET','POST'])
def create_restaurant():
    if current_user is not None and hasattr(current_user, 'id'):
        form = RestaurantForm()    

        if request.method == 'POST':

            if form.validate_on_submit():

                tables = form.tables.data
                del form.tables

                dishes = form.dishes.data 
                del form.dishes
                    
                tot_capacity = 0
                tables_to_add = []
                for table in tables:
                    table = Table(**table)
                    tot_capacity += table.capacity
                    tables_to_add.append(table)
                
                new_restaurant = Restaurant()
                form.populate_obj(new_restaurant)
                new_restaurant.owner_id = current_user.id
                new_restaurant.capacity = tot_capacity
                
                db.session.add(new_restaurant)
                db.session.commit()

                for table in tables_to_add:
                    table.restaurant_id = new_restaurant.id
                    db.session.add(table)

                for dish in dishes:
                    new_dish = Dish(**dish)
                    new_dish.restaurant_id = new_restaurant.id
                    db.session.add(new_dish)

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
    restaurantRecord = db.session.query(Restaurant).filter_by(id = int(restaurant_id)).all()[0]

    tableRecords = db.session.query(Table).filter(Table.restaurant_id == restaurant_id)

    cuisinetypes = ""
    for cuisine in restaurantRecord.cuisine_type:
        cuisinetypes = cuisinetypes+cuisine.name+" "

    return render_template("restaurantsheet.html", name=restaurantRecord.name, 
                                                    likes=restaurantRecord.likes, 
                                                    lat=restaurantRecord.lat, 
                                                    lon=restaurantRecord.lon, 
                                                    phone=restaurantRecord.phone,
                                                    precmeasures=restaurantRecord.prec_measures,
                                                    cuisinetype=cuisinetypes,
                                                    totreviews=restaurantRecord.tot_reviews,
                                                    avgrating=restaurantRecord.avg_rating,
                                                    tables=tableRecords,
                                                    base_url="http://127.0.0.1:5000/restaurants/"+restaurant_id
                                                    )

@restaurants.route('/restaurants/<int:restaurant_id>/reservation/<int:table_id>', methods=['GET','POST'])
@login_required
def reservation(restaurant_id,table_id):
    # checking if restaurant and table are correct
    restaurantRecord = db.session.query(Restaurant).filter_by(id = restaurant_id).first()
    if(restaurantRecord is None):
        return make_response(render_template('error.html', message="Restaurant doesn't exist", redirect_url="/restaurants"), 404)

    tableRecord = db.session.query(Table).filter_by(id = table_id).first()
    if(tableRecord is None):
        return make_response(render_template('error.html', message="Table doesn't exist", redirect_url="/restaurants/"+str(restaurant_id)), 404)
    
    class test(FlaskForm):
        guest = f.FieldList(f.FormField(SubReservationPeopleEmail), min_entries=tableRecord.capacity, max_entries=tableRecord.capacity)
        display = ['guest']
    
    #form = ReservationPeopleEmail()
    form = test()
    #print(tableRecord.capacity)
    #form.capacity = tableRecord.capacity

    if request.method == 'POST':

            if form.validate_on_submit():

                reservation = Reservation()
                reservation.booker_id = current_user.id
                reservation.restaurant_id = restaurant_id
                reservation.table_id = table_id
                # TODO change date when work shifts available
                reservation.date = datetime.date(2020, 10, 5)
                reservation.hour = datetime.date(2020, 10, 5)
                reservation.cancelled = False

                db.session.add(reservation)
                db.session.commit()
                print(reservation.id)
                for emailField in form.guest.data:
                    print("DENTRO")
                    seat = Seat()
                    seat.reservation_id = reservation.id
                    seat.guests_email = emailField['email']
                    seat.confirmed = True

                    db.session.add(seat)

                db.session.commit()

            # this isn't an error
            return render_template('error.html', message="Reservation has been placed", redirect_url="/")
                
    return render_template('reservation.html', form=form)

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
