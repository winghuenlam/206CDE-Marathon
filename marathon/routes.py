import os
import secrets
from PIL import Image
from flask import render_template, request
from marathon import app
from marathon.forms import *
from plotly.offline import plot
import plotly.graph_objs as go
from flask import Markup
from marathon.models import *
from sqlalchemy.sql import func


@app.route("/signIn")
def loginForm():
    if 'email' in session:
        return redirect(url_for('index'))
    else:
        return render_template('register.html', error='')


@app.route("/login", methods=['POST', 'GET'])
def login_submit():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid(email, password):
            session['email'] = email
            
            return redirect(url_for('index'))
        else:
            error = 'Invalid Email / Password'
            return render_template('register.html', error=error)


@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect(url_for('index'))


@app.route("/registerationForm")
def registrationForm():
    isAdmin = isUserAdmin()
    return render_template("register.html", isAdmin=isAdmin)


@app.route("/register/submit", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Parse form data
        msg = extractAndPersistUserDataFromForm(request)
        return render_template("index.html", error=msg)


@app.route("/")
@app.route("/index")
def index():
    if isUserLoggedIn():
        isAdmin = isUserAdmin()
        loggedIn, firstName, productCountinKartForGivenUser, userid = getLoginUserDetails()
        allProductDetails = getAllProducts()
        allProductsMassagedDetails = massageItemData(allProductDetails)
        categoryData = getCategoryDetails()

        return render_template('index.html', itemData=allProductsMassagedDetails, loggedIn=loggedIn, firstName=firstName,
                               productCountinKartForGivenUser=productCountinKartForGivenUser,
                               categoryData=categoryData, isAdmin=isAdmin)
    return render_template('index.html')

''' 
@app.route("/displayGenderCategory")
def displayGenderCategory():
    isAdmin = isUserAdmin()
    loggedIn, firstName, noOfItems, userid = getLoginUserDetails()
    categoryId = request.args.get("categoryId")
    genderId = request.args.get("genderId")

    productDetails = Product.query.join(ProductCategory, Product.productid == ProductCategory.productid) \
        .add_columns(Product.productid, Product.product_name, Product.regular_price, Product.discounted_price,
                     Product.image) \
        .join(ProductGender, Product.productid == ProductGender.productid) \
        .join(Category, Category.categoryid == ProductCategory.categoryid) \
        .filter(Category.categoryid == int(categoryId)) \
        .add_columns(Category.category_name) \
        .join(Gender, Gender.genderid == ProductGender.genderid) \
        .filter(Gender.genderid == int(genderId)) \
        .add_columns(Gender.gender_name) \
        .all()

    categoryName = productDetails[0].category_name
    genderName = productDetails[0].gender_name
    data = massageItemData(productDetails)
    return render_template('category_products.html', data=data, loggedIn=loggedIn, firstName=firstName,
                           noOfItems=noOfItems, categoryName=categoryName, genderName=genderName, userid=userid, isAdmin=isAdmin)
'''

@app.route("/displayGender")
def displayGender():
    isAdmin = isUserAdmin()
    genderId = request.args.get("genderId")

    productDetailsByGenderId = Product.query.join(ProductGender, Product.productid == ProductGender.productid) \
        .add_columns(Product.productid, Product.product_name, Product.regular_price, Product.discounted_price,
                     Product.image, Product.image2) \
        .join(Gender, Gender.genderid == ProductGender.genderid) \
        .filter(Gender.genderid == int(genderId)) \
        .add_columns(Gender.gender_name) \
        .all()

    genderName = productDetailsByGenderId[0].gender_name
    products = massageItemData(productDetailsByGenderId)
    gender = [(row.gender_name) for row in Gender.query.all()]
    #products = Product.query.all()
    return render_template('gender_products.html', products=products, genderName=genderName, gender=gender, isAdmin=isAdmin)


@app.route("/addToCart")
def addToCart():
    if isUserLoggedIn():
        productId = int(request.args.get('productId'))

        # Using Flask-SQLAlchmy SubQuery
        extractAndPersistKartDetailsUsingSubquery(productId)

        # Using Flask-SQLAlchmy normal query
        # extractAndPersistKartDetailsUsingkwargs(productId)
        flash('Item successfully added to cart !!', 'success')
        return redirect(url_for('cart'))
    else:
        return redirect(url_for('loginForm'))


@app.route("/cart")
def cart():
    if isUserLoggedIn():
        isAdmin = isUserAdmin()
        loggedIn, firstName, productCountinKartForGivenUser, userid = getLoginUserDetails()
        cartdetails, totalsum = getusercartdetails();
        return render_template("cart.html", cartData=cartdetails,
                               productCountinKartForGivenUser=productCountinKartForGivenUser, loggedIn=loggedIn,
                               firstName=firstName, totalsum=totalsum, userid=userid, isAdmin=isAdmin)
    else:
        return redirect(url_for('index'))


@app.route("/user/orders")
def getUserOrders():
    if isUserLoggedIn():
        loggedIn, firstName, productCountinKartForGivenUser, userid = getLoginUserDetails()

        orderDetails = db.session.query(Order, OrderedProduct, Product) \
        .join(OrderedProduct, Order.orderid==OrderedProduct.orderid) \
        .join(Product, Product.productid==OrderedProduct.productid) \
        .filter(Order.userid == userid) \
        .all()

        #products = Product.query.all()
        return render_template('userOrders.html', orderDetails=orderDetails)
    return redirect(url_for('index'))


@app.route("/admin/category/<int:category_id>", methods=['GET'])
def category(category_id):
    if isUserAdmin():
        isAdmin = True
        category = Category.query.get_or_404(category_id)
        return render_template('adminCategory.html', category=category, isAdmin=isAdmin)
    return redirect(url_for('index'))

@app.route("/admin/categories/new", methods=['GET', 'POST'])
def addCategory():
    if isUserAdmin():
        isAdmin = True
        form = addCategoryForm()
        if form.validate_on_submit():
            category = Category(category_name=form.category_name.data)
            db.session.add(category)
            db.session.commit()
            flash(f'Category {form.category_name.data}! added successfully', 'success')
            return redirect(url_for('getCategories'))
        return render_template("addCategory.html", form=form, isAdmin=isAdmin)
    return redirect(url_for('getCategories'))


@app.route("/admin/categories/<int:category_id>/update", methods=['GET', 'POST'])
def update_category(category_id):
    if isUserAdmin():
        isAdmin = True
        category = Category.query.get_or_404(category_id)
        form = addCategoryForm()
        if form.validate_on_submit():
            category.category_name= form.category_name.data
            db.session.commit()
            flash('This category has been updated!', 'success')
            return redirect(url_for('getCategories'))
        elif request.method == 'GET':
            form.category_name.data = category.category_name
        return render_template('addCategory.html', legend="Update Category", form=form, isAdmin=isAdmin)
    return redirect(url_for('getCategories'))


@app.route("/admin/category/<int:category_id>/delete", methods=['POST'])
def delete_category(category_id):
    if isUserAdmin():
        ProductCategory.query.filter_by(categoryid=category_id).delete()
        db.session.commit()
        category= Category.query.get_or_404(category_id)
        db.session.delete(category)
        db.session.commit()
        flash('Your category has been deleted!', 'success')
    return redirect(url_for('getCategories'))

@app.route("/admin/categories", methods=['GET'])
def getCategories():
    if isUserAdmin():
        isAdmin = True
        #categories = Category.query.all()
        #cur = mysql.connection.cursor()
        #Query for number of products on a category:
        cur.execute('SELECT category.categoryid, category.category_name, COUNT(product_category.productid) as noOfProducts FROM category LEFT JOIN product_category ON category.categoryid = product_category.categoryid GROUP BY category.categoryid, category.category_name');
        categories = cur.fetchall()
        return render_template('adminCategories.html', categories = categories, isAdmin=isAdmin)
    return redirect(url_for('index'))


#this method is copied from Schafer's tutorials
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = form_picture.filename
    picture_path = os.path.join(app.static_folder, 'img', picture_fn)

    output_size = (250, 250)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn



@app.route("/admin/products", methods=['GET'])
def getProducts():
    if isUserAdmin():
        isAdmin = True
        products = Product.query.all()
        return render_template('adminProducts.html', products=products, isAdmin=isAdmin)
    return redirect(url_for('index'))

@app.route("/products", methods=['GET'])
def products():
    isAdmin = isUserAdmin()
    products = Product.query.all()
    gender = [(row.gender_name) for row in Gender.query.all()]
    return render_template('products.html', products=products, gender=gender, isAdmin=isAdmin)

@app.route("/admin/products/new", methods=['GET', 'POST'])
def addProduct():
    if isUserAdmin():
        isAdmin = True
        form = addProductForm()
        form.category.choices = [(row.categoryid, row.category_name) for row in Category.query.all()]
        form.gender.choices = [(row.genderid, row.gender_name) for row in Gender.query.all()]
        product_icon1 = "" #safer way in case the image is not included in the form
        if form.validate_on_submit():
            if form.image1.data:
                product_icon1 = save_picture(form.image1.data)
            if form.image2.data:
                product_icon2 = save_picture(form.image2.data)
            product = Product(product_name=form.productName.data, description=form.productDescription.data, image=product_icon1, image2=product_icon2, quantity=form.productQuantity.data, discounted_price=form.discountedPrice.data, product_rating=0, product_review=" ", regular_price=form.productPrice.data)

            db.session.add(product)
            db.session.commit()
            product_category = ProductCategory(categoryid=form.category.data, productid=product.productid)
            product_gender = ProductGender(genderid=form.gender.data, productid=product.productid)
            db.session.add(product_category)
            db.session.commit()
            db.session.add(product_gender)
            db.session.commit()

            flash(f'Product {form.productName} added successfully', 'success')
            return redirect(url_for('getProducts'))
        return render_template("addProduct.html", form=form, legend="New Product", isAdmin=isAdmin)
    return redirect(url_for('index'))


@app.route("/product/<int:product_id>", methods=['GET'])
def product(product_id):
    isAdmin = isUserAdmin()
    product = Product.query.get_or_404(product_id)
    productid = request.args.get('productId')#for add cart
    productDetailsByProductId = getProductDetails(productid)#for add cart
    return render_template('products_detail.html', product=product, isAdmin=isAdmin)
   


@app.route("/admin/product/<int:product_id>", methods=['GET'])
def admin_product(product_id):
    if isUserAdmin():
        isAdmin = True
        loggedIn, firstName, noOfItems, userid = getLoginUserDetails()
        product = Product.query.get_or_404(product_id)
        productid = request.args.get('productId')#for add cart
        productDetailsByProductId = getProductDetails(productid)#for add cart
        return render_template('admin_products_detail.html', product=product, loggedIn=loggedIn,
                           firstName=firstName,
                           noOfItems=noOfItems, isAdmin=isAdmin)
    return redirect(url_for('index'))
  

@app.route("/admin/product/<int:product_id>/update", methods=['GET', 'POST'])
def update_product(product_id):
    if isUserAdmin():
        isAdmin = True
        product = Product.query.get_or_404(product_id)
        form = addProductForm()
        form.category.choices = [(row.categoryid, row.category_name) for row in Category.query.all()]
        form.gender.choices = [(row.genderid, row.gender_name) for row in Gender.query.all()]
        if form.validate_on_submit():
            if form.image1.data:
                product.image = save_picture(form.image1.data)
            if form.image2.data:
                product.image2 = save_picture(form.image2.data)
            product.product_name = form.productName.data
            product.productDescription = form.productDescription.data
            product.quantity = form.productQuantity.data
            # product.discounted_price = form.data.discounted_price = 15
            product.regular_price = form.productPrice.data
            product.discounted_price = form.discountedPrice.data
            db.session.commit()
            product_category = ProductCategory.query.filter_by(productid = product.productid).first()
            if form.category.data != product_category.categoryid:
                new_product_category = ProductCategory(categoryid=form.category.data, productid = product.productid)
                db.session.add(new_product_category)
                db.session.commit()
                db.session.delete(product_category)
                db.session.commit()

            product_gender = ProductGender.query.filter_by(productid = product.productid).first()
            if form.gender.data != product_gender.genderid:
                new_product_gender = ProductGender(genderid=form.gender.data, productid = product.productid)
                db.session.add(new_product_gender)
                db.session.commit()
                db.session.delete(product_gender)
                db.session.commit()

            flash('This product has been updated!', 'success')
            return redirect(url_for('getProducts'))
        elif request.method == 'GET':
            form.productName.data = product.product_name
            form.productDescription.data = product.description
            form.productPrice.data = product.regular_price
            form.productQuantity.data = product.quantity
        return render_template('addProduct.html', legend="Update Product", form=form, isAdmin=isAdmin)
    return redirect(url_for('index'))

@app.route("/admin/product/<int:product_id>/delete", methods=['POST'])
def delete_product(product_id):
    if isUserAdmin():
        product_category = ProductCategory.query.filter_by(productid=product_id).first()
        if product_category is not None:
            db.session.delete(product_category)
            db.session.commit()
        Cart.query.filter_by(productid=product_id).delete()
        db.session.commit()
        product = Product.query.get_or_404(product_id)
        db.session.delete(product)
        db.session.commit()
        flash('Your product has been deleted!', 'success')
    return redirect(url_for('getProducts'))


@app.route("/admin/users")
def getUsers():
    if isUserAdmin():
        isAdmin = True
        # users = User.query.all()
        #cur = mysql.connection.cursor()
        cur.execute("SELECT u.fname, u.lname, u.email, u.phone, COUNT(o.orderid) as noOfOrders FROM `user` u LEFT JOIN `order` o ON u.userid = o.userid WHERE u.usertype = 'customer' GROUP BY u.userid")
        users = cur.fetchall()
        return render_template('adminUsers.html', users= users, isAdmin=isAdmin)
    return redirect(url_for('index'))


@app.route("/admin/orders")
def getOrders():
    if isUserAdmin():
        isAdmin = True

        orderDetails = db.session.query(Order, OrderedProduct, Product) \
        .join(OrderedProduct, Order.orderid==OrderedProduct.orderid) \
        .join(Product, Product.productid==OrderedProduct.productid) \
        .all()

        #products = Product.query.all()
        return render_template('adminOrders.html', orderDetails=orderDetails, isAdmin=isAdmin)
    return redirect(url_for('index'))


@app.route("/removeFromCart")
def removeFromCart():
    if isUserLoggedIn():
        productId = int(request.args.get('productId'))
        removeProductFromCart(productId)
        return redirect(url_for('cart'))
    else:
        return redirect(url_for('loginForm'))


@app.route("/checkoutPage")
def checkoutForm():
    if isUserLoggedIn():
        isAdmin = isUserAdmin()
        cartdetails, totalsum = getusercartdetails()
        loggedIn, firstName, productCountinKartForGivenUser, userid = getLoginUserDetails() 
        userdetails = getUserDetails()
       
        #return render_template("checkout1.html", cartData=cartdetails, totalsum=totalsum, userdetails=userdetails)
        return render_template("checkout1.html", cartData=cartdetails, totalsum=totalsum, userdetails=userdetails, isAdmin=isAdmin)

    else:
        return redirect(url_for('loginForm'))


@app.route("/createOrder", methods=['GET', 'POST'])
def createOrder():
    isAdmin = isUserAdmin()
    totalsum = request.args.get('total')
    email, username, ordernumber, address, fullname, phonenumber = extractOrderdetails(request, totalsum)
    #if email:
     #   sendEmailconfirmation(email, username, ordernumber, phonenumber)

    return render_template("checkout2.html", email=email, username=username, ordernumber=ordernumber,
                                   address=address, fullname=fullname, phonenumber=phonenumber, isAdmin=isAdmin)


@app.route("/seeTrends", methods=['GET', 'POST'])
def seeTrends():
    if isUserAdmin():
        isAdmin = True
        trendtype = str(request.args.get('trend'))
        #cur = mysql.connection.cursor()
        '''
        if(trendtype=="least"):
            cur.execute("SELECT ordered_product.productid, sum(ordered_product.quantity) AS TotalQuantity,product.product_name FROM \
                           ordered_product,product where ordered_product.productid=product.productid GROUP BY productid \
                               ORDER BY TotalQuantity ASC ")
        else:
            trendtype="most"
            cur.execute("SELECT ordered_product.productid, sum(ordered_product.quantity) AS TotalQuantity,product.product_name FROM \
                    ordered_product,product where ordered_product.productid=product.productid GROUP BY productid \
                        ORDER BY TotalQuantity DESC ")
        '''

        products2 = db.session.query(OrderedProduct, Product) \
        .with_entities(func.sum(OrderedProduct.quantity).label('TotalQuantity')) \
        .join(Product, Product.productid==OrderedProduct.productid) \
        .add_column(Product.productid) \
        .add_column(Product.product_name) \
        .order_by(func.sum(OrderedProduct.quantity).amount.desc()) \
        .all()


        #products = cur.fetchall()
        #cur.close()
        x = []
        y = []
        for item in products2:
            #x.append(item['product_name'])
            y.append(item['TotalQuantity'])

        my_plot_div = plot([go.Bar(x=x, y=y)], output_type='div')

        return render_template('trends.html',
                               div_placeholder=Markup(my_plot_div),trendtype=trendtype, isAdmin=isAdmin
                               )
    return redirect(url_for('index'))

@app.route("/contact")
def contact():
    isAdmin = isUserAdmin()
    return render_template("contact.html", isAdmin=isAdmin)
