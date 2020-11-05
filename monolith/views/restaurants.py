from flask import Blueprint, redirect, render_template, request, make_response
from monolith.database import db, Review, Restaurant, Like, WorkingDay, Table, Dish, Seat, Reservation
from monolith.auth import admin_required, current_user
from flask_login import (current_user, login_user, logout_user,
                         login_required)
from monolith.forms import UserForm, RestaurantForm, ReservationPeopleEmail, SubReservationPeopleEmail, ReservationRequest, EditRestaurantForm, ReviewForm
from monolith.views import auth
import datetime
from flask_wtf import FlaskForm
import wtforms as f
from wtforms import Form
from wtforms.validators import DataRequired, Length, Email, NumberRange
import ast
import time
from time import mktime
from datetime import timedelta

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
        if (current_user.role == 'customer' or current_user.role == 'ha'):
            return make_response(render_template('error.html', message="You are not a restaurant owner! Redirecting to home page", redirect_url="/"), 403)

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
                return redirect('/')

            else:
                # invalid form
                return make_response(render_template('create_restaurant.html', form=form), 400)

        return render_template('create_restaurant.html', form=form)

    else:
        return make_response(render_template('error.html', message="You are not logged! Redirecting to login page", redirect_url="/login"), 403)

@restaurants.route('/restaurants')
@login_required
def _restaurants(message=''):

    if (current_user.role == 'ha' or current_user.role == 'owner'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)
    
    allrestaurants = db.session.query(Restaurant)
    return render_template("restaurants.html", message=message, restaurants=allrestaurants, base_url="http://127.0.0.1:5000/restaurants")

@restaurants.route('/restaurants/<restaurant_id>', methods=['GET','POST'])
@login_required
def restaurant_sheet(restaurant_id):

    if (current_user.role == 'ha' or current_user.role == 'owner'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)

    restaurantRecord = db.session.query(Restaurant).filter_by(id = int(restaurant_id)).all()[0]

    #tableRecords = db.session.query(Table).filter(Table.restaurant_id == restaurant_id)

    cuisinetypes = ""
    for cuisine in restaurantRecord.cuisine_type:
        cuisinetypes = cuisinetypes+cuisine.name+" "

    # get menu
    restaurant_menu = db.session.query(Dish).filter_by(restaurant_id = restaurant_id)


    form = ReservationRequest()

    data_dict = dict(name=restaurantRecord.name, 
                                                    likes=restaurantRecord.likes, 
                                                    lat=restaurantRecord.lat, 
                                                    lon=restaurantRecord.lon, 
                                                    phone=restaurantRecord.phone,
                                                    precmeasures=restaurantRecord.prec_measures,
                                                    cuisinetype=cuisinetypes,
                                                    totreviews=restaurantRecord.tot_reviews,
                                                    avgrating=restaurantRecord.avg_rating,
                                                    dishes=restaurant_menu,
                                                    restaurant_id=restaurantRecord.id,
                                                    form=form)


    if request.method == 'POST':

                if form.validate_on_submit():
                    # 1 transform datetime from form in week day
                    # 2 search inside working day DB with restaurant ID, check if in the specific day and time the restaurant is open
                    # 3 check the list of available tables, the search starts from reservation (consider avg_stay_time)
                    # 4 check in the remaining tables if there is at least one that has more or equals seats then the required
                    
                    weekday = form.date.data.weekday() + 1
                    workingday = db.session.query(WorkingDay).filter(WorkingDay.restaurant_id == int(restaurant_id)).filter(WorkingDay.day == WorkingDay.WEEK_DAYS(weekday)).first()
                    
                    if workingday is None:
                        return make_response(render_template('restaurantsheet.html', **data_dict, state_message="Restaurant isn't open this day"), 333)
                    
                    time_span = False
                    reservation_time = time.strptime(request.form['time'], '%H:%M')
                    for shift in workingday.work_shifts:
                        try:
                            start = time.strptime(shift[0], '%H:%M')
                            end = time.strptime(shift[1], '%H:%M')
                            if reservation_time >= start and reservation_time <= end:
                                time_span = True
                                break
                        except:
                            print("except")

                    if time_span is False:
                            return make_response(render_template('restaurantsheet.html', **data_dict, state_message="Restaurant isn't open at this hour"), 444)

                    table_records = db.session.query(Table).filter(
                            Table.restaurant_id == int(restaurant_id),
                            Table.capacity >= form.guests.data
                        ).all()

                    if len(table_records) == 0:
                            return make_response(render_template('restaurantsheet.html', **data_dict, state_message="There are no table with this capacity"), 555)

                    reservation_datetime_str = str(request.form['date']) + " " + str(request.form['time'])
                    reservation_datetime = datetime.datetime.strptime(reservation_datetime_str, "%d/%m/%Y %H:%M")

                    start_reservation = reservation_datetime - timedelta(minutes=restaurantRecord.avg_time_of_stay)
                    end_reservation = reservation_datetime + timedelta(minutes=restaurantRecord.avg_time_of_stay)

    
                    reserved_table_records = db.session.query(Reservation).filter(
                            Reservation.date >= start_reservation,
                            Reservation.date <= end_reservation,
                            Reservation.cancelled == False
                        ).all()

                    #reserved_table_id = reserved_table_records.values('table_id')
                    reserved_table_id = [reservation.table_id for reservation in reserved_table_records]
                    table_records.sort(key=lambda x: x.capacity)

                    table_id_reservation = None
                    for table in table_records:
                        if table.id not in reserved_table_id:
                            table_id_reservation = table.id
                            break


                    if table_id_reservation is None:
                            return make_response(render_template('restaurantsheet.html', **data_dict, state_message="No table available for this amount of people at this time"), 404)
                    else:
                        return redirect('/restaurants/'+str(restaurant_id)+'/reservation?table_id='+str(table_id_reservation)+'&'+'guests='+str(form.guests.data)+'&'+'date='+reservation_datetime_str)
                        #return redirect('/restaurants/'+str(restaurant_id)+'/reservation', table_id=table_id_reservation, guests=form.guests.data)


    return render_template("restaurantsheet.html", **data_dict)

