import hashlib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import session
from flask import url_for, flash, redirect
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, IntegerField, RadioField, FloatField, SelectField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import DataRequired, Length, Email

#from marathon import mysql
from marathon.models import *
from marathon import cur


def getAllProducts():
    itemData = Product.query.join(ProductCategory, Product.productid == ProductCategory.productid) \
        .add_columns(Product.productid, Product.product_name, Product.discounted_price, Product.description,
                     Product.image, Product.quantity) \
        .join(Category, Category.categoryid == ProductCategory.categoryid) \
        .order_by(Category.categoryid.desc()) \
        .all()
    return itemData


def getCategoryDetails():
    itemData = Category.query.join(ProductCategory, Category.categoryid == ProductCategory.categoryid) \
        .join(Product, Product.productid == ProductCategory.productid) \
        .order_by(Category.categoryid.desc()) \
        .distinct(Category.categoryid) \
        .all()
    return itemData


def massageItemData(data):
    ans = []
    i = 0
    while i < len(data):
        curr = []
        for j in range(6):
            if i >= len(data):
                break
            curr.append(data[i])
            i += 1
        ans.append(curr)
    return ans


def is_valid(email, password):
    # Using Flask-SQLAlchmy ORM
    userData = User.query.with_entities(User.email, User.password).all()

    # Using Raw SQL Select Query
    #cur = mysql.connection.cursor()
    #cur.execute('SELECT email, password FROM "user"')
    #userData = cur.fetchall()
    #cur.close()

    for row in userData:
        if row.email == email and row.password == password:
            return True
    return False


def getLoginUserDetails():
    productCountinCartForGivenUser = 0

    if 'email' not in session:
        loggedIn = False
        firstName = ''
    else:
        loggedIn = True
        userid, firstName = User.query.with_entities(User.userid, User.fname).filter(
            User.email == session['email']).first()

        productCountinCart = []

        # for Cart in Cart.query.filter(Cart.userId == userId).distinct(Products.productId):
        for cart in Cart.query.filter(Cart.userid == userid).all():
            productCountinCart.append(cart.productid)
            productCountinCartForGivenUser = len(productCountinCart)

    return (loggedIn, firstName, productCountinCartForGivenUser, userid)


def getProductDetails(productId):
    productDetailsById = Product.query.filter(Product.productid == productId).first()
    return productDetailsById

def getUserDetails():
    if 'email' in session:
        userdetails = User.query.filter(User.email == session['email']).first()
    return userdetails


def extractAndPersistUserDataFromForm(request):
    password = request.form['password']
    email = request.form['email']
    firstName = request.form['firstName']
    lastName = request.form['lastName']
    address = request.form['address']
    phone = request.form['phone']
    username = request.form['username']

    user = User(fname=firstName, lname=lastName, password=password, address=address,
                email=email, phone=phone, username=username)
    db.session.add(user)
    db.session.flush()
    db.session.commit()
    return "Registered Successfully"


def isUserLoggedIn():
    if 'email' not in session:
        return False
    else:
        return True


# check if user is an admin.html
def isUserAdmin():
    if isUserLoggedIn():
        # ProductCategory.query.filter_by(productid=product.productid).first()
        userId, usertype = User.query.with_entities(User.userid, User.usertype).filter(User.email == session['email']).first()
        if User.query.get_or_404(userId) and usertype == 'admin':
            return True
        else:
            return False



# Using Flask-SQL Alchemy SubQuery
def extractAndPersistKartDetailsUsingSubquery(productId):
    userId = User.query.with_entities(User.userid).filter(User.email == session['email']).first()
    userId = userId[0]

    subqury = Cart.query.filter(Cart.userid == userId).filter(Cart.productid == productId).subquery()
    qry = db.session.query(Cart.quantity).select_entity_from(subqury).all()

    if len(qry) == 0:
        cart = Cart(userid=userId, productid=productId, quantity=1)
    else:
        cart = Cart(userid=userId, productid=productId, quantity=qry[0][0] + 1)

    db.session.merge(cart)
    db.session.flush()
    db.session.commit()

