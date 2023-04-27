# defines that this page is the blueprint of the website.
from flask import Blueprint, render_template, request, flash
from flask_login import login_required, logout_user, current_user
from .models import Products
from . import db

views = Blueprint('views', __name__)


@views.route('/')
@login_required
def home():
    return render_template("home.html", user = current_user)

@views.route('/upload',methods=['POST'])



@views.route('/seller',methods=['GET','POST'])
@login_required
def home_seller():
    if request.method=='POST':
        description = request.form.get('product')
        price = request.form.get('price')
        picture = request.files['file']
        print(picture)

        print(description)


        if len(description) < 2:
            flash('Description needs to be more than 5 characters', category='error')
        else:
            new_product = Products(description=description,price=price,user_id =current_user.id, picture=picture.read())
            db.session.add(new_product)
            db.session.commit()
            flash('Product posted!', category='success')

    return render_template("home_seller.html", user = current_user)


@views.route('/buyer')
@login_required
def home_buyer():
    products = Products.query.all()
    return render_template("home_buyer.html", user = current_user, products = products)
