from flask import Blueprint, redirect, render_template, request, make_response
from monolith.database import db, User, Reservation, Restaurant, Seat
from monolith.database import Quarantine, Notification, Like, Review
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


@users.route('/delete_user', methods=['GET', 'POST', 'DELETE'])
@login_required
def delete_user():

    # also the admin cannot be deleted, but since the operation must be visible to him
    # he is not included in this case as error
    if (current_user.role == 'ha'):
        return make_response(render_template('error.html', message="HA is allowed to unregister itself! Redirecting to home page", redirect_url="/"), 403)
   
    user_to_delete = db.session.query(User).filter(User.email == current_user.email).first()
    if( user_to_delete is None): #user not already registered
        return make_response(render_template('error.html', message="Unregistered user is not allowed to unregister itself! Redirecting to home page", redirect_url="/"), 403) 


    # ---------------------------------------- DELETE FROM QUARANTINE
    """
    # check if user is not positive
    get_user_quarantine = db.session.query(Quarantine).filter(Quarantine.user_id == user_to_delete.id and Quarantine.in_observation == True).first()
    if get_user_quarantine is not None: # patient is in observation, un-registration will be done after the deadline        
        return make_response(render_template('error.html', 
            message="You are positive and cannot unregister yourself untill: "+str(get_user_quarantine.end_date)+" Redirecting to home page", redirect_url="/"), 403) 
    """
    # check if user is not positive
    all_user_quarantine = db.session.query(Quarantine).filter(Quarantine.user_id == user_to_delete.id).all()
    for user_quarantine in all_user_quarantine:        
        if user_quarantine.in_observation == True: # patient is in observation, un-registration will be done after the deadline        
            return make_response(render_template('error.html', 
                message="You are positive and cannot unregister yourself till: "+str(user_quarantine.end_date)+" Redirecting to home page", 
                redirect_url="/"), 403) 
        else: # remove patient from Quarantine
            db.session.delete(user_quarantine)
            # the commit is after all the cases
    
    # --------------------------------------------- DELETE FROM NOTIFICATION    
    all_user_notification = db.session.query(Notification).filter(Notification.user_id == user_to_delete.id).all()
    for user_notification in all_user_notification:
        if user_notification is not None:
            db.session.delete(user_notification)
            # the commit is after all the cases
    #------------------------------------------------- DELETE FROM RESERVATION

    all_user_reservation = db.session.query(Reservation).filter(Reservation.booker_id == user_to_delete.id).all()
    for user_reservation in all_user_reservation:
        # is similar to the next function delete reservation which deletes also the seat and table linked to it
        #---------------------------------------------------DELETE FROM SEAT
        all_user_seat = db.session.query(Seat).filter(Seat.reservation_id == user_reservation.id).all()
        for user_seat in all_user_seat:
            
            # first notify all guests for the removing of seat            
            for guest_email in user_set.guests_email: 
                if(guest_email != user_to_delete.email):

                    user_to_notify = db.session.query(User).filter(User.email == guest_email.email).first()
                    if user_to_notify is not None: #notify all guests who are registered
                        new_dict = dict(
                            user_id=user_to_nofitfy.id, 
                            email=guest_email, 
                            message='The reservation in which you were guest has been cancelled', 
                            pending=True, 
                            type_=Notification.TYPE(2),
                            date=datetime.now()
                        )
                        new_notification = Notification(**new_dict)
                        db.session.add(new_notification)
                        #db.session.commit() after all the cases
            
            # then remove the seat
            db.session.delete(user_seat)     
            # commit follows after all cases   
        #---------------------------------------------------DELETE FROM TABLE
        # how is the removing of reservation(FK) - Table?
        # (how does the table know that is again available for another reservation?)
        #---------------------------------------------------DELETE FROM RESTAURANT
        # how is the removing of reservation(FK) - Restaurant?
        # (how does the restaurant know that the reservation is not more available?)

        db.session.delete(user_reservation) 
        #it's commit is after all
    #------------------------------------------------- DELETE FROM LIKE
    all_user_like = db.session.query(Like).filter(Like.liker_id == user_to_delete.id).all()
    for user_like in all_user_like:
        # how does restaurant know that the like is not more available?
        # adjusting it's like counter is enough?
        if user_like.marked == True: #the like was counted by Restaurant.likes
            rest_to_dislike = db.session.query(Restaurant).filter(Restaurant.id == user_like.restaurant_id).first()
            rest_to_dislike.likes = (rest_to_dislike) - 1
            db.session.commit(rest_to_dislike) # commit changes about the like counter of the linked restaurant
        db.session.delete(user_like)
        #it's commit is after all

    #------------------------------------------------- DELETE FROM REVIEW
    all_user_review = db.session.query(Review).filter(Review.reviewer_id == user_to_delete.id).all()
    for user_review in all_user_review:
        # how does restaurant know that the review is not more available?
        # adjusting it's review counter and avg rating is enough is enough?
        if user_review.marked == True:
            rest_to_disreview = db.session.query(Restaurant).filter(Restaurant.id == user_review.restaurant_id).first()
            rest_to_disreview.tot_reviews = rest_to_disreview.tot_reviews - 1
            rest_to_disreview.avg_rating = (rest_to_disreview.avg_rating - user_review.rating)/rest_to_disreview.tot_reviews
            db.session.commit(rest_to_disreview) # commit changes about the review counter and avg of the linked restaurant
        db.session.delete(user_review)


    # till now were deleted all operations available to a customer
    if( user_to_delete.role == 'customer'):
        print('customer ta eliminare')
        db.session.delete(user_to_delete)
        db.session.commit()

    else: #owner
        print('owner da trattare una volta eliminato ristorante')

        #------------------------------------------------- DELETE FROM RESTAURANT
        # DELETE FIRST RESTAURANT AND THE LINKINGS WITH IT
        # then its owner becomes a user that can be deleted



    


    # is shown only to understand that the user was deleted
    # MUST be changed with home page
    users = db.session.query(User)
    return render_template("users.html", users=users)




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

    q = Reservation.query.filter_by(id = reservation_id).first()

    if q is not None:

        seat_query = Seat.query.filter_by(reservation_id = q.id).all()

        for seat in seat_query:
            seat.confirmed = True

        q.cancelled = True

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

    
    






