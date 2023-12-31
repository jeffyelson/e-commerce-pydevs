from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import date


class Products(db.Model):
    __searchable__ = ['name', 'description']
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(precision=10, scale=2))
    totalPrice = db.Column(db.Numeric(precision=10, scale=2))
    stock = db.Column(db.Integer)

    image1 = db.Column(db.String(120), default='image.jpg')
    image2 = db.Column(db.String(120), default='image.jpg')
    image3 = db.Column(db.String(120), default='image.jpg')

    discount = db.Column(db.String(100), db.ForeignKey('offer_codes.discount_code'))
    discount_percentage = db.Column(db.Integer)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    offers = db.Column(db.String(120), default="0", nullable=False)
    offer_img = db.Column(db.String(120), default='image.jpg')
    is_sponsored = db.Column(db.String(120),default="No")


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    userType = db.Column(db.String(20))
    firstName = db.Column(db.String(150))
    products = db.relationship('Products')
    messages_sent = db.relationship('Message', backref='sender', foreign_keys='Message.sender_id')
    messages_received = db.relationship('Message', backref='recipient', foreign_keys='Message.recipient_id')
    products_sold = db.Column(db.Integer,default=0)
    pro_membership = db.Column(db.String(5),default="No")



class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=func.now())

class OfferCodes(db.Model):
    discount_code = db.Column(db.String(100), primary_key=True)
    discount_percentage = db.Column(db.Integer)
    validity = db.Column(db.Date, default=date.today)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    discount_img = db.Column(db.String(120), default='image.jpg')
    products = db.relationship('Products')

class UserDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    postalCode = db.Column(db.Integer)
    address = db.Column(db.String(120))
    iban = db.Column(db.String(50))
    country = db.Column(db.String(30))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class OrderDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    product_name = db.Column(db.String(150), db.ForeignKey('products.name'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    quantity = db.Column(db.Integer)
    seller_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    rating = db.Column(db.Integer,default=0)
    num_rating = db.Column(db.Integer,default=0)