@restaurants.route('/restaurants/<int:restaurant_id>/reservation', methods=['GET','POST'])
@login_required
def reservation(restaurant_id):

    if (current_user.role == 'owner' or current_user.role == 'ha'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)

    table_id = int(request.args.get('table_id'))

    # minus 1 because one is the user placing the reservation
    guests = int(request.args.get('guests')) -1
    date = datetime.datetime.strptime(request.args.get('date'), "%d/%m/%Y %H:%M")
    #table_id = int(request.get('table_id'))
    #guests = int(request.get('guests'))

    # checking if restaurant and table are correct
    # TODO maybe this part could be removed, I did it before removing access to table to the users
    '''
    restaurantRecord = db.session.query(Restaurant).filter_by(id = restaurant_id).first()
    if(restaurantRecord is None):
        return make_response(render_template('error.html', message="Restaurant doesn't exist", redirect_url="/restaurants"), 404)

    tableRecord = db.session.query(Table).filter_by(id = table_id).first()
    if(tableRecord is None):
        return make_response(render_template('error.html', message="Table doesn't exist", redirect_url="/restaurants/"+str(restaurant_id)), 404)
    '''
    class test(FlaskForm):
        guest = f.FieldList(f.FormField(SubReservationPeopleEmail), min_entries=guests, max_entries=guests)
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
                reservation.date = date
                reservation.cancelled = False

                #this prevents concurrent reservations
                check_reservation = db.session.query(Reservation).filter(
                            Reservation.date == reservation.date,
                            Reservation.table_id == reservation.table_id,
                            Reservation.restaurant_id == reservation.restaurant_id,
                            Reservation.cancelled == False
                        ).first()

                if check_reservation is not None:
                    return render_template('error.html', message="Ops someone already placed a reservation", redirect_url='/restaurants/'+str(restaurant_id))


                db.session.add(reservation)
                db.session.commit()
                for emailField in form.guest.data:
                    seat = Seat()
                    seat.reservation_id = reservation.id
                    seat.guests_email = emailField['email']
                    seat.confirmed = True

                    db.session.add(seat)

                # seat of the booker
                seat = Seat()
                seat.reservation_id = reservation.id
                seat.guests_email = current_user.email
                seat.confirmed = True

                db.session.add(seat)

                db.session.commit()

                # this isn't an error
                return make_response(render_template('error.html', message="Reservation has been placed", redirect_url="/"), 666)
                
    return render_template('reservation.html', form=form)

@restaurants.route('/restaurants/like/<restaurant_id>')
@login_required
def _like(restaurant_id):

    if (current_user.role == 'owner' or current_user.role == 'ha'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)

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

        if (current_user.role == 'ha' or current_user.role == 'customer'):
            return make_response(render_template('error.html', message="You are not an owner! Redirecting to home page", redirect_url="/"), 403)

        restaurants = db.session.query(Restaurant).filter(Restaurant.owner_id == current_user.id)
        if restaurants.first() is None:
            return make_response(render_template('error.html', message="You have not restaurants! Redirecting to create a new one", redirect_url="/create_restaurant"), 403)

        # in a GET I list all my restaurants
        return render_template("restaurant_informations_edit.html", restaurants=restaurants)

    # user not logged
    return make_response(render_template('error.html', message="You are not logged! Redirecting to login page", redirect_url="/login"), 403)


