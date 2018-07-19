from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine(
    'sqlite:///catalog.db', connect_args={'check_same_thread': False})
# Bind the engine to the metadata of the Base class so that thef
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


def get_categories():
    return session.query(Category).order_by(asc(Category.name))


def get_latest_items():
    return session.query(Item).order_by(Item.id.desc()).limit(5)


@app.route('/')
@app.route('/catalog')
def show_homepage():
    categories = get_categories()
    latest_items = get_latest_items()
    return render_template(
        'index.html', categories=categories, latest_items=latest_items)


# Create anti-forgery state token.
def create_state_token():
    return ''.join(
        random.choice(
            string.ascii_uppercase + string.digits) for x in xrange(32))


@app.route('/login')
def show_login():
    state = create_state_token()
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Validate state token.
def is_state_token_valid(state, state_from_url):
    return state == state_from_url


def make_json_response(message, http_code):
    response = make_response(json.dumps(message), http_code)
    response.headers['Content-Type'] = 'application/json'
    return response


def get_credentials_object(auth_code):
    oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
    oauth_flow.redirect_uri = 'postmessage'
    # Credentials object returned by Google.
    return oauth_flow.step2_exchange(auth_code)


# Upgrade the authorization code into a credentials object.
def upgrade_token_to_credentials(auth_code):
    try:
        credentials = get_credentials_object(auth_code)
    except FlowExchangeError:
        return False
    return credentials


def get_result_from_google_API(access_token):
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    return json.loads(h.request(url, 'GET')[1])


def is_right_user(token_user_id, gplus_id):
    return token_user_id == gplus_id


def get_user_info(access_token):
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': access_token, 'alt': 'json'}
    return requests.get(userinfo_url, params=params)


def store_data_in_session(access_token, gplus_id, data):
    # Store the access token in the session for later use.
    login_session['access_token'] = access_token
    login_session['gplus_id'] = gplus_id
    # Store user infos.
    login_session['username'] = data['name']
    login_session['email'] = data['email']


def create_user(login_session):
    new_user = User(username=login_session['username'], email=login_session[
                   'email'])
    session.add(new_user)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def get_user_ID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def show_login_message():
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    print "done!"
    return output


@app.route('/gconnect', methods=['POST'])
def gconnect():
    state = login_session['state']
    state_from_url = request.args.get('state')
    if not is_state_token_valid(state, state_from_url):
        return make_json_response('Invalid state parameter.', 401)

    # Obtain authorization code.
    auth_code = request.data
    credentials = upgrade_token_to_credentials(auth_code)
    if not credentials:
        return make_json_response(
            'Failed to upgrade the authorization code.', 401)

    # Check that the access token inside credentials is valid.
    access_token = credentials.access_token
    # Attempt get request.
    result = get_result_from_google_API(access_token)
    if result.get('error') is not None:
        return make_json_response(result.get('error'), 500)

    # Verify that the access token is used for the intended user.
    token_user_id = credentials.id_token['sub']
    gplus_id = result['user_id']
    if not is_right_user(token_user_id, gplus_id):
        return make_json_response(
            "Token's user ID doesn't match given user ID.", 401)

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        return make_json_response(
            "Token's client ID does not match app's.", 401)

    # Verify that the user is not already connected.
    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and token_user_id == stored_gplus_id:
        return make_json_response('Current user is already connected.', 200)

    # Store token and user's infos in login session.
    answer = get_user_info(access_token)
    data = answer.json()
    store_data_in_session(access_token, gplus_id, data)

    # Create a new user if it doesn't exist.
    user_id = get_user_ID(data["email"])
    if not user_id:
        user_id = create_user(login_session)
    login_session['user_id'] = user_id

    return show_login_message()


def empty_session():
    del login_session['access_token']
    del login_session['username']
    del login_session['email']
    del login_session['user_id']
    del login_session['gplus_id']


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        return make_json_response('Current user not connected.', 401)
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        empty_session()
        return redirect(url_for('show_homepage'))
    else:
        return make_json_response(
            'Failed to revoke token for given user.', 400)


@app.route('/item/new/', methods=['GET', 'POST'])
def new_item():
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        if request.form['name'] == "":
            flash("Name is needed to create a new item.")
            categories = get_categories()
            return render_template('new_item.html', categories=categories)
        else:
            item = Item(
                category_name=request.form['category'],
                name=request.form['name'],
                description=request.form['description'],
                creator_id=login_session['user_id'])
            session.add(item)
            session.commit()
            return redirect(url_for('show_homepage'))
    else:
        categories = get_categories()
        return render_template('new_item.html', categories=categories)


def get_item(item_name):
    try:
        item = session.query(
            Item).filter_by(name=item_name).one()
    except:
        return None
    return item


@app.route('/catalog/<string:item_name>/edit/', methods=['GET', 'POST'])
def edit_item(item_name):
    item = get_item(item_name)
    if not item:
        return make_json_response("This item doesn't exist", 404)
    if 'username' not in login_session:
        return redirect('/login')
    if item.creator_id != login_session['user_id']:
        if item.creator_id != login_session['user_id']:
            flash("You are not authorized to edit this item.")
            categories = get_categories()
            return render_template(
                'edit_item.html', item=item, categories=categories)
    if request.method == 'POST':
        if request.form['name'] == "":
            return redirect(url_for('show_homepage'))

        item.name = request.form['name']
        item.description = request.form['description']
        item.category_name = request.form['category']
        session.commit()
        return redirect(url_for('show_homepage'))
    else:
        categories = get_categories()
        return render_template(
            'edit_item.html', item=item, categories=categories)


@app.route('/catalog/<string:item_name>/delete/', methods=['GET', 'POST'])
def delete_item(item_name):
    item = get_item(item_name)
    if not item:
        return make_json_response("This item doesn't exist", 404)
    if 'username' not in login_session:
        return redirect('/login')
    if item.creator_id != login_session['user_id']:
        flash("You are not authorized to delete this item.")
        return render_template('delete_item.html', item=item)
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('show_homepage'))
    else:
        return render_template('delete_item.html', item=item)


def get_category_items(category_name):
    return (session.query(Item).filter(Item.category_name == category_name))


@app.route('/catalog/<string:category_name>/items')
def show_category_items(category_name):
    categories = get_categories()
    items = get_category_items(category_name)
    return render_template(
        'category_items.html',
        categories=categories,
        items=items,
        category_name=category_name)


@app.route('/catalog/<string:category_name>/<string:item_name>')
def show_item_infos(category_name, item_name):
    item = get_item(item_name)
    if not item:
        return make_json_response("This item doesn't exist", 404)
    return render_template('item_infos.html', item=item)


@app.route('/catalog/<string:item_name>/JSON')
def item_JSON(item_name):
    item = get_item(item_name)
    if not item:
        return make_json_response("This item doesn't exist", 404)
    return jsonify(item=item.serialize)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
