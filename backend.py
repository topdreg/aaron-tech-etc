#! /usr/bin/env python3

from flask import Flask, render_template
from flask import request, redirect, url_for, jsonify, flash
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, Items, User

# Security imports.
from flask import session as login_session
import random
import string
import os
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# JSON endpoints listed below.


# JSON endpoint for a list of all categories.

@app.route('/catalog/JSON')
def showCategoriesJSON():
    categories = session.query(Categories).all()
    return jsonify(Categories=[i.serialize for i in categories])

# JSON endpoint for a single category.


@app.route('/catalog/<int:category_id>/JSON')
def showCategoryJSON(category_id):
    category = session.query(Categories).filter_by(id=category_id).first()
    return jsonify(category.serialize)

# JSON endpoint for a list of all items.


@app.route('/catalog/<int:category_id>/items/JSON')
def showItemsJSON(category_id):
    items = session.query(Items).filter_by(category_id=category_id).all()
    return jsonify(Items=[i.serialize for i in items])

# JSON endpoint for a single item.


@app.route('/catalog/items/<int:item_id>/JSON')
def showItemJSON(item_id):
    item = session.query(Items).filter_by(id=item_id).first()
    return jsonify(item.serialize)

# Create user functionality.


def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


# Application endpoints listed below.

@app.route('/')
@app.route('/catalog')
def showCatalog():
    # Generate random string for OAuth.
    state = ''.join(
        random.choice(
            string.ascii_uppercase +
            string.digits) for x in range(32))
    login_session['state'] = state
    print(login_session['state'])

    # Proceed with loading the page.
    categories = session.query(Categories)
    latestItems = session.query(Items).order_by(
        desc('last_updated')).limit(15).all()
    if 'username' not in login_session:
        return render_template(
            "main.html",
            categories=categories,
            latestItems=latestItems,
            STATE=state)
    else:
        return render_template(
            "mainLogIn.html",
            categories=categories,
            latestItems=latestItems)


# sqlalchemy's filter_by function supposedly has sql injection protection.

@app.route('/catalog/<string:category_name>')
def showCategory(category_name):
    categories = session.query(Categories)
    category = session.query(Categories).filter_by(name=category_name).first()
    items = session.query(Items).filter_by(category_id=category.id)
    creator = getUserInfo(category.user_id)
    if 'username' not in login_session or creator.id != login_session['user_id']:
        return render_template(
            "showCategory.html",
            items=items,
            category=category,
            categories=categories)
    else:
        return render_template(
            "showCategoryLogIn.html",
            items=items,
            category=category,
            categories=categories)


@app.route('/catalog/addCategory', methods=['GET', 'POST'])
def addCategory():
    if 'username' not in login_session:
        return redirect('/')
    if request.method == 'POST':
        newCategory = Categories(name=request.form['name'],
                                 user_id=login_session['user_id'])
        session.add(newCategory)
        session.commit()
        flash("Category successfully added.")
        return redirect(url_for('showCatalog'))
    else:
        categories = session.query(Categories)
        return render_template("addCategory.html", categories=categories)


@app.route('/catalog/<string:category_name>/editCategory', methods=['GET', 'POST'])
def editCategory(category_name):
    category = session.query(Categories).filter_by(name=category_name).one()
    creator = getUserInfo(category.user_id)
    if 'username' not in login_session or creator.id != login_session['user_id']:
        flash("You are not the user who created this category.")
        return redirect(url_for('showCategory', category_name=category_name))
    if request.method == 'POST':
        category.name = request.form['name']
        session.add(category)
        session.commit()
        flash("Category successfully edited.")
        return redirect(url_for('showCategory', category_name=category.name))
    else:
        categories = session.query(Categories)
        return render_template(
            "editCategory.html",
            category=category,
            categories=categories)