@restaurants.route('/edit_restaurant_informations/<restaurant_id>', methods=['GET','POST'])
def restaurant_edit(restaurant_id):    
    if current_user is not None and hasattr(current_user, 'id'):

        if (current_user.role == 'ha' or current_user.role == 'customer'):
            return make_response(render_template('error.html', message="You are not an owner! Redirecting to home page", redirect_url="/"), 403)

        record = db.session.query(Restaurant).filter_by(id = int(restaurant_id)).first()
        if record is None:    
            return make_response(
                render_template('error.html', 
                    message="You have not restaurants! Redirecting to create a new one", 
                    redirect_url="/create_restaurant"
                ), 404)


        form = EditRestaurantForm()

        if request.method == 'POST':

            if form.validate_on_submit():

                phone_changed = form.data['phone']                
                #tables_changed = []
                #tot_capacity_changed = -1
                dishes_changed = []
                # check that phone and all tables/dishes fields are correct
                # the changing of tables changes also the overall capacity
                #tables_changed, tot_capacity_changed = _check_tables(form.tables.data)
                #del form.tables

                dishes_changed = _check_dishes(form.dishes.data)
                del form.dishes
                record.phone = phone_changed
                #tables_to_edit = db.session.query(Table).filter(Table.restaurant_id == int(restaurant_id))
                #if tables_to_edit is not None:                    
                #    for t in tables_to_edit:
                #        db.session.delete(t)
                dishes_to_edit = db.session.query(Dish).filter(Dish.restaurant_id == int(restaurant_id))
                if dishes_to_edit is not None: 
                    for d in dishes_to_edit:
                        db.session.delete(d)
                '''
                for l in [tables_changed, dishes_changed]:
                    for el in l:
                        el.restaurant_id = int(restaurant_id)
                        db.session.add(el)                    
                '''
                for el in dishes_changed:
                    newdish = Dish()
                    newdish.restaurant_id = int(restaurant_id)
                    newdish.dish_name = el.dish_name
                    newdish.price = el.price
                    newdish.ingredients = el.ingredients
                    db.session.add(newdish)

                db.session.commit()
                return make_response(render_template('error.html', message="You have correctly edited! Redirecting to your restaurants", redirect_url="/edit_restaurant_informations"), 200)


            else:
                # invalid form
                return make_response(render_template('restaurant_edit.html', form=form, base_url="http://127.0.0.1:5000/edit_restaurant_informations/"+restaurant_id), 400)
        else: 
            # in the GET we fill all the fields
            form.phone.data = record.phone

            # will not be empty since from the creation of the restaurant at least one table was added            
            #tables_to_edit = db.session.query(Table).filter(Table.restaurant_id == int(restaurant_id))
            '''
            i=0
            for t in tables_to_edit:
                form.tables[i].table_name.data = t.table_name
                #print(t.table_name)
                form.tables[i].capacity.data = t.capacity
                #print(t.capacity)
                i = i+1
            '''

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

@restaurants.route('/restaurants/reviews/<restaurant_id>')
@login_required
def create_review(restaurant_id):

    if (current_user.role == 'ha'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)

    restaurantRecord = db.session.query(Restaurant).filter_by(id = int(restaurant_id)).all()[0]

    reviews = Review.query.filter_by(restaurant_id=int(restaurant_id)).all()
    ratings = 5

    reservation = Reservation.query.filter_by(booker_id = int(current_user.id)).first()

    # the user has not been at restaurant yet
    if (reservation is not None and reservation.date > datetime.date.today()):
        reservation = None

    review = Review.query.filter_by(reviewer_id = int(current_user.id)).filter_by(restaurant_id=restaurant_id).first()

    form = ReviewForm()

    if request.method == 'POST':

        if current_user.role == 'owner':
            return make_response(render_template('error.html', message="You are the owner of this restaurant! Redirecting to home page", redirect_url="/"), 403)

        if reservation is None:
            return make_response(render_template('error.html', message="You have never been at this restaurant! Redirecting to home page", redirect_url="/"), 403)

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
            return render_template("reviews_owner.html", reviews=reviews), 200

        else:
            return render_template("reviews.html", form=form,reviews=reviews), 400


    elif current_user.role == 'customer' and review is None and reservation is not None:
        return render_template("reviews.html", form=form, reviews=reviews), 200

    else:
        return render_template("reviews_owner.html", reviews=reviews), 200