# Using Flask-SQL Alchemy query
def extractAndPersistKartDetailsUsingkwargs(productId):
    userId = User.query.with_entities(User.userid).filter(User.email == session['email']).first()
    userId = userId[0]

    kwargs = {'userid': userId, 'productid': productId}
    quantity = Cart.query.with_entities(Cart.quantity).filter_by(**kwargs).first()

    if quantity is not None:
        cart = Cart(userid=userId, productid=productId, quantity=quantity[0] + 1)
    else:
        cart = Cart(userid=userId, productid=productId, quantity=1)

    db.session.merge(cart)
    db.session.flush()
    db.session.commit()


class addCategoryForm(FlaskForm):
    category_name = StringField('Category Name', validators=[DataRequired()])
    submit = SubmitField('Save')

class addProductForm(FlaskForm):
    category = SelectField('Category:', coerce=int, id='select_category')
    gender = SelectField('Gender:', coerce=int, id='select_gender')
    productName = StringField('Product Name:', validators=[DataRequired()])
    productDescription = TextAreaField('Product Description:', validators=[DataRequired()])
    productPrice = FloatField('Product Price:', validators=[DataRequired()])
    discountedPrice = FloatField('Discounted Price:', validators=[DataRequired()])
    productQuantity = IntegerField('Product Quantity:', validators=[DataRequired()])
    image1 = FileField('Product Image 1', validators=[FileAllowed(['jpg', 'png'])])
    image2 = FileField('Product Image 2', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Save')


# START CART MODULE
# Gets products in the cart
def getusercartdetails():
    userId = User.query.with_entities(User.userid).filter(User.email == session['email']).first()

    productsincart = Product.query.join(Cart, Product.productid == Cart.productid) \
        .add_columns(Product.productid, Product.product_name, Product.regular_price, Product.discounted_price, Cart.quantity, Product.image) \
        .add_columns(Product.discounted_price * Cart.quantity).filter(
        Cart.userid == userId[0])
    totalsum = 0

    for row in productsincart:
        totalsum += row[7]

    return (productsincart, totalsum)


# Removes products from cart when user clicks remove
def removeProductFromCart(productId):
    userId = User.query.with_entities(User.userid).filter(User.email == session['email']).first()
    userId = userId[0]
    kwargs = {'userid': userId, 'productid': productId}
    cart = Cart.query.filter_by(**kwargs).first()
    if productId is not None:
        db.session.delete(cart)
        db.session.commit()
        flash("Product has been removed from cart !!")
    else:
        flash("failed to remove Product cart please try again !!")
    return redirect(url_for('cart'))


# flask form for checkout details
class checkoutForm(FlaskForm):
    fullname = StringField('Full Name',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    address = TextAreaField('address',
                            validators=[DataRequired()])
    city = StringField('city',
                       validators=[DataRequired(), Length(min=2, max=20)])
    state = StringField('state',
                        validators=[DataRequired(), Length(min=2, max=20)])
    zip = StringField('zip',
                      validators=[DataRequired(), Length(min=2, max=6)])
    cctype = RadioField('cardtype')
    cardname = StringField('cardnumber',
                           validators=[DataRequired(), Length(min=12, max=12)])
    ccnumber = StringField('Credit card number',
                           validators=[DataRequired()])

    expmonth = StringField('Exp Month',
                           validators=[DataRequired(), Length(min=12, max=12)])
    expyear = StringField('Expiry Year',
                          validators=[DataRequired(), Length(min=4, max=4)])
    cvv = StringField('CVV',
                      validators=[DataRequired(), Length(min=3, max=4)])
    submit = SubmitField('MAKE PAYMENT')


# Gets form data for the sales transaction

def extractOrderdetails(request, totalsum):
    #fullname = request.form['FullName']
    fullname = request.form['firstname'] + " " + request.form['lastname']
    email = request.form['email']
    address = request.form['address']
    phone = request.form['phone']
    cctype = request.form['cardtype']
    ccnumber = request.form['cardnum']
    orderdate = datetime.utcnow()
    userId = User.query.with_entities(User.userid).filter(User.email == session['email']).first()
    userId = userId[0]
    order = Order(order_date=orderdate, total_price=int(totalsum), userid=userId)
    db.session.add(order)
    db.session.flush()
    db.session.commit()

    orderid = Order.query.with_entities(Order.orderid).filter(Order.userid == userId).order_by(
        Order.orderid.desc()).first()

    # add details to ordered;
    #  products table
    addOrderedproducts(userId, orderid)
    # add transaction details to the table
    updateSalestransaction(totalsum, ccnumber, orderid, cctype)

    # remove ordered products from cart after transaction is successful
    removeordprodfromcart(userId)
    # sendtextconfirmation(phone,fullname,orderid)
    return (email, fullname, orderid, address, fullname, phone)


# adds data to orderdproduct table

def addOrderedproducts(userId, orderid):
    cart = Cart.query.with_entities(Cart.productid, Cart.quantity).filter(Cart.userid == userId)

    for item in cart:
        orderedproduct = OrderedProduct(orderid=orderid, productid=item.productid, quantity=item.quantity)
        db.session.add(orderedproduct)

        product_qty = Product.query.filter_by(productid=item.productid).first()
        product_qty.quantity = product_qty.quantity - item.quantity

        db.session.flush()
        db.session.commit()


# removes all sold products from cart for the user

def removeordprodfromcart(userId):
    userid = userId
    db.session.query(Cart).filter(Cart.userid == userid).delete()
    db.session.commit()


# adds sales transaction

def updateSalestransaction(totalsum, ccnumber, orderid, cctype):
    salesTransaction = SaleTransaction(orderid=orderid, transaction_date=datetime.utcnow(), amount=totalsum,
                                       cc_number=ccnumber, cc_type=cctype, response="success")
    db.session.add(salesTransaction)
    db.session.flush()
    db.session.commit()


# sends email for order confirmation
'''
def sendEmailconfirmation(email, username, ordernumber, phonenumber):
    msg = MIMEMultipart()
    sitemail = "stargadgets@engineer.com"
    msg['Subject'] = "Your Order has been placed for " + username
    msg['From'] = sitemail
    msg['To'] = email
    text = "Hello!\nThank you for shopping with us.Your order No is:" +str(ordernumber[0])
    html = """\
        <html>
          <head></head>
          <body>
            <p><br>
               Please stay tuned for more fabulous offers and gadgets.You can visit your account for more details on this order.<br> 
               <br>Please write to us at <u>stargadgets@engineer.com</u> for any assistance.</br>
               <br></br>
               <br></br>
               Thank you!
               <br></br>
               StarGadgets Team          
            </p>
          </body>
        </html>
        """
    msg1 = MIMEText(text, 'plain')
    msg2 = MIMEText(html, 'html')
    msg.attach(msg1)
    msg.attach(msg2)
    server = smtplib.SMTP(host='smtp.mail.com', port=587)
    server.connect('smtp.mail.com', 587)
    # Extended Simple Mail Transfer Protocol (ESMTP) command sent by an email server to identify itself when connecting to another email.

    server.ehlo()
    # upgrade insecure connection to secure
    server.starttls()
    server.ehlo()
    server.login("stargadgets@engineer.com", "stargadget@123")
    server.ehlo()
    server.sendmail(sitemail, email, msg.as_string())
    # hack to send text confirmation using emailsms gateway
    phonenumber = phonenumber + "@tmomail.net"

     #   phonenumber = phonenumber + "@txt.att.net"

    server.sendmail(sitemail, phonenumber, msg.as_string())
    server.quit()
'''
# except:
#     "no tls please try again later"
#     return False

# def sendTextnotification(phone,fullname,orderid):


# problem 1--TextMagic lots of unknown packages
# username = "akankshanegi"
# token = "di18DWYaXQRT3KqDLn8wfYpr5utQl3"
# client = TextmagicRestClient(username, token)
#
# message = client.messages.create(phones="8478486054", text="Hello TextMagic")

# problem 2--TWILIO not free need to buy a paid number
# # the following line needs your Twilio Account SID and Auth Token
# client = Client("AC488c3b9e98a6bbbf84d5002631f2fd63", "f1b4ca2a3913f5f39ba6a7cf44afb77f")
#
# # change the "from_" number to your Twilio number and the "to" number
# # to the phone number you signed up for Twilio with, or upgrade your
# # account to send SMS to any phone number
# client.messages.create(to="+18478486054",
#                        from_="+15005550006",
#                        body="Hello from Python!")


# END CART MODULE
