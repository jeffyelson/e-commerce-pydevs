# defines that this page is the blueprint of the website.
from flask import Blueprint, render_template, request, flash, current_app
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
    return render_template("home.html", user=current_user, products=products)


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
        photo = saveImage(request.files.get('image'))

        print(category, name, description, price, photo)

        new_product = Products(category=category, name=name, description=description, price=price, stock=stock,
                               image=photo,
                               user_id=current_user.id)
        db.session.add(new_product)
        db.session.commit()
        flash('Product posted!', category='success')
        products = Products.query.filter_by(user_id=current_user.id)
        return render_template("home_seller.html", user=current_user, products=products)

    return render_template("addProduct.html", user=current_user)


@views.route('/editProduct/<int:id>', methods=['GET', 'POST'])
def editProduct(id):
    result = Products.query.get_or_404(id)
    if request.method == "POST":
        result.name = request.form.get('name')
        result.description = request.form.get('description')
        result.price = request.form.get('price')
        result.stock = request.form.get('stock')
        result.photo = saveImage(request.files.get('image'))
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
@login_required
def home_buyer():
    products = Products.query.all()
    return render_template("home_buyer.html", user=current_user, products=products)
