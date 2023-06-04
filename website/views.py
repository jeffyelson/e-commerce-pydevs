# defines that this page is the blueprint of the website.
from flask import Blueprint, render_template, request, flash, current_app,session,redirect,url_for
from flask_login import login_required, logout_user, current_user
from .models import Products
import os
import secrets
from . import db

views = Blueprint('views', __name__)


def saveImage(photo):
    hashPhoto = secrets.token_urlsafe(10)
    _, file_extension = os.path.splitext(photo.filename)
    photo_name = hashPhoto + file_extension
    file_path = os.path.join(current_app.root_path, 'static/img', photo_name)
    photo.save(file_path)
    return photo_name


@views.route('/')
def home():
    products = Products.query.all()
    return render_template("landingPage.html", user=current_user, products=products)


@views.route('/result')
def searchResult():
    query = request.args.get('q')
    products = Products.query.msearch(query, fields=['name', 'description'])
    return render_template("searchResult.html", products=products)


@views.route('/addProduct', methods=['GET', 'POST'])
def addProduct():
    if request.method == 'POST':
        category = request.form.get('category')
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        stock = request.form.get('stock')
        discount = request.form.get('discount')
        photo = saveImage(request.files.get('image'))

        print(category, name, description, price, photo)

        new_product = Products(category=category, name=name, description=description, price=price, stock=stock,
                               image=photo, discount = discount,
                               user_id=current_user.id)
        db.session.add(new_product)
        db.session.commit()
        flash('Product posted!', category='success')
        products = Products.query.filter_by(user_id=current_user.id)
        return render_template("home_seller.html", user=current_user, products=products)

    return render_template("addProduct.html", user=current_user)


@views.route('/electronics')
def electronics():
    products = Products.query.filter_by(category="electronics")
    print(products)
    return render_template("home_buyer.html", products=products, user=current_user)


@views.route('/food')
def food():
    products = Products.query.filter_by(category="food")
    print(products)
    return render_template("home_buyer.html", products=products, user=current_user)


@views.route('/shoes')
def shoes():
    products = Products.query.filter_by(category="shoes")
    print(products)
    return render_template("home_buyer.html", products=products, user=current_user)


@views.route('/clothes')
def clothes():
    products = Products.query.filter_by(category="clothing")
    print(products)
    return render_template("home_buyer.html", products=products, user=current_user)


@views.route('/editProduct/<int:id>', methods=['GET', 'POST'])
def editProduct(id):
    result = Products.query.get_or_404(id)
    if request.method == "POST":
        result.name = request.form.get('name')
        result.description = request.form.get('description')
        result.price = request.form.get('price')
        result.stock = request.form.get('stock')
        result.photo = request.files.get('image')
        result.discount = request.form.get('discount')
        db.session.commit()
        flash(f'Your product has been updated', 'success')
        products = Products.query.all()
        return render_template("home_seller.html", user=current_user, products=products)

    return render_template("editProduct.html", user=current_user, result=result)


@views.route('/deleteProduct/<int:id>', methods=["POST"])
def deleteProduct(id):
    product = Products.query.get_or_404(id)
    if request.method == "POST":
        db.session.delete(product)
        db.session.commit()
        flash(f'The product {product.name} was deleted', 'success')
        products = Products.query.all()
        return render_template("home_seller.html", user=current_user, products=products)


@views.route('/seller', methods=['GET', 'POST'])
@login_required
def home_seller():
    products = Products.query.filter_by(user_id=current_user.id)
    return render_template("home_seller.html", user=current_user, products=products)


@views.route('/buyer')
def home_buyer():
    products = Products.query.all()
    return render_template("home_buyer.html", user=current_user, products=products)


@views.route('/sort/price')
def sort_by_price():
    products = Products.query.order_by(Products.price).all()
    return render_template("home_buyer.html", user=current_user, products=products)


@views.route('/sort/name')
def sort_by_name():
    products = Products.query.order_by(Products.name).all()
    return render_template("home_buyer.html", user=current_user, products=products)


def mergeDictionary(dict01,dict02):
    if isinstance(dict01, list) and isinstance(dict02, list):
        return dict01 + dict02
    if isinstance(dict01, dict) and isinstance(dict02, dict):
        return dict(list(dict01.items()) + list(dict02.items()))

@views.route('/cart', methods=['POST'])
def addToCart():
    try:
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity'))
        product = Products.query.filter_by(id=product_id).first()
        print(session)

        if request.method == "POST":
            dictItems = {product_id: {'name': product.name, 'price': float(product.price),
                                      'quantity': quantity, 'image': product.image}}
            if 'shopping_cart' in session:
                print(session['shopping_cart'])
                if product_id in session['shopping_cart']:
                    for key, item in session['shopping_cart'].items():
                        if int(key) == int(product_id):
                            session.modified = True
                            item['quantity'] += 1
                else:
                    session['shopping_cart'] = mergeDictionary(session['shopping_cart'], dictItems)
                    return redirect(request.referrer)
            else:
                session['shopping_cart'] = dictItems
                return redirect(request.referrer)
    except Exception as e:
        print(e)
    finally:
        return redirect(request.referrer)

@views.route('/cart')
def getCart():
    if 'shopping_cart' not in session or len(session['shopping_cart']) <= 0:
        return redirect(url_for('views.home_buyer'))
    total = 0

    for key,product in session['shopping_cart'].items():
        total += float(product['price']) * int(product['quantity'])
    print(total)

    return render_template('cart.html',total=total,user=current_user)

@views.route('/deleteitem/<int:id>')
def deleteitem(id):
    if 'shopping_cart' not in session or len(session['shopping_cart']) <= 0:
        return redirect(url_for('views.home_buyer'))
    try:
        session.modified = True
        for key , item in session['shopping_cart'].items():
            if int(key) == id:
                session['shopping_cart'].pop(key, None)
                return redirect(url_for('views.getCart'))
    except Exception as e:
        print(e)
        return redirect(url_for('views.getCart'))


@views.route('/clearcart')
def clearcart():
    try:
        session.pop('shopping_cart', None)
        return redirect(url_for('views.home_buyer'))
    except Exception as e:
        print(e)