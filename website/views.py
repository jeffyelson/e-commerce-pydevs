# defines that this page is the blueprint of the website.
from flask import Blueprint, render_template, request, flash, current_app, session, redirect, url_for
from flask_login import login_required, logout_user, current_user
from sqlalchemy import func, desc
from datetime import datetime, date
from decimal import Decimal
from math import ceil

from .models import Products, Message, User, OfferCodes, UserDetails, OrderDetails
import os
import secrets
from . import db
import json
import numpy as np

views = Blueprint('views', __name__)


def saveImage(photo):
    hashPhoto = secrets.token_urlsafe(10)
    _, file_extension = os.path.splitext(photo.filename)
    photo_name = hashPhoto + file_extension
    file_path = os.path.join(current_app.root_path, 'static/img', photo_name)
    photo.save(file_path)
    return photo_name


def calDiscount(products):
    discount_percentages = {}
    for product in products:
        discount_code = product.discount  # Get the discount code for the current product

        if discount_code:
            offer = OfferCodes.query.filter_by(discount_code=discount_code).first()

            if offer and offer.validity > date.today():
                discount_percentages[product.id] = offer.discount_percentage
            else:
                discount_percentages[product.id] = 0
        else:
            discount_percentages[product.id] = 0
    return discount_percentages


@views.route('/')
def home():
    products = Products.query.order_by(desc(Products.is_sponsored)).all()
    discount_percentages = calDiscount(products)
    return render_template("landingPage.html", user=current_user, products=products,
                           discount_percentages=discount_percentages)


@views.route('/result')
def searchResult():
    query = request.args.get('q')
    products = Products.query.msearch(query, fields=['name', 'description'])
    return render_template("searchResult.html", user=current_user, products=products)


@views.route('/addProduct', methods=['GET', 'POST'])
def addProduct():
    offercodes = OfferCodes.query.all()
    if request.method == 'POST':
        category = request.form.get('category')
        name = request.form.get('name')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        stock = request.form.get('stock')
        discount = request.form.get('discount_code')

        photo1 = saveImage(request.files.get('image1'))
        photo2 = saveImage(request.files.get('image2'))
        photo3 = saveImage(request.files.get('image3'))

        print(category, name, description, price, photo1)

        discount_check = OfferCodes.query.get(discount)
        if discount == '':
            discount_percentage = 0
        else:
            discount_check = OfferCodes.query.get(discount)
            discount_percentage = discount_check.discount_percentage
        totalPrice = price - (price * (discount_percentage / 100))
        new_product = Products(category=category, name=name, description=description, price=price, stock=stock,
                               image1=photo1, image2=photo2, image3=photo3, discount=discount,
                               discount_percentage=discount_percentage, totalPrice=totalPrice,
                               user_id=current_user.id)

        db.session.add(new_product)
        db.session.commit()
        flash('Product posted!', category='success')
        products = Products.query.filter_by(user_id=current_user.id)
        return render_template("home_seller.html", user=current_user, products=products)

    return render_template("addProduct.html", user=current_user, offercodes= offercodes)


@views.route('/dogs')
def electronics():
    page = request.args.get('page', 1, type=int)
    products = Products.query.filter_by(category="dogs").paginate(page=page, per_page=4)
    discount_percentages = calDiscount(products)
    return render_template("home_buyer1.html", products=products, user=current_user,
                           discount_percentages=discount_percentages)


@views.route('/cats')
def food():
    page = request.args.get('page', 1, type=int)
    products = Products.query.filter_by(category="cats").paginate(page=page, per_page=4)
    discount_percentages = calDiscount(products)
    return render_template("home_buyer1.html", products=products, user=current_user,
                           discount_percentages=discount_percentages)


@views.route('/birds')
def shoes():
    page = request.args.get('page', 1, type=int)
    products = Products.query.filter_by(category="birds").paginate(page=page, per_page=4)
    discount_percentages = calDiscount(products)
    return render_template("home_buyer1.html", products=products, user=current_user,
                           discount_percentages=discount_percentages)


@views.route('/smallAnimals')
def clothes():
    page = request.args.get('page', 1, type=int)
    products = Products.query.filter_by(category="smallAnimals").paginate(page=page, per_page=4)
    discount_percentages = calDiscount(products)
    return render_template("home_buyer1.html", products=products, user=current_user,
                           discount_percentages=discount_percentages)


@views.route('/editProduct/<int:id>', methods=['GET', 'POST'])
def editProduct(id):
    result = Products.query.get_or_404(id)
    offercodes = OfferCodes.query.all()
    if request.method == "POST":
        result.name = request.form.get('name')
        result.description = request.form.get('description')
        result.price = request.form.get('price')
        result.stock = request.form.get('stock')
        result.photo = request.files.get('image1')
        result.discount = request.form.get('discount')
        discount_check = OfferCodes.query.get(result.discount)
        if discount_check == '':
            discount_percentage = 0
        else:
            db.session.commit()
            flash(f'Your product has been updated', 'success')
            products = Products.query.filter_by(user_id=current_user.id)
            return render_template("home_seller.html", user=current_user, products=products)

    return render_template("editProduct.html", user=current_user, result=result, offercodes = offercodes)


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
    products = Products.query.filter(Products.stock > 0).order_by(desc(Products.is_sponsored)).paginate(page=page, per_page=4)
    session['name_order']="Default"
    session['order']="Default"

    if current_user.is_authenticated:
        messages = Message.query.filter(
            (Message.sender_id == current_user.id) |
            (Message.recipient_id == current_user.id)
        ).order_by(Message.timestamp.desc()).limit(10).all()
    else:
        messages = None

    discount_percentages = calDiscount(products)

    return render_template("home_buyer1.html", user=current_user, products=products, messages=messages,
                           discount_percentages=discount_percentages)


