from monolith.database import db, User
from monolith.classes.tests.conftest import test_app
import datetime
from sqlalchemy import exc

# why test_app doesn't work?
#class TestUser(unittest.TestCase):

    #test_client = app.test_client()
    
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


def populate_User():
    new_user = User()
    new_user.email = "newtestinguser@test.com"
    new_user.firstname = "firstname_test"
    new_user.lastname = "lastname_test"
    new_user.password = "passw"
    new_user.dateofbirth = datetime.datetime(2020, 10, 5)

    return new_user


def test_create_user(test_app):
    app, test_client = test_app

    temp_user_example_dict = user_example_credentials

    # --- UNIT TESTS ---
    with app.app_context():
        # checking user that doesn't exist
        getuser = db.session.query(User).filter(User.email == 'notexistinguser@test.com').first()
        assert getuser is None

        # create a new user and check if he has been added
        new_user = populate_User()

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
            assert True
        except Exception:
            assert False

        # creation of a user with an already existing email must fail
        new_user_2 = populate_User()
        try:
            db.session.add(new_user_2)
            db.session.commit()
            assert False
        except exc.IntegrityError:
            assert True
        except Exception:
            assert False
        

    # --- COMPONENTS TESTS ---

    assert create_user_EP(test_client, temp_user_example_dict).status_code == 200

    # creation of a user with an already existing email must fail

    assert create_user_EP(test_client, temp_user_example_dict).status_code ==  403

    # creation of a user with wrong email syntax
    temp_user_example_dict['email'] = 'newuserwrongemail'
    assert create_user_EP(test_client, temp_user_example_dict).status_code == 400

    # creation of a user with an already existing email must fail (in this case user was added via db.commit)
    temp_user_example_dict['email'] = "newtestinguser@test.com"
    assert create_user_EP(test_client, temp_user_example_dict).status_code == 403

def test_login_user(test_app):
    app, test_client = test_app

    temp_user_example_dict = user_example_credentials

    test_client.post('/create_user', data=temp_user_example_dict, follow_redirects=True)
    
    # --- UNIT TESTS ---
    with app.app_context():

        # authentication with correct credentials
        getuser = db.session.query(User).filter(User.email == temp_user_example_dict['email']).first()
        
        assert getuser is not None
        assert getuser.authenticate(temp_user_example_dict['password']) == True

        # authentication with wrong email
        getuser = db.session.query(User).filter(User.email == "wrongemail@test.com").first()
        
        assert getuser is None

        # authentication with correct email and wrong password
        getuser = db.session.query(User).filter(User.email == temp_user_example_dict['email']).first()

        assert getuser is not None
        assert getuser.authenticate("wrngpass") == False

    # --- COMPONENT TESTS ---

    # authentication with wrong email
    assert user_login_EP(test_client, "wrongemail@test.com", temp_user_example_dict['password']).status_code == 401

    # authentication with correct email and wrong password
    assert user_login_EP(test_client, temp_user_example_dict['email'], "wrngpass").status_code == 401

    # authentication with wrong email syntax
    assert user_login_EP(test_client, "wrongemailsyntax", temp_user_example_dict['password']).status_code == 400

    # authentication with correct credentials
    assert user_login_EP(test_client, temp_user_example_dict['email'], temp_user_example_dict['password']).status_code == 200

    # creation of a new user when already logged in must fail
    temp_user_example_dict['email'] = 'newtestinguser2@test.com'
    assert create_user_EP(test_client, temp_user_example_dict).status_code == 403


def test_logout_user(test_app):
    app, test_client = test_app

    temp_user_example_dict = user_example_credentials

    create_user_EP(test_client, temp_user_example_dict)
    
    # TODO does the unit test even exist?
    # --- UNIT TESTS ---

    # --- COMPONENT TESTS ---
    result = user_login_EP(test_client, temp_user_example_dict['email'], temp_user_example_dict['password'])

    assert result.status_code == 200
    # logout
    result = test_client.get('/logout', follow_redirects=True)

    assert result.status_code == 200
