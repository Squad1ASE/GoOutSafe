from flask import Blueprint, render_template, redirect, request, make_response
from flask_login import (current_user, login_user, logout_user,
                         login_required)

from monolith.database import db, User
from monolith.forms import LoginForm

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user is not None and hasattr(current_user, 'id'):
        return redirect('/')
        
    form = LoginForm()
    if form.validate_on_submit():
        email, password = form.data['email'], form.data['password']
        q = db.session.query(User).filter(User.email == email)
        user = q.first()
        
        if user is not None and user.authenticate(password):
            login_user(user)
            return redirect('/')
        else:
            form.password.errors.append("Invalid credentials.")
            return make_response(render_template('login.html', form=form), 401)   

    #return render_template('login.html', form=form)
    # invalid form
    return make_response(render_template('login.html', form=form), 400)

@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')