@views.route('/product/<int:id>')
def detailsPage(id):
    product = Products.query.get_or_404(id)
    seller = User.query.get_or_404(product.user_id)
    suggestions = Products.query.filter(Products.category == product.category, Products.id != id).limit(4).all()
    print(suggestions)
    discount_code = product.discount
    expired_offer = OfferCodes.query.filter_by(discount_code="EXPIREDOFFER").first()
    if discount_code:
        offer = OfferCodes.query.filter_by(discount_code=discount_code).first()

        if offer and offer.validity > date.today():
            discount_percentage = offer.discount_percentage
            discount_img_path = offer.discount_img
        else:
            discount_percentage = 0
            discount_img_path = expired_offer.discount_img
    else:
        discount_percentage = 0
        discount_img_path = ''

    return render_template("details.html", product=product, user=current_user, discount_percentage=discount_percentage,
                           discount_img_path=discount_img_path, seller=seller, suggestions=suggestions)


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


@views.route('/userDetails')
@login_required
def userDetails():
    details = UserDetails.query.filter_by(user_id=current_user.id).first()
    return render_template('userDetails.html', user=current_user, details=details)


@views.route('/editUserDetails', methods=['POST'])
@login_required
def editUserDetails():
    details = UserDetails.query.filter_by(user_id=current_user.id).first()
    if details:
        details.address = request.form['address']
        details.postalCode = request.form['postalCode']
        details.iban = request.form['iban']
        details.country = request.form['country']
    else:
        details = UserDetails(
            address=request.form['address'],
            postalCode=request.form['postalCode'],
            iban=request.form['iban'],
            country=request.form['country'],
            user_id=current_user.id
        )
        db.session.add(details)
    db.session.commit()
    return redirect(url_for('views.userDetails'))


@views.route('/addUserDetails', methods=['POST'])
@login_required
def addUserDetails():
    details = UserDetails(
        address=request.form['address'],
        postalCode=request.form['postalCode'],
        iban=request.form['iban'],
        country=request.form['country'],
        user_id=current_user.id
    )
    db.session.add(details)
    db.session.commit()
    return redirect(url_for('views.userDetails'))


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


@views.route('/sort/price', methods=['GET'])
def sort_by_price():
    order = session.get('order', "Descending")
    page = request.args.get('page', 1, type=int)
    if order == "Descending":
        products = Products.query.order_by(Products.totalPrice).paginate(page=page, per_page=4)
        order = "Ascending"
    else:
        products = Products.query.order_by(desc(Products.totalPrice)).paginate(page=page, per_page=4)
        order = "Descending"
    session['order'] = order
    print(order)

    discount_percentages = calDiscount(products)
    return render_template("home_buyer1.html", user=current_user, products=products,
                           discount_percentages=discount_percentages)


@views.route('/sort/name', methods=['GET'])
def sort_by_name():
    page = request.args.get('page', 1, type=int)
    name_order = session.get('name_order', "Descending")
    page = request.args.get('page', 1, type=int)
    if name_order == "Descending":
        products = Products.query.order_by(Products.name).paginate(page=page, per_page=4)
        name_order = "Ascending"
    else:
        products = Products.query.order_by(desc(Products.name)).paginate(page=page, per_page=4)
        name_order = "Descending"
    session['name_order'] = name_order
    print(name_order)
    discount_percentages = calDiscount(products)
    return render_template("home_buyer1.html", user=current_user, products=products,
                           discount_percentages=discount_percentages)


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
        offer = OfferCodes.query.filter_by(discount_code=product.discount).first()
        if offer:
            if offer.validity > date.today():
                price = product.price - product.price * offer.discount_percentage / 100
            else:
                price = product.price
        else:
            price = product.price
        print(session)

        if request.method == "POST":
            dictItems = {product_id: {'name': product.name, 'price': float(price),
                                      'quantity': quantity, 'image': product.image1}}
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
    details = UserDetails.query.filter_by(user_id=current_user.id).first()

    for key, product in session['shopping_cart'].items():
        total += float(product['price']) * int(product['quantity'])
    print(total)

    return render_template('cart.html', total=total, user=current_user,details=details)


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


