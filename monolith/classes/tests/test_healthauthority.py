from monolith.database import db, User, Quarantine
from monolith.classes.tests.conftest import test_app
import datetime
from sqlalchemy import exc
from flask import url_for


user_example_credentials = dict(
        email='userexample@test.com',
        firstname='firstname_test',
        lastname='lastname_test',
        password='passw',
        dateofbirth='05/10/2000')


def create_user_EP(test_client, data_dict):
    return test_client.post('/create_user',
                            data=data_dict, follow_redirects=True)


def user_login_EP(test_client, email, password):
    return test_client.post('/login',
                            data=dict(email=email,
                                    password=password),
                            follow_redirects=True)

def get_patient_informations(test_client, email):
    return test_client.post('/patient_informations',
                            data=dict(email=email), follow_redirects=True)


def populate_User():
    new_user = User()
    new_user.email = "newtestinguser@test.com"
    new_user.firstname = "firstname_test"
    new_user.lastname = "lastname_test"
    new_user.password = "passw"
    new_user.dateofbirth = datetime.datetime(2020, 10, 5)

    return new_user


def test_mark_positive(test_app):
    app, test_client = test_app

    temp_user_example_dict = user_example_credentials

    create_user_EP(test_client, temp_user_example_dict)

    # --- UNIT TESTS ---
    with app.app_context():
        # mark a wrong user user that doesn't exist
        getuser = db.session.query(User).filter(User.email == 'notexistinguser@test.com').first()
        assert getuser is None

        # get the user to be marked as positive
        getuser = db.session.query(User).filter(User.email == temp_user_example_dict['email']).first()
        
        assert getuser is not None

        new_quarantine = Quarantine()
        new_quarantine.user_id = getuser.id
        today = datetime.date.today()
        new_quarantine.start_date = today
        new_quarantine.end_date = today + datetime.timedelta(days=14)
        new_quarantine.in_observation = True

        db.session.add(new_quarantine)
        db.session.commit()

        getquarantine = db.session.query(Quarantine).filter(Quarantine.user_id == getuser.id).first()
        assert getquarantine is not None
        assert getquarantine.start_date == today
        assert getquarantine.end_date == today + datetime.timedelta(days=14)
        assert getquarantine.in_observation == True

        # change in_observation state, so the user can use the app again
        getquarantine.in_observation = False
        db.session.commit()

        getquarantinenewstatus = db.session.query(Quarantine).filter(Quarantine.user_id == getuser.id).first()
        assert getquarantinenewstatus.in_observation == False

    # --- COMPONENTS TESTS ---

    user_login_EP(test_client, "userexample@test.com", "passw")

    #Try to get informations with a user that is not the health authority
    assert(get_patient_informations(test_client, "userexample@test.com").status_code == 403)

    user_login_EP(test_client, "healthauthority@ha.com", "ha")
    #getuser =  test_client.post('/mark_positive', data=user_example_credentials, follow_redirects=True)
    
    assert(get_patient_informations(test_client, temp_user_example_dict['email']).status_code == 200)

    #Try to get informations of a user that doesn't exist
    assert(get_patient_informations(test_client, 'userexample2@test.com').status_code == 404)