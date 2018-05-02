from flask import Flask, render_template, request, redirect, url_for, jsonify
from sqlalchemy import create_engine, asc, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Categories, Items

app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine 

DBSession = sessionmaker(bind=engine) 
session = DBSession() 

# HTML endpoints listed below. 

@app.route('/') 
@app.route('/catalog') 
def showCatalog(): 
    categories = session.query(Categories)
    return render_template("main.html", categories = categories)

@app.route('/catalog/<category_name>') 
def showCategory(category_name): 
    categories = session.query(Categories)
    category = session.query(Categories).filter_by(name=category_name).first()
    items = session.query(Items).filter_by(category_id=category.id)
    return render_template("showCategory.html", items = items, category = category, categories = categories)

@app.route('/catalog/addCategory', methods = ['GET', 'POST'])
def addCategory(): 
    if request.method == 'POST': 
        newCategory = Categories(name=request.form['name'])
        session.add(newCategory)
        session.commit()
        return redirect(url_for('showCatalog'))
    else:
        return render_template("addCategory.html")

@app.route('/catalog/<category_name>/editCategory', methods = ['GET', 'POST'])
def editCategory(category_name): 
    return "Edit a category here"; 

@app.route('/catalog/<category_name>/deleteCategory', methods = ['GET', 'POST'])
def deleteCategory(category_name): 
    return "Delete a category";

@app.route('/catalog/<category_name>/addItem', methods = ['GET', 'POST'])
def addItem(category_name): 
    category = session.query(Categories).filter_by(name=category_name).one() 
    if request.method == 'POST': 
        newItem = Items(name=request.form['name'], description=request.form['description'],
        price = request.form['price'], image= request.form['image'], category_id=category.id)
        session.add(newItem) 
        session.commit()
        return redirect(url_for('showCategory', category_name = category.name))
    else: 
        return render_template("addItem.html", category = category) 

@app.route('/catalog/<category_name>/<item_name>/edit', methods = ['GET', 'POST'])
def editItem(item_name, category_name): 
    category = session.query(Categories).filter_by(name=category_name).one() 
    item = session.query(Items).filter_by(name=item_name).one()
    if request.method == 'POST': 
        item.name = request.form['name'] 
        item.description = request.form['description']
        item.price = request.form['price']
        item.image = request.form['image']
        session.add(item)
        session.commit() 
        return redirect(url_for('showCategory', category_name = category.name))
    else: 
        return render_template("editItem.html", item = item, category = category)

@app.route('/catalog/<category_name>/<item_name>/delete', methods = ['GET', 'POST'])
def deleteItem(item_name, category_name): 
    item = session.query(Items).filter_by(name=item_name).first() 
    category = session.query(Categories).filter_by(name=category_name).one()
    if request.method == 'POST': 
        session.delete(item)
        session.commit()
        return redirect(url_for('showCategory', category_name = category.name))
    else:
        return render_template("deleteItem.html", item = item, category = category) 


if __name__ == '__main__': 
    app.secret_key = 'super_secret_key' 
    app.debug = True
    app.run(host= '0.0.0.0', port = 8000) 
