import unittest
from monolith.database import db, User
from monolith.classes.tests.conftest import test_app
import datetime
from sqlalchemy import exc

'''
def test_create_userr(test_app):
    tested_app, app = test_app
    print("SUCCESS")
'''
# why test_app doesn't work?
#class TestUser(unittest.TestCase):

    #test_client = app.test_client()

'''
def test_users(self):
    q = db.session.query(User)
    user = q.first()
'''


def test_create_user(test_app):
    app,test_client = test_app

    # --- UNIT TESTS ---
    with app.app_context():
        # checking user that doesn't exist
        getuser = db.session.query(User).filter(User.email == 'notexistinguser@test.com').first()
        assert getuser is None

        # create a new user and check if he has been added
        new_user = User()
        new_user.email = "newtestinguser@test.com"
        new_user.firstname = "firstname_test"
        new_user.lastname = "lastname_test"
        new_user.password = "passw" 
        new_user.dateofbirth = datetime.datetime(2020, 10, 5)

        db.session.add(new_user)
        db.session.commit()

        getuser = db.session.query(User).filter(User.email == 'newtestinguser@test.com').first()
        assert getuser is not None
        assert getuser.email == 'newtestinguser@test.com'
        assert getuser.firstname == "firstname_test"
        assert getuser.lastname == "lastname_test"
        assert getuser.password == "passw" 
        assert getuser.dateofbirth == datetime.datetime(2020, 10, 5)
        
        # setting a wrong email syntax
        try:
            new_user.email = "newuserwrongemail"
            assert False
        except SyntaxError:
            #print("DENTRO")
            assert True
        except Exception as e:
            assert False

        # creation of a user with an already existing email must fail
        new_user_2 = User()
        new_user_2.email = "newtestinguser@test.com"
        new_user_2.firstname = "firstname_test"
        new_user_2.lastname = "lastname_test"
        new_user_2.password = "passw" 
        new_user_2.dateofbirth = datetime.datetime(2020, 10, 5)
        
        try:
            db.session.add(new_user_2)
            db.session.commit()
            assert False
        except exc.IntegrityError as e:
            assert True
        except Exception as e:
            assert False
        

    # --- COMPONENTS TESTS ---
    data_dict = dict(
        email='newtestinguser2@test.com',
        firstname='firstname_test',
        lastname='lastname_test',
        password='passw',
        dateofbirth='05/10/2000')

    result = test_client.post('/create_user', data=data_dict, follow_redirects=True)
           
    assert result.status_code == 200

    # creation of a user with an already existing email must fail
    result = test_client.post('/create_user', data=data_dict, follow_redirects=True)

    assert result.status_code == 403

    # creation of a user with wrong email syntax
    data_dict['email'] = 'newuserwrongemail'
    result = test_client.post('/create_user', data=data_dict, follow_redirects=True)

    assert result.status_code == 400

    # creation of a user with an already existing email must fail (in this case user was added via db.commit)
    data_dict['email'] = "newtestinguser@test.com"
    result = test_client.post('/create_user', data=data_dict, follow_redirects=True)
           
    assert result.status_code == 403

def test_login_user(test_app):
    app,test_client = test_app

    data_dict = dict(
        email='newtestinguser@test.com',
        firstname='firstname_test',
        lastname='lastname_test',
        password='passw',
        dateofbirth='05/10/2000')

    test_client.post('/create_user', data=data_dict, follow_redirects=True)
    
    # --- UNIT TESTS ---
    with app.app_context():

        # authentication with correct credentials
        getuser = db.session.query(User).filter(User.email == data_dict['email']).first()
        
        assert getuser is not None
        assert getuser.authenticate(data_dict['password']) == True

        # authentication with wrong email
        getuser = db.session.query(User).filter(User.email == "wrongemail@test.com").first()
        
        assert getuser is None

        # authentication with correct email and wrong password
        getuser = db.session.query(User).filter(User.email == data_dict['email']).first()
        
        assert getuser is not None
        assert getuser.authenticate("wrngpass") == False

    # --- COMPONENT TESTS ---
    # authentication with wrong email
    result = test_client.post('/login', data=dict(email = "wrongemail@test.com",
                                                    password = data_dict['password']), 
                                                    follow_redirects=True)
           
    assert result.status_code == 401

    # authentication with correct email and wrong password
    result = test_client.post('/login', data=dict(email = data_dict['email'],
                                                    password = "wrngpass"), 
                                                    follow_redirects=True)
           
    assert result.status_code == 401

    # authentication with wrong email syntax
    result = test_client.post('/login', data=dict(email = "wrongemailsyntax",
                                                    password = data_dict['password']), 
                                                    follow_redirects=True)
           
    assert result.status_code == 400

    # authentication with correct credentials   
    result = test_client.post('/login', data=dict(email = data_dict['email'],
                                                    password = data_dict['password']), 
                                                    follow_redirects=True)
           
    assert result.status_code == 200


    # creation of a new user when already logged in must fail
    data_dict['email'] = 'newtestinguser2@test.com'
    result = test_client.post('/create_user', data=data_dict, follow_redirects=True)

    assert result.status_code == 403

def test_logout_user(test_app):
    app,test_client = test_app

    data_dict = dict(
        email='newtestinguser@test.com',
        firstname='firstname_test',
        lastname='lastname_test',
        password='passw',
        dateofbirth='05/10/2000')

    test_client.post('/create_user', data=data_dict, follow_redirects=True)
    
    # TODO does the unit test even exist?
    # --- UNIT TESTS ---

    # --- COMPONENT TESTS ---

    result = test_client.post('/login', data=dict(email = data_dict['email'],
                                                    password = data_dict['password']), 
                                                    follow_redirects=True)

    assert result.status_code == 200
    # logout 
    result = test_client.get('/logout', follow_redirects=True)

    assert result.status_code == 200
    
