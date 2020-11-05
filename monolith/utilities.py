from monolith.database import Restaurant, WorkingDay
import datetime


# --- UTILITIES RESTAURANT  ---
restaurant_example = [
    { 
        'name':'Restaurant 1', 'lat':43.7216621, 'lon':10.4083723, 'phone':'111111', 
        'cuisine_type':[Restaurant.CUISINE_TYPES(1),Restaurant.CUISINE_TYPES(6)], 'prec_measures':'leggeX', 'avg_time_of_stay':15,
        'tables-0-table_name':'res1red', 'tables-0-capacity':2, 
        'dishes-0-dish_name':'pizza', 'dishes-0-price':4, 'dishes-0-ingredients':'pomodoro, mozzarella',
        'dishes-1-dish_name':'pasta agli scampi', 'dishes-1-price':4, 'dishes-1-ingredients':'pasta, scampi',
        'workingdays-0-day': WorkingDay.WEEK_DAYS(1), 'workingdays-0-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-1-day': WorkingDay.WEEK_DAYS(2), 'workingdays-1-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-2-day': WorkingDay.WEEK_DAYS(3), 'workingdays-2-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-3-day': WorkingDay.WEEK_DAYS(4), 'workingdays-3-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-4-day': WorkingDay.WEEK_DAYS(5), 'workingdays-4-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-5-day': WorkingDay.WEEK_DAYS(6), 'workingdays-5-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-6-day': WorkingDay.WEEK_DAYS(7), 'workingdays-6-work_shifts':"('12:00','15:00'),('19:00','23:00')"
    },
    { 
        'name':'Restaurant 2', 'lat':43.7176394, 'lon':10.4032292, 'phone':'222222', 
        'cuisine_type':[Restaurant.CUISINE_TYPES(1),Restaurant.CUISINE_TYPES(3)], 'prec_measures':'leggeX', 'avg_time_of_stay':25,
        'tables-0-table_name':'res2red', 'tables-0-capacity':6, 
        'tables-1-table_name':'res2blue', 'tables-1-capacity':4, 
        'dishes-0-dish_name':'pasta al pesto', 'dishes-0-price':4, 'dishes-0-ingredients':'pasta, pesto, basilico',
        'dishes-1-dish_name':'burrito', 'dishes-1-price':3, 'dishes-1-ingredients':'carne,fagioli',
        'workingdays-0-day': WorkingDay.WEEK_DAYS(1), 'workingdays-0-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-1-day': WorkingDay.WEEK_DAYS(2), 'workingdays-1-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-2-day': WorkingDay.WEEK_DAYS(3), 'workingdays-2-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-3-day': WorkingDay.WEEK_DAYS(4), 'workingdays-3-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-4-day': WorkingDay.WEEK_DAYS(5), 'workingdays-4-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-5-day': WorkingDay.WEEK_DAYS(6), 'workingdays-5-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-6-day': WorkingDay.WEEK_DAYS(7), 'workingdays-6-work_shifts':"('12:00','15:00'),('19:00','23:00')"
    },
    { 
        'name':'Restaurant 3', 'lat':43.7176589, 'lon':10.4015256, 'phone':'333333', 
        'cuisine_type':[Restaurant.CUISINE_TYPES(2)], 'prec_measures':'leggeX', 'avg_time_of_stay':40,
        'tables-0-table_name':'res3green', 'tables-0-capacity':4, 
        'tables-1-table_name':'res3red', 'tables-1-capacity':4, 
        'tables-2-table_name':'res3blue', 'tables-2-capacity':6, 
        'tables-3-table_name':'res3yellow', 'tables-3-capacity':10, 
        'dishes-0-dish_name':'riso', 'dishes-0-price':4, 'dishes-0-ingredients':'funghi',
        'workingdays-0-day': WorkingDay.WEEK_DAYS(2), 'workingdays-0-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-1-day': WorkingDay.WEEK_DAYS(3), 'workingdays-1-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-2-day': WorkingDay.WEEK_DAYS(4), 'workingdays-2-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-3-day': WorkingDay.WEEK_DAYS(5), 'workingdays-3-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-4-day': WorkingDay.WEEK_DAYS(6), 'workingdays-4-work_shifts':"('12:00','15:00'),('19:00','23:00')",
        'workingdays-5-day': WorkingDay.WEEK_DAYS(7), 'workingdays-5-work_shifts':"('12:00','15:00'),('19:00','23:00')"
    }
]

# recall: to call this function you must be logged in
def create_restaurant_EP(test_client, data_dict=restaurant_example[0]):
    return test_client.post('/create_restaurant', data=data_dict, follow_redirects=True)


# --- UTILITIES USER ---
# customers
customers_example = [
    dict(
        email='userexample1@test.com',
        phone='39111111',
        firstname='firstname_test1',
        lastname='lastname_test1',
        password='passw1',
        dateofbirth='05/10/2001'
    ),
    dict(
        email='userexample2@test.com',
        phone='39222222',
        firstname='firstname_test2',
        lastname='lastname_test2',
        password='passw2',
        dateofbirth='05/10/2002'
    ),
    dict(
        email='userexample3@test.com',
        phone='39333333',
        firstname='firstname_test3',
        lastname='lastname_test3',
        password='passw3',
        dateofbirth='05/10/2003'
    )
]       
# health authority
health_authority_example = dict(
    email='healthauthority@ha.com',
    phone='66666',
    firstname='Ha',
    lastname='Ha',
    password='ha',
    dateofbirth='05/10/2000'
)
# admin 
admin_example = dict(
    email='badmin@admin.com',
    phone='666',
    firstname='badministrator_fn',
    lastname='badministrator_ln',
    password='badminpassw',
    dateofbirth='05/10/2001'
)

def create_user_EP(
        test_client, email=customers_example[0]['email'], phone=customers_example[0]['phone'],firstname=customers_example[0]['firstname'], 
        lastname=customers_example[0]['lastname'], password=customers_example[0]['password'], dateofbirth=customers_example[0]['dateofbirth']
    ):
    data = dict(
        email=email,
        phone=phone,
        firstname=firstname,
        lastname=lastname,
        password=password,
        dateofbirth=dateofbirth
    )
    return test_client.post('/create_user', data=data, follow_redirects=True)


def user_login_EP(test_client, email=customers_example[0]['email'], password=customers_example[0]['password']):
    data = dict(
        email=email,
        password=password
    )
    return test_client.post('/login', data=data, follow_redirects=True)

def user_logout_EP(test_client):
    return test_client.get('/logout', follow_redirects=True)

def edit_user_EP(
    test_client, phone, old_passw, new_passw
):
    data = dict(
        phone=phone,
        old_password=old_passw,
        new_password=new_passw
    )
    return test_client.post('/edit_user_informations', data=data, follow_redirects=True)

