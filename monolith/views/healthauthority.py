from flask import Blueprint, redirect, render_template, request, make_response, url_for
from monolith.database import db, User, Quarantine
from monolith.auth import admin_required
from monolith.forms import GetPatientInformationsForm
from flask_login import (current_user, login_user, logout_user,
                         login_required)
import datetime

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