from flask import Blueprint, redirect, render_template, request, make_response
from monolith.database import db, Restaurant, Like, WorkingDay, Table, Dish, Seat, Review, Reservation
from monolith.auth import admin_required, current_user
from flask_login import (current_user, login_user, logout_user,
                         login_required)
from monolith.forms import UserForm, RestaurantForm, ReservationPeopleEmail, SubReservationPeopleEmail, ReviewForm
from monolith.views import auth
import datetime
from flask_wtf import FlaskForm
import wtforms as f
from wtforms import Form
from wtforms.validators import DataRequired, Length, Email, NumberRange
import ast

restaurants = Blueprint('restaurants', __name__)


def _check_working_days(form_working_days):
    working_days_to_add = []
    
    for wd in form_working_days:
        new_wd = WorkingDay()
        str_shifts = '[' + wd['work_shifts'] + ']'
        shifts = list(ast.literal_eval(str_shifts))
        new_wd.work_shifts = shifts
        new_wd.day = wd['day']

        working_days_to_add.append(new_wd)

    return working_days_to_add


def _check_tables(form_tables):
    tables_to_add = []
    tot_capacity = 0

    for table in form_tables:
        new_table = Table(**table)
        tot_capacity += new_table.capacity
        tables_to_add.append(new_table)

    return tables_to_add, tot_capacity


def _check_dishes(form_dishes):
    dishes_to_add = []

    for dish in form_dishes:
        new_dish = Dish(**dish)
        dishes_to_add.append(new_dish)

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

                working_days_to_add = []
                tables_to_add = []
                dishes_to_add = []
                new_restaurant = Restaurant()

                # check that all restaurant/working days/tables/dishes fields are correct
                try:
                    working_days_to_add = _check_working_days(form.workingdays.data)
                    del form.workingdays

                    tables_to_add, tot_capacity = _check_tables(form.tables.data)
                    del form.tables

                    dishes_to_add = _check_dishes(form.dishes.data)
                    del form.dishes

                    form.populate_obj(new_restaurant)
                    new_restaurant.owner_id = current_user.id
                    new_restaurant.capacity = tot_capacity
                except:
                    return make_response(render_template('create_restaurant.html', form=RestaurantForm()), 400)

                db.session.add(new_restaurant)
                db.session.commit()

                # database check when insert the tables and dishes
                for l in [working_days_to_add, tables_to_add, dishes_to_add]:
                    for el in l:
                        el.restaurant_id = new_restaurant.id
                        db.session.add(el)
                db.session.commit()
                
                return redirect('/restaurants')

            else:
                # invalid form
                return make_response(render_template('create_restaurant.html', form=form), 400)

        return render_template('create_restaurant.html', form=form)

    else:
        return make_response(render_template('error.html', message="You are not logged! Redirecting to login page", redirect_url="/login"), 403)


