import pytest
from monolith.database import db, User
from monolith.app import create_app
import tempfile
import os
import datetime

@pytest.fixture
def test_app():
    app = create_app()

    app.config['WTF_CSRF_ENABLED'] = False  #this has been disabled to allows testing of forms
    temp_db, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+app.config['DATABASE']
    
    db.create_all(app=app)
    db.init_app(app=app)

    with app.app_context():
        q = db.session.query(User).filter(User.email == 'healthauthority@ha.com')
        user = q.first()
        if user is None:

            # test for a user defined in database.db
            example = User()
            example.email = 'healthauthority@ha.com'
            example.firstname = 'Ha'
            example.lastname = 'Ha'
            example.set_password('ha')
            example.dateofbirth = datetime.date(2020, 10, 5)            
            example.is_admin = False
            db.session.add(example)
            db.session.commit()

    yield app, app.test_client()

    os.close(temp_db)