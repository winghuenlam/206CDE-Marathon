from datetime import datetime
from marathon import db


db.Model.metadata.reflect(db.engine)


class User(db.Model):
    __table_args__ = {'extend_existing': True}
    userid = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(20), nullable=False)
    lname = db.Column(db.String(20), nullable=False)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(60), nullable=False)
    address = db.Column(db.String(20), unique=False, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(8), nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    usertype = db.Column(db.String(20), nullable=False, default='customer')

    def __repr__(self):
        return f"User('{self.fname}', '{self.lname}'), '{self.username}', '{self.password}', " \
               f"'{self.email}','{self.phone}', '{self.usertype}')"


class Category(db.Model):
    __table_args__ = {'extend_existing': True}
    categoryid = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Category('{self.categoryid}', '{self.category_name}')"

class Gender(db.Model):
    __table_args__ = {'extend_existing': True}
    genderid = db.Column(db.Integer, primary_key=True)
    gender_name = db.Column(db.String(30), nullable=False)

    def __repr__(self):
        return f"Gender('{self.genderid}', '{self.gender_name}')"


class Product(db.Model):
    __table_args__ = {'extend_existing': True}
    productid = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(100), nullable=False)
    image2 = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    regular_price = db.Column(db.DECIMAL)
    discounted_price = db.Column(db.DECIMAL)
    product_rating = db.Column(db.DECIMAL)
    product_review = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f"Product('{self.productid}','{self.product_name}','{self.description}', '{self.image}',  '{self.quantity}', '{self.regular_price}', '{self.discounted_price}')"


class ProductCategory(db.Model):
    __table_args__ = {'extend_existing': True}
    categoryid = db.Column(db.Integer, db.ForeignKey('category.categoryid'), nullable=False, primary_key=True)
    productid = db.Column(db.Integer, db.ForeignKey('product.productid'), nullable=False, primary_key=True)
    created_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Product('{self.categoryid}', '{self.productid}')"


class ProductGender(db.Model):
    __table_args__ = {'extend_existing': True}
    genderid = db.Column(db.Integer, db.ForeignKey('gender.genderid'), nullable=False, primary_key=True)
    productid = db.Column(db.Integer, db.ForeignKey('product.productid'), nullable=False, primary_key=True)
    created_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"Product('{self.genderid}', '{self.productid}')"


class Cart(db.Model):
    __table_args__ = {'extend_existing': True}
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False, primary_key=True)
    productid = db.Column(db.Integer, db.ForeignKey('product.productid'), nullable=False, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"Cart('{self.userid}', '{self.productid}, '{self.quantity}')"


class Order(db.Model):
    __table_args__ = {'extend_existing': True}
    orderid = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, nullable=False)
    total_price = db.Column(db.DECIMAL, nullable=False)
    userid = db.Column(db.Integer, db.ForeignKey('user.userid'), nullable=False, primary_key=True)


    def __repr__(self):
        return f"Order('{self.orderid}', '{self.order_date}','{self.total_price}','{self.userid}'')"

class OrderedProduct(db.Model):
    __table_args__ = {'extend_existing': True}
    ordproductid = db.Column(db.Integer, primary_key=True)
    orderid = db.Column(db.Integer,db.ForeignKey('order.orderid'), nullable=False)
    productid = db.Column(db.Integer,db.ForeignKey('product.productid'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)


    def __repr__(self):
        return f"Order('{self.ordproductid}', '{self.orderid}','{self.productid}','{self.quantity}')"



class SaleTransaction(db.Model):
    __table_args__ = {'extend_existing': True}
    transactionid = db.Column(db.Integer, primary_key=True)
    orderid = db.Column(db.Integer,db.ForeignKey('order.orderid'), nullable=False)
    transaction_date = db.Column(db.DateTime,nullable=False)
    amount = db.Column(db.DECIMAL, nullable=False)
    cc_number=db.Column(db.String(50), nullable=False)
    cc_type = db.Column(db.String(50), nullable=False)
    response = db.Column(db.String(50), nullable=False)


    def __repr__(self):
        return f"Order('{self.transactionid}', '{self.orderid}','{self.transactiondate}','{self.amount}', '{self.cc_number}','{self.cc_type}','{self.response}')"