@app.route('/catalog/<string:category_name>/deleteCategory', methods=['GET', 'POST'])
def deleteCategory(category_name):
    category = session.query(Categories).filter_by(name=category_name).first()
    creator = getUserInfo(category.user_id)
    if 'username' not in login_session or creator.id != login_session['user_id']:
        flash("You are not the user who created this category.")
        return redirect(url_for('showCategory', category_name=category_name))
    if request.method == 'POST':
        items = session.query(Items).filter_by(category_id=category.id)
        session.delete(category)
        for item in items:
            session.delete(item)
        flash("Category successfully deleted.")
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        categories = session.query(Categories)
        return render_template(
            "deleteCategory.html",
            category=category,
            categories=categories)


@app.route('/catalog/<string:category_name>/<string:item_name>')
def showItem(item_name, category_name):
    item = session.query(Items).filter_by(name=item_name).first()
    categories = session.query(Categories)
    category = session.query(Categories).filter_by(name=category_name).one()
    if 'username' not in login_session:
        return render_template(
            "showItem.html",
            item=item,
            categories=categories,
            category=category)
    else:
        return render_template(
            "showItemLogIn.html",
            item=item,
            categories=categories,
            category=category)


@app.route('/catalog/<string:category_name>/addItem', methods=['GET', 'POST'])
def addItem(category_name):
    if 'username' not in login_session:
        return redirect(url_for('showCategory', category_name=category_name))
    category = session.query(Categories).filter_by(name=category_name).one()
    if request.method == 'POST':
        newItem = Items(
            name=request.form['name'],
            short_description=request.form['short_description'],
            description=request.form['description'],
            price=request.form['price'],
            image=request.form['image'],
            user_id=login_session['user_id'],
            category_id=category.id)
        session.add(newItem)
        session.commit()
        flash("Item successfully added.")
        return redirect(url_for('showCategory', category_name=category.name))
    else:
        categories = session.query(Categories)
        return render_template(
            "addItem.html",
            category=category,
            categories=categories)


@app.route('/catalog/<string:category_name>/<string:item_name>/edit',
           methods=['GET', 'POST'])
def editItem(item_name, category_name):
    item = session.query(Items).filter_by(name=item_name).one()
    creator = getUserInfo(item.user_id)
    if 'username' not in login_session or creator.id != login_session['user_id']:
        flash("You are not the user who created this item.")
        return redirect(
            url_for(
                'showItem',
                item_name=item_name,
                category_name=category_name))
    category = session.query(Categories).filter_by(name=category_name).one()
    if request.method == 'POST':
        item.name = request.form['name']
        item.short_description = request.form['short_description']
        item.description = request.form['description']
        item.price = request.form['price']
        item.image = request.form['image']
        session.add(item)
        flash("Item successfully edited.")
        session.commit()
        return redirect(
            url_for(
                'showItem',
                item_name=item.name,
                category_name=category.name))
    else:
        return render_template("editItem.html", item=item, category=category)


@app.route('/catalog/<string:category_name>/<string:item_name>/delete',
           methods=['GET', 'POST'])
def deleteItem(item_name, category_name):
    item = session.query(Items).filter_by(name=item_name).one()
    creator = getUserInfo(item.user_id)
    if 'username' not in login_session or creator.id != login_session['user_id']:
        flash("You are not the user who created this item.")
        return redirect(
            url_for(
                'showItem',
                item_name=item_name,
                category_name=category_name))
    category = session.query(Categories).filter_by(name=category_name).one()
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        flash("Item successfully deleted.")
        return redirect(url_for('showCategory', category_name=category.name))
    else:
        categories = session.query(Categories)
        return render_template(
            "deleteItem.html",
            item=item,
            category=category,
            categories=categories)


# Security endpoints.
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token.
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code.
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object.
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' %
        access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['email'] = data['email']

    # See if user exists, if it doesn't make a new one.
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    return "Login successful."


@app.route('/gdisconnect')
def gdisconnect():
    del login_session['access_token']
    del login_session['gplus_id']
    del login_session['username']
    return redirect(url_for('showCatalog'))

# HTML endpoints listed below.

app.secret_key = 'super secret key'

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
