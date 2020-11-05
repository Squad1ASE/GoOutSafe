from monolith.database import db, User
from monolith.classes.tests.conftest import test_app, create_user_EP, user_login_EP, edit_user_EP, user_example, insert_admin
import datetime
from sqlalchemy import exc


def populate_user():
    new_user = User()
    new_user.email = "newtestinguser@test.com"
    new_user.phone = '3333333333'
    new_user.firstname = "firstname_test"
    new_user.lastname = "lastname_test"
    new_user.password = "passw"
    new_user.dateofbirth = datetime.date(2020, 10, 5)
    new_user.role = "customer"

    return new_user


def test_create_user(test_app):
    app, test_client = test_app

    temp_user_example_dict = user_example

    # --- UNIT TESTS ---
    with app.app_context():
        # checking user that doesn't exist
        getuser = db.session.query(User).filter(User.email == 'notexistinguser@test.com').first()
        assert getuser is None

        # create a new user and check if he has been added
        new_user = populate_user()

        db.session.add(new_user)
        db.session.commit()

        getuser = db.session.query(User).filter(User.email == 'newtestinguser@test.com').first()
        assert getuser is not None
        assert getuser.email == 'newtestinguser@test.com'
        assert getuser.firstname == "firstname_test"
        assert getuser.lastname == "lastname_test"
        assert getuser.password == "passw"
        assert getuser.dateofbirth == datetime.date(2020, 10, 5)
        assert getuser.role == "customer"
        
        # setting a wrong email syntax
        count_assert = 0
        try:
            new_user.email = "newuserwrongemail"
        except SyntaxError:
            count_assert = 1
            assert True
        assert count_assert == 1

        count_assert = 0
        try:
            new_user.role = "norole"
        except SyntaxError:
            count_assert = 1
            assert True
        assert count_assert == 1

        # creation of a user with an already existing email must fail
        new_user_2 = populate_user()
        count_assert = 0
        try:
            db.session.add(new_user_2)
            db.session.commit()
        except exc.IntegrityError:
            count_assert = 1
            assert True
        assert count_assert == 1
        

    # --- COMPONENTS TESTS ---
    assert test_client.get('/create_user').status_code == 200

    assert create_user_EP(test_client, role="admin").status_code == 403

    assert create_user_EP(test_client, **temp_user_example_dict).status_code == 200

    # creation of a user with an already existing email must fail
    assert create_user_EP(test_client, **temp_user_example_dict).status_code ==  403

    # creation of a user with wrong email syntax
    temp_user_example_dict['email'] = 'newuserwrongemail'
    assert create_user_EP(test_client, **temp_user_example_dict).status_code == 400

    # creation of a user with an already existing email must fail (in this case user was added via db.commit)
    temp_user_example_dict['email'] = "newtestinguser@test.com"
    assert create_user_EP(test_client, **temp_user_example_dict).status_code == 403 

    temp_user_example_dict['email'] = "userexample@test.com"
    user_login_EP(test_client, temp_user_example_dict['email'], temp_user_example_dict['password'])

    assert test_client.get('/create_user').status_code == 403


def test_login_user(test_app):
    app, test_client = test_app

    temp_user_example_dict = user_example

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

    # test get
    assert test_client.get('/login').status_code == 200

    # authentication with wrong email
    assert user_login_EP(test_client, "wrongemail@test.com", temp_user_example_dict['password']).status_code == 401

    # authentication with correct email and wrong password
    assert user_login_EP(test_client, temp_user_example_dict['email'], "wrngpass").status_code == 401

    # authentication with wrong email syntax
    assert user_login_EP(test_client, "wrongemailsyntax", temp_user_example_dict['password']).status_code == 400

    # authentication with correct credentials
    assert user_login_EP(test_client, temp_user_example_dict['email'], temp_user_example_dict['password']).status_code == 200

    # double login
    assert user_login_EP(test_client, temp_user_example_dict['email'], temp_user_example_dict['password']).status_code == 200

    # creation of a new user when already logged in must fail
    temp_user_example_dict['email'] = 'newtestinguser2@test.com'
    assert create_user_EP(test_client, **temp_user_example_dict).status_code == 403


def test_logout_user(test_app):
    app, test_client = test_app

    temp_user_example_dict = user_example

    create_user_EP(test_client, **temp_user_example_dict)
    
    # --- UNIT TESTS --- nothing to be tested as unit

    # --- COMPONENT TESTS ---
    # logout without user logged
    result = test_client.get('/logout', follow_redirects=True)

    assert result.status_code == 401

    result = user_login_EP(test_client, temp_user_example_dict['email'], temp_user_example_dict['password'])

    assert result.status_code == 200

    # logout
    result = test_client.get('/logout', follow_redirects=True)

    assert result.status_code == 200


def test_unit_edit_user(test_app):

    app, test_client = test_app

    temp_user_example_dict = user_example
    
    # create a user
    create_user_EP(test_client, **temp_user_example_dict)

    #--- UNIT TESTS ---

    with app.app_context():

        # modify a user and check if it is modified
        
        getuser = db.session.query(User).filter(User.email == temp_user_example_dict['email']).first()
        
        getuser.phone = '4444444444'
        getuser.password = 'newpassw'
        db.session.commit()

        getuser = db.session.query(User).filter(User.email == temp_user_example_dict['email']).first()
        
        assert getuser is not None
        assert getuser.email == temp_user_example_dict['email']
        assert getuser.phone == '4444444444'
        assert getuser.firstname == temp_user_example_dict['firstname']
        assert getuser.lastname == temp_user_example_dict['lastname']
        assert getuser.password == "newpassw"
        assert getuser.dateofbirth == datetime.date(2000, 10, 5)
        

    #--- COMPONENT TESTS ---

def test_component_user_editing(test_app):

    app, test_client = test_app

    temp_user_example_dict = user_example

    # create a new user
    create_user_EP(test_client, **temp_user_example_dict)

    # test get without user logged
    assert test_client.get('/edit_user_informations').status_code == 401

    # test without user logged
    assert edit_user_EP(test_client, '4444444444', temp_user_example_dict['password'], 'passw').status_code == 401

    # login with a user
    user_login_EP(test_client, temp_user_example_dict['email'], temp_user_example_dict['password'])

    # test get with success
    assert test_client.get('/edit_user_informations').status_code == 200
    
    # try to edit the user with success
    assert edit_user_EP(test_client, '4444444444', temp_user_example_dict['password'], 'newpassw').status_code == 200

    # login with old password
    assert user_login_EP(test_client, temp_user_example_dict['email'], "passw").status_code == 401

    # login the user with the new password
    assert user_login_EP(test_client, temp_user_example_dict['email'], "newpassw").status_code == 200

    # try to edit an user with wrong password
    assert edit_user_EP(test_client, '4444444444', 'wrongp', 'newpassw').status_code == 401

    # try to send an invalid form (password too long)
    assert edit_user_EP(test_client, '4444444444', 'passwtoolong', 'newpassw').status_code == 400

def test_users_list(test_app):

    app, test_client = test_app

    temp_user_example_dict = user_example
    insert_admin(db, app)

    #assert test_client.get('/users').status_code == 401

    # login with a user
    user_login_EP(test_client, 'admin@admin.com', 'admin')

    assert test_client.get('/users').status_code == 200

    test_client.get('/logout', follow_redirects=True)

    assert create_user_EP(test_client, **temp_user_example_dict).status_code == 200

    user_login_EP(test_client, temp_user_example_dict['email'], temp_user_example_dict['password'])

    assert test_client.get('/users').status_code == 403




