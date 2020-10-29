from flask import Blueprint, redirect, render_template, request, make_response
from monolith.database import db, User
from monolith.auth import admin_required
from monolith.forms import UserForm
from flask_login import (current_user, login_user, logout_user,
                         login_required)

users = Blueprint('users', __name__)
_called_from_test = False

@users.route('/users')
def _users():
    users = db.session.query(User)
    return render_template("users.html", users=users)


@users.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if current_user is not None and hasattr(current_user, 'id'):
        return make_response(render_template('error.html', message="You are already logged! Redirectig to home page", redirect_url="/"), 403)


    form = UserForm()

    if request.method == 'POST':

        if form.validate_on_submit():
            new_user = User()
            form.populate_obj(new_user)

            check_already_register = db.session.query(User).filter(User.email == new_user.email).first()
            if(check_already_register is not None):
                # already registered
                return render_template('create_user.html', form=form), 403

            new_user.set_password(form.password.data) #pw should be hashed with some salt

            # database check
            try:
                db.session.add(new_user)
                db.session.commit()
            except:
                return make_response(render_template('create_user.html', form=form), 400)

            return redirect('/users')
        else:
            # invalid form
            return make_response(render_template('create_user.html', form=form), 400)
            
        

    return render_template('create_user.html', form=form)