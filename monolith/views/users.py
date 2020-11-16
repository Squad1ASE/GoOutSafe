from flask import Blueprint, redirect, render_template, request, make_response
from monolith.database import db, User, Reservation, Restaurant, Seat, Notification, Table
from monolith.auth import admin_required
from flask_wtf import FlaskForm
import wtforms as f
from wtforms import Form
from wtforms.validators import DataRequired, Length, Email, NumberRange
from monolith.forms import UserForm, EditUserForm, SubReservationPeopleEmail
from flask_login import (current_user, login_user, logout_user,
                         login_required)
import datetime

users = Blueprint('users', __name__)

@users.route('/users')
@login_required
def _users():
    if (current_user.role != 'admin'):
        return make_response(render_template('error.html', message="You are not the admin! Redirecting to home page", redirect_url="/"), 403)
    users = db.session.query(User)
    return render_template("users.html", users=users)


@users.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if current_user is not None and hasattr(current_user, 'id'):
        return make_response(render_template('error.html', message="You are already logged! Redirecting to home page", redirect_url="/"), 403)

    form = UserForm()

    if request.method == 'POST':

        if form.validate_on_submit():

            new_user = User()
            form.populate_obj(new_user)
            new_user.role = request.form['role']
            check_already_register = db.session.query(User).filter(User.email == new_user.email).first()
            
            if(check_already_register is not None):
                # already registered
                return render_template('create_user.html', form=form), 403
                
            new_user.set_password(form.password.data) #pw should be hashed with some salt
            
            if new_user.role != 'customer' and new_user.role != 'owner':
                return make_response(render_template('error.html', message="You can sign in only as customer or owner! Redirecting to home page", redirect_url="/"), 403)
            
            db.session.add(new_user)
            db.session.commit()
            return redirect('/')
        else:
            # invalid form
            return make_response(render_template('create_user.html', form=form), 400)

    return render_template('create_user.html', form=form)

@users.route('/edit_user_informations', methods=['GET', 'POST'])
@login_required
def edit_user():

    form = EditUserForm()
    email = current_user.email
    user = db.session.query(User).filter(User.email == email).first()

    if request.method == 'POST':

        if form.validate_on_submit():

            password = form.data['old_password']
            
            if (user is not None and user.authenticate(password)):
                user.phone = form.data['phone']
                user.set_password(form.data['new_password'])
                db.session.commit()
                return redirect('/logout')
            
            else:
                form.old_password.errors.append("Invalid password.")
                return make_response(render_template('edit_user.html', form=form, email=current_user.email), 401)

        else:
            # invalid form
            return make_response(render_template('edit_user.html', form=form, email=current_user.email), 400)

    else:
        form.phone.data = user.phone
        return render_template('edit_user.html', form=form, email=current_user.email)


@users.route('/users/reservation_list', methods=['GET'])
@login_required
def reservation_list():

    if (current_user.role == 'ha' or current_user.role == 'owner'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)

    reservation_records = db.session.query(Reservation).filter(
        Reservation.booker_id == current_user.id, 
        Reservation.cancelled == False,
        Reservation.date >= datetime.datetime.now()
    ).all()

    data_dict = []
    for reservation in reservation_records:
        rest_name = db.session.query(Restaurant).filter_by(id = reservation.restaurant_id).first().name
        temp_dict = dict(
            restaurant_name = rest_name,
            date = reservation.date,
            reservation_id = reservation.id
        )
        data_dict.append(temp_dict)

    return render_template('user_reservations_list.html', reservations=data_dict, base_url="http://127.0.0.1:5000/users")


@users.route('/users/deletereservation/<reservation_id>')
@login_required
def deletereservation(reservation_id):

    if (current_user.role == 'ha' or current_user.role == 'owner'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)

    reservation = db.session.query(Reservation).filter(
        Reservation.id == reservation_id,
        Reservation.booker_id == current_user.id
    ).first()

    if reservation is not None:

        seat_query = Seat.query.filter_by(reservation_id = reservation.id).all()

        for seat in seat_query:
            seat.confirmed = False

        reservation.cancelled = True

        table = db.session.query(Table).filter(Table.id == reservation.table_id).first()
        restaurant = db.session.query(Restaurant).filter(Restaurant.id == reservation.restaurant_id).first()
        restaurant_owner = db.session.query(User).filter(User.id == restaurant.owner_id).first()


        now = datetime.datetime.now()
        notification = Notification()
        notification.email = restaurant_owner.email
        notification.date = now
        notification.type_ = Notification.TYPE(2)
        notification.message = 'The reservation of the ' + table.table_name + ' table for the date ' + str(reservation.date) + ' has been canceled'
        notification.user_id = restaurant_owner.id

        db.session.add(notification)

        db.session.commit()

    return reservation_list()

@users.route('/users/editreservation/<reservation_id>', methods=['GET','POST'])
@login_required
def editreservation(reservation_id):

    if (current_user.role == 'ha' or current_user.role == 'owner'):
        return make_response(render_template('error.html', message="You are not a customer! Redirecting to home page", redirect_url="/"), 403)

    q = Reservation.query.filter_by(id = reservation_id).first()
    
    if q is not None:

        seat_query = db.session.query(Seat).filter(Seat.reservation_id == q.id).all()

        number_of_guests = len(seat_query) -1

        if(len(seat_query) > 1):

            guests_email_list = list()

            for seat in seat_query:
                if(seat.guests_email != current_user.email):
                    guests_email_list.append(seat.guests_email)

            class edit_form(FlaskForm):
                guest = f.FieldList(f.FormField(SubReservationPeopleEmail), min_entries=number_of_guests, max_entries=number_of_guests)
                display = ['guest']

            form = edit_form()

            if request.method == 'POST':

                if form.validate_on_submit():

                    for i, email_field in enumerate(form.guest.data):

                        seat_query[i].guests_email = email_field['email']
                    
                    db.session.commit()

                    # this isn't an error
                    return make_response(render_template('error.html', message="Guests changed!", redirect_url="/"), 222)


            return render_template('user_reservation_edit.html', form=form)
    
    else:
        return reservation_list()

    
    






