from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class Products(db.Model):
    __searchable__ = ['name', 'description']
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer)
    stock = db.Column(db.Integer)

    image1 = db.Column(db.String(120), default='image.jpg')
    image2 = db.Column(db.String(120), default='image.jpg')
    image3 = db.Column(db.String(120), default='image.jpg')

    discount = db.Column(db.Integer)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    offers = db.Column(db.String(120), default="0",nullable=False)
    offer_img = db.Column(db.String(120), default='image.jpg')


# seller homepage
# price,stock, name a-z
# top 5 products seller.

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    userType = db.Column(db.String(20))
    firstName = db.Column(db.String(150))
    products = db.relationship('Products')
