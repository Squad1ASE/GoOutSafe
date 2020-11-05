from monolith.database import db, User, Restaurant, WorkingDay, Table, Dish
from monolith.classes.tests.conftest import test_app, create_user_EP, user_login_EP, create_restaurant_EP
import json
from sqlalchemy import exc

def test_component_home(test_app):
    app, test_client = test_app
    
    assert test_client.get('/', follow_redirects=True).status_code == 200
    # normal user
    assert create_user_EP(test_client).status_code == 200
    assert user_login_EP(test_client).status_code == 200
    assert test_client.get('/', follow_redirects=True).status_code == 200
    # admin
    assert test_client.get('/logout', follow_redirects=True)
    assert create_user_EP(test_client, email='admin@admin.com', password='admin',role='admin').status_code == 200
    assert user_login_EP(test_client, 'admin@admin.com', 'admin').status_code == 200
    assert test_client.get('/', follow_redirects=True).status_code == 200
    # ha
    assert test_client.get('/logout', follow_redirects=True)
    assert create_user_EP(test_client, email='ha@ha.com', password='ha',role='ha').status_code == 200
    assert user_login_EP(test_client, 'ha@ha.com', 'ha').status_code == 200
    assert test_client.get('/', follow_redirects=True).status_code == 200
    # owner
    assert test_client.get('/logout', follow_redirects=True)
    assert create_user_EP(test_client, email='owner@owner.com', password='owner',role='owner').status_code == 200
    assert user_login_EP(test_client, 'owner@owner.com', 'owner').status_code == 200
    assert test_client.get('/', follow_redirects=True).status_code == 200
    assert create_restaurant_EP(test_client).status_code == 200
    assert test_client.get('/', follow_redirects=True).status_code == 200
    '''
    # no-role
    assert test_client.get('/logout', follow_redirects=True)
    assert create_user_EP(test_client, email='nr@nr.com', password='nr',role='norole').status_code == 500
    assert user_login_EP(test_client, 'nr@nr.com', 'nr').status_code == 200
    assert test_client.get('/', follow_redirects=True).status_code == 404
    '''