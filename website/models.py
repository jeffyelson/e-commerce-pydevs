from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class Products(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    description = db.Column(db.String(100))
    price = db.Column(db.Integer)
    date = db.Column(db.DateTime(timezone =True),default =func.now())
    picture = db.Column(db.Text)
    mimetype = db.Column(db.Text)
    user_id =db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin ):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique= True)
    password = db.Column(db.String(150))
    userType = db.Column(db.String(20))
    firstName = db.Column(db.String(150))
    products = db.relationship('Products')