@restaurants.route('/restaurants/<restaurant_id>', methods=['GET', 'POST'])
@login_required
def restaurant_sheet(restaurant_id):
    restaurantRecord = db.session.query(Restaurant).filter_by(id = int(restaurant_id)).all()[0]

    reviews = Review.query.filter_by(restaurant_id=int(restaurant_id)).all()
    ratings = 5

    reservation = Reservation.query.filter_by(booker_id = int(current_user.id)).first()

    # the user has not been at restaurant yet
    if (reservation is not None and reservation.date > datetime.date.today()):
        reservation = None

    review = Review.query.filter_by(reviewer_id = int(current_user.id)).filter_by(restaurant_id=restaurant_id).first()

    tableRecords = db.session.query(Table).filter(Table.restaurant_id == restaurant_id)

    cuisinetypes = ""
    for cuisine in restaurantRecord.cuisine_type:
        cuisinetypes = cuisinetypes+cuisine.name+" "

    form = ReviewForm()

    if request.method == 'POST':

        # check if the current user is the health_authority
        if current_user.email == 'healthauthority@ha.com':
            return make_response(render_template('error.html', message="You are the health authority! Redirecting to home page", redirect_url="/"), 403)

        # check if the current user is the owner
        if current_user.id == restaurantRecord.owner_id:
            return make_response(render_template('error.html', message="You are the owner of this restaurant! Redirecting to home page", redirect_url="/"), 403)

        # check if the user has never been at the restaurant 
        if reservation is None:
            return make_response(render_template('error.html', message="You have never been at this restaurant! Redirecting to home page", redirect_url="/"), 403)

        # check if the user has already left a review for this restaurant
        if review is not None:
            return make_response(render_template('error.html', message="You have already reviewed this restaurant! Redirecting to home page", redirect_url="/"), 403)


        if form.validate_on_submit():
            # add to database
            new_review = Review()
            new_review.marked = False
            new_review.comment = request.form['comment']
            new_review.rating = request.form['rating']
            new_review.date = datetime.date.today()
            new_review.restaurant_id = restaurant_id
            new_review.reviewer_id = current_user.id
            db.session.add(new_review)
            db.session.commit()

            # after the review don't show the possibility to add another review
            reviews = Review.query.filter_by(restaurant_id=int(restaurant_id)).all()
            return render_template("restaurantsheet_alreadyreviewed.html", name=restaurantRecord.name, 
                                                    likes=restaurantRecord.likes, 
                                                    lat=restaurantRecord.lat, 
                                                    lon=restaurantRecord.lon, 
                                                    phone=restaurantRecord.phone,
                                                    precmeasures=restaurantRecord.prec_measures,
                                                    cuisinetype=cuisinetypes,
                                                    totreviews=restaurantRecord.tot_reviews,
                                                    avgrating=restaurantRecord.avg_rating,
                                                    tables=tableRecords,
                                                    base_url="http://127.0.0.1:5000/restaurants/"+restaurant_id,
                                                    reviews=reviews
                                                    )
        
        else:
            # invalid form
            return render_template("restaurantsheet.html", name=restaurantRecord.name, 
                                                    likes=restaurantRecord.likes, 
                                                    lat=restaurantRecord.lat, 
                                                    lon=restaurantRecord.lon, 
                                                    phone=restaurantRecord.phone,
                                                    precmeasures=restaurantRecord.prec_measures,
                                                    cuisinetype=cuisinetypes,
                                                    totreviews=restaurantRecord.tot_reviews,
                                                    avgrating=restaurantRecord.avg_rating,
                                                    ratings=ratings,
                                                    tables=tableRecords,
                                                    base_url="http://127.0.0.1:5000/restaurants/"+restaurant_id,
                                                    form=form,
                                                    reviews=reviews
                                                    ), 400

    elif current_user.id == restaurantRecord.owner_id or reservation is None or review is not None or current_user.email == 'healthauthority@ha.com':
        # get from the owner: don't show the possibility to add a review
        return render_template("restaurantsheet_alreadyreviewed.html", name=restaurantRecord.name, 
                                                    likes=restaurantRecord.likes, 
                                                    lat=restaurantRecord.lat, 
                                                    lon=restaurantRecord.lon, 
                                                    phone=restaurantRecord.phone,
                                                    precmeasures=restaurantRecord.prec_measures,
                                                    cuisinetype=cuisinetypes,
                                                    totreviews=restaurantRecord.tot_reviews,
                                                    avgrating=restaurantRecord.avg_rating,
                                                    tables=tableRecords,
                                                    base_url="http://127.0.0.1:5000/restaurants/"+restaurant_id,
                                                    reviews=reviews
                                                    ), 555
    else:
        # get from a customer
        return render_template("restaurantsheet.html", name=restaurantRecord.name, 
                                                    likes=restaurantRecord.likes, 
                                                    lat=restaurantRecord.lat, 
                                                    lon=restaurantRecord.lon, 
                                                    phone=restaurantRecord.phone,
                                                    precmeasures=restaurantRecord.prec_measures,
                                                    cuisinetype=cuisinetypes,
                                                    totreviews=restaurantRecord.tot_reviews,
                                                    avgrating=restaurantRecord.avg_rating,
                                                    ratings=ratings,
                                                    tables=tableRecords,
                                                    base_url="http://127.0.0.1:5000/restaurants/"+restaurant_id,
                                                    form=form,
                                                    reviews=reviews
                                                    )



@restaurants.route('/restaurants')
def _restaurants(message=''):
    allrestaurants = db.session.query(Restaurant)
    return render_template("restaurants.html", message=message, restaurants=allrestaurants, base_url="http://127.0.0.1:5000/restaurants")

'''
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
'''

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