@views.route('/placeOrder', methods=['GET', 'POST'])
def placeOrder():
    if request.method == "GET":
        try:
            session.modified = True
            order_id = np.random.randint(1, 10000)
            order = OrderDetails.query.get(order_id)

            while order is not None:
                order_id = np.random.randint(1, 10000)
                order = OrderDetails.query.get(order_id)
                print(session['shopping_cart'])

            for key, item in session['shopping_cart'].items():
                print(key)
                product = Products.query.get(key)
                if product.stock >= item['quantity']:
                    quantity = item['quantity']
                    product.stock -= quantity
                    user = User.query.get(product.user_id)
                    user.products_sold += quantity

                    orderDetails = OrderDetails(
                        order_id=order_id,
                        product_id=product.id,
                        product_name=product.name,
                        quantity=quantity,
                        user_id=current_user.id,
                        seller_id=product.user_id
                    )

                    db.session.add(orderDetails)

                    # Commit the changes to the database
                    db.session.commit()
                    print(order_id)

                    # Remove the item from the shopping cart


                    fetch_order = OrderDetails.query.filter_by(order_id=order_id).first()
                    print(fetch_order)
                    product_details = Products.query.get(fetch_order.product_id)
                else:
                    flash("Insufficient stock", category="error")
                    return redirect(url_for('views.getCart'))
            session.pop('shopping_cart', None)

        except Exception as e:
            print(e)
            flash("An error occurred while placing the order.", category="error")

    return render_template("order.html", user=current_user,orders=order_id)




@views.route('/seller_profile')
def seller_profile():
    user = User.query.get(current_user.id)
    awards = "None"
    if user.products_sold > 25:
        awards = "Gold"
    elif user.products_sold > 15 and user.products_sold <= 25:
        awards = "Silver"
    elif user.products_sold <= 15 and user.products_sold > 5:
        awards = "Bronze"
    ratings = OrderDetails.query.filter_by(seller_id=current_user.id).all()
    total_ratings = len(ratings)
    total_satisfaction = sum([rating.rating for rating in ratings if rating.rating is not None])

    if total_ratings > 0:
        satisfaction_percentage = (total_satisfaction / (total_ratings * 5)) * 100
    else:
        satisfaction_percentage = 0
    return render_template('seller_profile.html', user=user, awards=awards,satisfaction_percentage=satisfaction_percentage)


@views.route('/get-pro-membership', methods=['POST'])
def get_pro_membership():
    if request.method == 'POST':
        user = User.query.get(current_user.id)
        user.pro_membership = 'Yes'
        products = Products.query.filter_by(user_id=current_user.id).all()
        for product in products:
            product.is_sponsored = 'Yes'
        db.session.commit()
        flash('Pro Membership successfully activated!', 'success')
        return redirect(url_for('views.seller_profile'))


@views.route('/cancel-pro-membership', methods=['POST'])
def cancel_pro_membership():
    if request.method == 'POST':
        user = User.query.get(current_user.id)
        user.pro_membership = 'No'
        products = Products.query.filter_by(user_id=current_user.id).all()
        for product in products:
            product.is_sponsored = 'No'
        db.session.commit()
        flash('Pro Membership cancelled!', 'error')
        return redirect(url_for('views.seller_profile'))


@views.route('/addOffers', methods=['GET', 'POST'])
def addOffers():
    if request.method == 'POST':
        discount = request.form.get('discount')
        discount_code = request.form.get('discount_code')
        discount_image = saveImage(request.files.get('discount_img'))
        validity = request.form.get('validity')
        validity = datetime.strptime(validity, '%Y-%m-%d').date()

        new_offer = OfferCodes(seller_id=current_user.id, discount_code=discount_code, discount_img=discount_image,
                               discount_percentage=discount, validity=validity)

        db.session.add(new_offer)
        db.session.commit()
        flash('Offer posted!', category='success')
        products = Products.query.filter_by(user_id=current_user.id)
        return render_template("home_seller.html", user=current_user, products=products)

    return render_template("addOffers.html", user=current_user)


@views.route('/myOrders', methods=['GET', 'POST'])
@login_required
def myOrders():
    orders = OrderDetails.query.filter_by(user_id=current_user.id).all()
    return render_template("myorders.html", user=current_user, orders=orders)


@views.route('/order_seller_details/<int:id>')
def order_seller_details(id):
    user = User.query.get(id)
    awards = "None"
    if user.products_sold > 25:
        awards = "Gold"
    elif user.products_sold > 15 and user.products_sold <= 25:
        awards = "Silver"
    elif user.products_sold <= 15 and user.products_sold > 5:
        awards = "Bronze"
    ratings = OrderDetails.query.filter_by(seller_id=id).all()
    total_ratings = len(ratings)
    total_satisfaction = sum([rating.rating for rating in ratings if rating.rating is not None])

    if total_ratings > 0:
        satisfaction_percentage = (total_satisfaction / (total_ratings * 5)) * 100
    else:
        satisfaction_percentage = 0
    return render_template('order_seller_details.html', user=user, awards=awards,satisfaction_percentage=satisfaction_percentage)


@views.route('/submit_rating/<int:id>', methods=['POST'])
@login_required
def submit_rating(id):
    print(id)
    rating = int(request.form.get('rating'))
    order = OrderDetails.query.get(id)
    print(order)
    order.rating = rating
    order.num_rating += 1
    db.session.commit()
    flash('Rating submitted successfully.', 'success')
    return redirect(url_for('views.myOrders'))


