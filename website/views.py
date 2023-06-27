# defines that this page is the blueprint of the website.
from flask import Blueprint, render_template, request, flash, current_app, session, redirect, url_for
from flask_login import login_required, logout_user, current_user
from sqlalchemy import func

from .models import Products, Message, User
import os
import secrets
from . import db
import json

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
    return render_template("searchResult.html", user=current_user, products=products)


@views.route('/addProduct', methods=['GET', 'POST'])
def addProduct():
    if request.method == 'POST':
        category = request.form.get('category')
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        stock = request.form.get('stock')
        discount = request.form.get('discount')

        photo1 = saveImage(request.files.get('image1'))
        photo2 = saveImage(request.files.get('image2'))
        photo3 = saveImage(request.files.get('image3'))

        print(category, name, description, price, photo1)

        new_product = Products(category=category, name=name, description=description, price=price, stock=stock,
                               image1=photo1, image2=photo2, image3=photo3, discount=discount,
                               user_id=current_user.id)

        db.session.add(new_product)
        db.session.commit()
        flash('Product posted!', category='success')
        products = Products.query.filter_by(user_id=current_user.id)
        return render_template("home_seller.html", user=current_user, products=products)

    return render_template("addProduct.html", user=current_user)


@views.route('/dogs')
def electronics():
    products = Products.query.filter_by(category="dogs")
    print(products)
    return render_template("home_buyer1.html", products=products, user=current_user)


@views.route('/cats')
def food():
    products = Products.query.filter_by(category="cats")
    print(products)
    return render_template("home_buyer1.html", products=products, user=current_user)


@views.route('/birds')
def shoes():
    products = Products.query.filter_by(category="birds")
    print(products)
    return render_template("home_buyer1.html", products=products, user=current_user)


@views.route('/smallAnimals')
def clothes():
    products = Products.query.filter_by(category="smallAnimals")
    print(products)
    return render_template("home_buyer1.html", products=products, user=current_user)


@views.route('/editProduct/<int:id>', methods=['GET', 'POST'])
def editProduct(id):
    result = Products.query.get_or_404(id)
    if request.method == "POST":
        result.name = request.form.get('name')
        result.description = request.form.get('description')
        result.price = request.form.get('price')
        result.stock = request.form.get('stock')
        result.photo = request.files.get('image1')
        result.offers = result.offers + "," + str(result.discount)
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
def home_seller():
    products = Products.query.filter_by(user_id=current_user.id)
    buyers = User.query.filter_by(userType='buyer').all()
    return render_template("home_seller.html", user=current_user, products=products, buyers=buyers)


@views.route('/buyer')
def home_buyer():
    page = request.args.get('page', 1, type=int)
    products = Products.query.filter(Products.stock > 0).paginate(page=page, per_page=4)

    if current_user.is_authenticated:
        messages = Message.query.filter(
            (Message.sender_id == current_user.id) |
            (Message.recipient_id == current_user.id)
        ).order_by(Message.timestamp.desc()).limit(10).all()
    else:
        messages = None

    return render_template("home_buyer1.html", user=current_user, products=products, messages=messages)


@views.route('/product/<int:id>')
def detailsPage(id):
    product = Products.query.get_or_404(id)
    return render_template("details.html", product=product, user=current_user)


@views.route('/sellers')
@login_required
def sellers_list():
    sellers = User.query.filter_by(userType="seller").all()
    return render_template('sellers.html', user=current_user, sellers=sellers)


@views.route('/buyers')
@login_required
def buyers_list():
    buyers = User.query.filter_by(userType="buyer").all()
    return render_template('buyers.html', user=current_user, buyers=buyers)


@views.route('/chat/<int:seller_id>', methods=['GET', 'POST'])
@login_required
def chat(seller_id):
    seller = User.query.get_or_404(seller_id)

    if request.method == 'POST':
        recipient_id = seller_id
        content = request.form.get('content')

        if content:
            new_message = Message(
                sender_id=current_user.id,
                recipient_id=recipient_id,
                content=content,
                timestamp=func.now()
            )
            db.session.add(new_message)
            db.session.commit()
            flash('Message sent!', category='success')

    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == seller_id)) |
        ((Message.sender_id == seller_id) & (Message.recipient_id == current_user.id))
    ).order_by(Message.timestamp.asc()).all()

    return render_template('chat.html', buyer=seller, messages=messages, user=current_user)


@views.route('/messages/<int:buyer_id>')
@login_required
def messages(buyer_id):
    buyer = User.query.get(buyer_id)
    if not buyer:
        flash('Buyer not found.', category='error')
        return redirect(url_for('views.home'))

    # Fetch messages between current user (seller) and the buyer
    messages = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user.id, Message.recipient_id == buyer_id),
            db.and_(Message.sender_id == buyer_id, Message.recipient_id == current_user.id)
        )
    ).order_by(Message.timestamp.asc()).all()

    return render_template('messages.html', buyer=buyer, messages=messages, user=current_user)


@views.route('/send_message/<int:buyer_id>', methods=['POST'])
@login_required
def send_message(buyer_id):
    buyer = User.query.get(buyer_id)
    if not buyer:
        flash('Buyer not found.', category='error')
        return redirect(url_for('views.home_seller'))

    message_content = request.form.get('message')
    if not message_content:
        flash('Message content cannot be empty.', category='error')
        return redirect(url_for('views.messages', buyer_id=buyer_id))

    new_message = Message(sender_id=current_user.id, recipient_id=buyer_id, content=message_content)
    db.session.add(new_message)
    db.session.commit()

    flash('Message sent successfully.', category='success')
    return redirect(url_for('views.messages', buyer_id=buyer_id))


@views.route('/sort/price')
def sort_by_price():
    products = Products.query.order_by(Products.price).all()
    return render_template("home_buyer1.html", user=current_user, products=products)


@views.route('/sort/name')
def sort_by_name():
    products = Products.query.order_by(Products.name).all()
    return render_template("home_buyer1.html", user=current_user, products=products)


def mergeDictionary(dict01, dict02):
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

    for key, product in session['shopping_cart'].items():
        total += float(product['price']) * int(product['quantity'])
    print(total)

    return render_template('cart.html', total=total, user=current_user)


@views.route('/deleteitem/<int:id>')
def deleteitem(id):
    if 'shopping_cart' not in session or len(session['shopping_cart']) <= 0:
        return redirect(url_for('views.home_buyer'))
    try:
        session.modified = True
        for key, item in session['shopping_cart'].items():
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


@views.route('/updatecart/<int:id>', methods=['POST'])
def updateCart(id):
    if 'shopping_cart' not in session or len(session['shopping_cart']) <= 0:
        return redirect(url_for('views.home_buyer'))
    if request.method == "POST":
        quantity = int(request.form.get('quantity'))
        try:
            session.modified = True
            for key, item in session['shopping_cart'].items():
                if int(key) == id:
                    item['quantity'] = quantity
                    print(item['quantity'])
                    flash('Your cart has been updated!')
                    return redirect(url_for('views.getCart'))
        except Exception as e:
            print(e)
            return redirect(url_for('views.getCart'))
