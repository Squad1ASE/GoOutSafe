from monolith.database import db, User, Quarantine
from monolith.classes.tests.conftest import test_app, create_user_EP, user_login_EP, user_example
import datetime
from sqlalchemy import exc


def test_mark_positive(test_app):
    app, test_client = test_app
    
    # create a health authority and an user for testing 
    temp_ha_dict = dict(
        email='healthauthority@ha.com',
        phone='3333333333',
        firstname='Ha',
        lastname='Ha',
        password='ha',
        dateofbirth='05/10/2000'
    )
    temp_user_example_dict = user_example
    assert create_user_EP(test_client, **temp_ha_dict).status_code == 200 
    assert create_user_EP(test_client, **temp_user_example_dict).status_code == 200

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
    # access to patient information is forbidden for customers
    user_login_EP(test_client, user_example['email'], user_example['password'])

    result = test_client.get('/patient_informations', follow_redirects=True)
    assert result.status_code == 403

    test_client.get('/logout', follow_redirects=True)

    # access to health authority is allowed
    user_login_EP(test_client, "healthauthority@ha.com", "ha")

    result = test_client.get('/patient_informations', follow_redirects=True)
    assert result.status_code == 200

    # wrong email must return patient not found
    result = test_client.post('/patient_informations', data=dict(email="wrongemail@test.com"), follow_redirects=True)
    assert result.status_code == 404
    
    # correct email must returns the patient informations 
    result = test_client.post('/patient_informations', data=dict(email=user_example['email']), follow_redirects=True)
    assert result.status_code == 200

    # patient is marked as positive 
    result = test_client.post('/patient_informations?email=userexample%40test.com', data=dict(mark_positive_button='mark_positive'), follow_redirects=True)
    assert result.status_code == 555

    # go to the previous page when patient is already marked as positive
    result = test_client.get('/patient_informations?email=userexample%40test.com', data=dict(mark_positive_button='mark_positive'), follow_redirects=True)
    assert result.status_code == 200
    
