from flask import Blueprint, redirect, render_template, request, make_response, url_for
from monolith.database import db, User, Quarantine
from monolith.auth import admin_required
from monolith.forms import GetPatientInformationsForm, MarkPositiveForm
from flask_login import (current_user, login_user, logout_user,
                         login_required)

healthauthority = Blueprint('healthauthority', __name__)

@healthauthority.route('/mark_patient', methods=['GET','POST'])
@login_required
def mark_patient():

    if(current_user.email != "healthauthority@ha.com"):
       return make_response(render_template('error.html', message="Access denied!", redirect_url="/"), 403)

    if request.args.get("email") == None or request.args.get("firstname") == None or request.args.get("lastname") == None or request.args.get("dateofbirth") == None or request.args.get("id") == None:
       return make_response(render_template('error.html', message="User doesn't exists!", redirect_url="/"), 404)

    form = MarkPositiveForm()
    if request.method == 'POST':

        if request.form['mark_positive_button'] == 'mark_positive':
            quarantine = Quarantine()
            form.populate_obj(quarantine)
            quarantine.user_id = request.args.get('id')
            db.session.add(quarantine)
            db.session.commit()
            return redirect('/')


    return render_template('patient_informations.html', 
                                                        email=request.args.get("email"),
                                                        firstname=request.args.get("firstname"),
                                                        lastname=request.args.get("lastname"),
                                                        dateofbirth=request.args.get("dateofbirth"),
                                                        form=form
                                                        )




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
            if(getuser is None):
                # email isn't correct, user doesn't exist
                form.email.errors.append("Wrong email. User doesn't exist")
                return render_template('generic_template.html', form=form), 404
            else:
                return redirect(url_for(
                                    '.mark_patient', 
                                        email=getuser.email,
                                        firstname=getuser.firstname,
                                        lastname=getuser.lastname,
                                        dateofbirth=getuser.dateofbirth,
                                        id=getuser.id))
                #return redirect('/mark_patient',user=getuser)


    return render_template('generic_template.html', form=form)


    #users = db.session.query(User)
    #return render_template("users.html", users=users)
