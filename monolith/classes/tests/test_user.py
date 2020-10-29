import unittest
from monolith.database import db, User
from monolith.classes.tests.conftest import test_app
import datetime

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
        getuser = db.session.query(User).filter(User.email == 'notexistinguser@test.com').first()
        assert getuser is None

    # --- COMPONENTS TESTS ---
    data_dict = dict(
        email='myemail_test@test.com',
        firstname='myfirstname_test',
        lastname='mylastname_test',
        password='passw',
        dateofbirth='10/10/2000')

    result = test_client.post('/create_user', data=data_dict, follow_redirects=True)
           
    assert result.status_code == 200

    # new user creation must fails

    data_dict = dict(
        email='myemail_test@test.com',
        firstname='myfirstname_test',
        lastname='mylastname_test',
        password='passw',
        dateofbirth='10/10/2000')

    result = test_client.post('/create_user', data=data_dict, follow_redirects=True)

    assert result.status_code == 403