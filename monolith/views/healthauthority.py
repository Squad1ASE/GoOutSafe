from flask import Blueprint, redirect, render_template, request, make_response, url_for
from monolith.database import db, User, Quarantine, Seat, Restaurant, Reservation
from monolith.auth import admin_required
from monolith.forms import GetPatientInformationsForm
from flask_login import (current_user, login_user, logout_user,
                         login_required)
import datetime
from datetime import timedelta
from sqlalchemy import or_, and_

healthauthority = Blueprint('healthauthority', __name__)


@healthauthority.route('/patient_informations', methods=['GET','POST'])
@login_required
def get_patient_informations():
    if(current_user.email != "healthauthority@ha.com"):
        return make_response(render_template('error.html', message="Access denied!", redirect_url="/"), 403)

    form = GetPatientInformationsForm()

    if request.method == 'POST':

        if form.validate_on_submit():
            patient = User()
            form.populate_obj(patient)

            getuser = db.session.query(User).filter(User.email == patient.email).first()
            # email isn't correct, user doesn't exist
            if(getuser is None):
                form.email.errors.append("Wrong email. User doesn't exist")
                return render_template('generic_template.html', form=form), 404

            # email correct, show patient's informations 
            else:
                getuserquarantine_status = db.session.query(Quarantine).filter(Quarantine.user_id == getuser.id and Quarantine.in_observation == True).first()
                # patient is in observation
                if getuserquarantine_status is not None:
                    startdate = getuserquarantine_status.start_date
                    enddate = getuserquarantine_status.end_date
                    state = "patient already under observation"
                else:
                    startdate = datetime.date.today()
                    enddate = startdate + datetime.timedelta(days=14)
                    state = "patient next under observation"

                return redirect(url_for('.get_patient_informations',    email=getuser.email,
                                                                        firstname=getuser.firstname,
                                                                        lastname=getuser.lastname,
                                                                        dateofbirth=getuser.dateofbirth,
                                                                        state=state,
                                                                        startdate=startdate,
                                                                        enddate=enddate
                                                                        ))
        #getuser = db.session.query(User).filter(User.email == request.args.get("email")).first()
        #getuserquarantine_status = db.session.query(Quarantine).filter(Quarantine.user_id == getuser.id and Quarantine.in_observation == True).first()
        #if request.form['mark_positive_button'] == 'mark_positive' and getuserquarantine_status is None:
        if 'mark_positive_button' in request.form and request.form['mark_positive_button'] == 'mark_positive':
                
            getuser = db.session.query(User).filter(User.email == request.args.get("email")).first()

            startdate = datetime.date.today()
            enddate = startdate + datetime.timedelta(days=14)

            quarantine = Quarantine()
            quarantine.user_id = getuser.id
            quarantine.start_date = startdate
            quarantine.end_date = enddate
            quarantine.in_observation = True

            #TODO: maybe try catch here is necessary
            db.session.add(quarantine)
            db.session.commit()   

            # TODO implement contact tracing: retrieve people near the positive one ecc
            _do_contact_tracing(getuser, quarantine.start_date)
                
            # this redirect isn't an error, it display that patient has been successfully marked positive
            return make_response(render_template('error.html', message="Patient marked as positive", redirect_url="/"), 555)     

    if 'go_back_button' in request.form and request.form['go_back_button'] == 'go_back':
        return redirect('/patient_informations')

    if 'email' in request.args:
        getuser = db.session.query(User).filter(User.email == request.args.get("email")).first()
        getuserquarantine_status = db.session.query(Quarantine).filter(Quarantine.user_id == getuser.id and Quarantine.in_observation == True).first()
        
        html = 'patient_informations.html'
        if getuserquarantine_status is not None:
            html = 'patient_informations_nomarkbutton.html'
            
        return render_template(html, email=request.args.get("email"),
                                                            firstname=request.args.get("firstname"),
                                                            lastname=request.args.get("lastname"),
                                                            dateofbirth=request.args.get("dateofbirth"),
                                                            state=request.args.get("state"),
                                                            startdate=request.args.get("startdate"),
                                                            enddate=request.args.get("enddate")
                                                            )

    return render_template('generic_template.html', form=form)


def _do_contact_tracing(user, start_date):
    #TODO: prendere la data 14gg fa -> pre_date
    pre_date = start_date - timedelta(days=14)
    print('user:', user)
    print('user mail:', user.email)
    print('start_date:', start_date)
    print('pre_date:', pre_date)
    user_reservations = db.session.query(Seat)\
        .join(Reservation, Reservation.id == Seat.reservation_id)\
        .filter(
            Seat.guests_email == user.email, 
            Seat.confirmed == True, 
            Reservation.cancelled == False,
            Reservation.date <= start_date,
            Reservation.date >= pre_date
        )\
        .join(Restaurant, Restaurant.id == Reservation.restaurant_id)\
        .join(User, User.id == Restaurant.owner_id)\
        .with_entities(
            Reservation.date, 
            Restaurant.id,
            Restaurant.avg_time_of_stay, 
            User.id,
            User.email
        )\
        .distinct()\
        
    print(user_reservations)
    customers_to_be_notified = set()
    owners_to_be_notified = set()
    for ur in user_reservations:
        date = ur[0]
        restaurant_id = ur[1]
        avg_time_of_stay = ur[2]
        owner_id = ur[3]
        owner_email = ur[4]

        owners_to_be_notified.add((date, owner_email, owner_id))
        print('date:', date)
        print('restaurant_id:', restaurant_id)
        print('avg_time_of_stay:', avg_time_of_stay)
        print('owner_id:', owner_id)
        print('owner_email:', owner_email)

        start_contagion_time = start_date + timedelta(minutes=15)
        span = avg_time_of_stay - 15
        end_contagion_time = start_date + timedelta(minutes=span)

        '''
        users_to_be_notified = db.session.query(Seat)\
            .join(Reservation, Reservation.id == Seat.reservation_id)\
            .filter(
                Seat.confirmed == True, 
                Reservation.cancelled == False,
                Reservation.restaurant_id == restaurant_id
            )\
            .filter(
                (Reservation.date >= date, Reservation.date <= end_contagion_time) |
                (Reservation.date + timedelta(minutes=avg_time_of_stay) >= start_date, Reservation.date + timedelta(minutes=avg_time_of_stay) <= date + timedelta(minutes=avg_time_of_stay) )
            )\
            .with_entities(
                Reservation.date,
                Seat.guests_email,
            )\
            .distinct()
        '''

        users_to_be_notified = db.session.query(Seat)\
            .join(Reservation, Reservation.id == Seat.reservation_id)\
            .filter(
                Seat.confirmed == True, 
                Reservation.cancelled == False,
                Reservation.restaurant_id == restaurant_id
            )\
            .filter(
                or_(
                    and_(Reservation.date >= date, Reservation.date <= end_contagion_time),
                    and_(Reservation.date + timedelta(minutes=avg_time_of_stay) >= start_date, Reservation.date + timedelta(minutes=avg_time_of_stay) <= date + timedelta(minutes=avg_time_of_stay))
                )
            )\
            .with_entities(
                Reservation.date,
                Seat.guests_email,
            )\
            .distinct()

        for u in users_to_be_notified:
            customers_to_be_notified.add(u)

    print('OWNERS TO BE NOTIFIED', owners_to_be_notified)
    print('CUSTOMERS TO BE NOTIFIED', customers_to_be_notified)
    #TODO: fare notifiche
    #owners_to_be_notified
    #customers_to_be_notified