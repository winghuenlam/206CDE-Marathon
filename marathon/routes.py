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
from marathon import cur


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
        error, msg = extractAndPersistUserDataFromForm(request)
        if error == True:
            return render_template("register.html", registermsg=msg, registererror=error)
        else:
            return redirect(url_for('index'))

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


@app.route("/displayGenderCategory")
def displayGenderCategory():
    isAdmin = isUserAdmin()
    categoryId = request.args.get("categoryId")
    genderId = request.args.get("genderId")

    productDetails = Product.query.join(ProductCategory, Product.productid == ProductCategory.productid) \
        .join(ProductGender, Product.productid == ProductGender.productid) \
        .join(Category, Category.categoryid == ProductCategory.categoryid) \
        .join(Gender, Gender.genderid == ProductGender.genderid) \
        .filter(Gender.genderid == int(genderId)) \
        .filter(Category.categoryid == int(categoryId)) \
        .filter(ProductGender.genderid == int(genderId)) \
        .filter(ProductCategory.categoryid == int(categoryId)) \
        .all()


    gender, category = getGenderCategory()
    genderName = Gender.query.with_entities(Gender.gender_name).filter(Gender.genderid == genderId).first()
    categoryName = Category.query.with_entities(Category.category_name).filter(Category.categoryid == categoryId).first()

    products = massageItemData(productDetails)
    return render_template('gender_category_products.html', products=products, 
                            productDetails=productDetails, gender=gender, category=category, genderName=genderName[0],
                           categoryName=categoryName[0], isAdmin=isAdmin)


@app.route("/displayGender")
def displayGender():
    isAdmin = isUserAdmin()
    genderId = request.args.get("genderId")

    productDetailsByGenderId = Product.query.join(ProductGender, Product.productid == ProductGender.productid) \
        .join(Gender, Gender.genderid == ProductGender.genderid) \
        .add_columns(Product.productid, Product.product_name, Product.regular_price, Product.discounted_price,
                     Product.image, Product.image2, Gender.gender_name) \
        .filter(Gender.genderid == int(genderId)) \
        .all()

    genderName = Gender.query.with_entities(Gender.gender_name).filter(Gender.genderid == int(genderId)).first()

    gender, category = getGenderCategory()

    genderName = Gender.query.with_entities(Gender.gender_name).filter(Gender.genderid == genderId).first()
    products = massageItemData(productDetailsByGenderId)
    #products = Product.query.all()
    return render_template('gender_products.html', products=products, gender=gender, genderName=genderName[0], category=category, isAdmin=isAdmin)


@app.route("/addToCart", methods=['POST'])
def addToCart():
    if isUserLoggedIn():
        productId = int(request.args.get('productId'))
        sizeChoice = request.form['size']

        # Using Flask-SQLAlchmy SubQuery
        extractAndPersistKartDetailsUsingSubquery(productId, sizeChoice)

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

        orderDetails = db.session.query(Order, OrderedProduct, Product, Size) \
        .join(OrderedProduct, Order.orderid==OrderedProduct.orderid) \
        .join(Product, Product.productid==OrderedProduct.productid) \
        .join(Size, Size.productid==OrderedProduct.productid) \
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
        #cur.execute('SELECT category.categoryid, category.category_name, COUNT(product_category.productid) as noOfProducts FROM category LEFT JOIN product_category ON category.categoryid = product_category.categoryid GROUP BY category.categoryid, category.category_name');
        #categories = cur.fetchall()
        #cur.close()

        categories = Category.query.with_entities(Category.categoryid, Category.category_name) \
        .outerjoin(ProductCategory, ProductCategory.categoryid == Category.categoryid) \
        .add_columns(func.count(ProductCategory.productid).label('noOfProducts')).group_by(Category.categoryid, Category.category_name).all()


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
        #products = Product.query.all()
        products = Product.query.with_entities(Product.productid, Product.product_name, Product.regular_price, Product.discounted_price) \
        .join(Size, Product.productid == Size.productid) \
        .add_columns(func.sum(Size.quantity).label('productQty')) \
        .group_by(Product.productid, Product.product_name, Product.regular_price, Product.discounted_price).all()
        print(products)
        return render_template('adminProducts.html', products=products, isAdmin=isAdmin)
    return redirect(url_for('index'))

@app.route("/products", methods=['GET'])
def products():
    isAdmin = isUserAdmin()
    products = Product.query.all()
    gender, category = getGenderCategory()
    return render_template('products.html', products=products, gender=gender, isAdmin=isAdmin, category=category)

@app.route("/admin/products/new", methods=['GET', 'POST'])
def addProduct():
    if isUserAdmin():
        isAdmin = True
        form = addProductForm()
        form.category.choices = [(row.categoryid, row.category_name) for row in Category.query.all()]
        form.gender.choices = [(row.genderid, row.gender_name) for row in Gender.query.all()]
        product_icon1 = "comingsoon.png" #safer way in case the image is not included in the form
        product_icon2 = "comingsoon.png" #safer way in case the image is not included in the form
        if form.validate_on_submit():
            if form.image1.data:
                product_icon1 = save_picture(form.image1.data)
            if form.image2.data:
                product_icon2 = save_picture(form.image2.data)
            product = Product(product_name=form.productName.data, description=form.productDescription.data, image=product_icon1, image2=product_icon2, discounted_price=form.discountedPrice.data, regular_price=form.productPrice.data)
            print(product_icon2)
            db.session.add(product)
            db.session.commit()
            product_category = ProductCategory(categoryid=form.category.data, productid=product.productid)
            product_gender = ProductGender(genderid=form.gender.data, productid=product.productid)
            db.session.add(product_category)
            db.session.commit()
            db.session.add(product_gender)
            db.session.commit()


            sizes = []
            sizeAvailable = form.sizeAvailable.data.split(",")
            for i in range(len(sizeAvailable)):
                sizes.append(sizeAvailable[i])

            productid = Product.query.with_entities(Product.productid).order_by(Product.productid.desc()).first()

            for size in sizes:
                add_size = Size(size_name=size, productid=productid[0], quantity="")
                db.session.add(add_size)
                db.session.commit()

                #print(size)
            flash(f'Product {form.productName} added successfully', 'success')


            return (redirect(url_for('addProduct_quantity', productid=productid[0])))
        return render_template("addProduct.html", form=form, legend="New Product", isAdmin=isAdmin)
    return redirect(url_for('index'))


@app.route("/admin/products/new/quantity/<int:productid>")
def addProduct_quantity(productid):
    if isUserAdmin():
        isAdmin = True
        sizes = getProductSizes(productid)
        return render_template("addProductQty.html", productid=productid, sizes=sizes, isAdmin=isAdmin)

    return redirect(url_for('index'))


@app.route("/admin/products/new/quantity/submit", methods=['GET', 'POST'])
def addProduct_quantity_submit():
    if isUserAdmin():
        isAdmin = True
        productid = request.args.get('productid')
        #sizes = Size.query.with_entities(Size.sizeid, Size.quantity).filter(Size.productid == int(productid)).all()
        sizes = db.session.query(Size).filter(Size.productid == int(productid))

        if request.method == 'POST':
            for size in sizes:
                Qty = request.form[str(size.sizeid)]
                size.quantity = int(Qty)

            db.session.commit()

        return redirect(url_for('getProducts'))



@app.route("/product/<int:product_id>", methods=['GET'])
def product(product_id):
    isAdmin = isUserAdmin()
    #productid = request.args.get('productId')#for add cart
    product, sizes = getProductDetails(product_id)#for add cart
    productQty = Size.query.with_entities(Size.size_name, Size.quantity).filter(Size.productid == product_id).all()
    return render_template('products_detail.html', product=product, isAdmin=isAdmin, sizes=sizes, productQty=productQty)
   


@app.route("/admin/product/<int:product_id>", methods=['GET'])
def admin_product(product_id):
    if isUserAdmin():
        isAdmin = True
        loggedIn, firstName, noOfItems, userid = getLoginUserDetails()
        product, sizeAvailable = getProductDetails(product_id)#for add cart
        productQty = Size.query.with_entities(Size.size_name, Size.quantity).filter(Size.productid == product_id).all()

        return render_template('admin_products_detail.html', product=product, loggedIn=loggedIn,
                           firstName=firstName,
                           noOfItems=noOfItems, isAdmin=isAdmin, productQty=productQty)
    return redirect(url_for('index'))
  

@app.route("/admin/product/<int:product_id>/update", methods=['GET', 'POST'])
def update_product(product_id):
    if isUserAdmin():
        isAdmin = True
        product = Product.query.get_or_404(product_id)
        showdbPoductSizes, dbPoductSizes = formatDBProductSize(product_id)

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

            input_sizes = []
            input_sizeAvailable = form.sizeAvailable.data.split(",")
            for i in range(len(input_sizeAvailable)):
                input_sizes.append(input_sizeAvailable[i])

            #compare dbPoductSizes vs. input_sizes
            add_size_list = []
            del_size_list = []
            for input_item in input_sizes:
                if input_item not in dbPoductSizes:
                    add_size_list.append(input_item)
            for db_item in dbPoductSizes:
                if db_item not in input_sizes:
                    del_size_list.append(db_item)
            # add and del size record
            for add_item in add_size_list:
                add_db = Size(size_name=add_item, productid=product_id, quantity="")
                db.session.add(add_db)
                db.session.commit()
            for del_item in del_size_list:
                Size.query.filter_by(productid=product_id, size_name=del_item).delete()
            db.session.commit()

            flash('This product has been updated!', 'success')
            return redirect(url_for('addProduct_quantity', productid=product_id))
        elif request.method == 'GET':

            form.productName.data = product.product_name
            form.productDescription.data = product.description
            form.productPrice.data = product.regular_price
            form.discountedPrice.data = product.discounted_price
            form.sizeAvailable.data = showdbPoductSizes

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

        #cur.execute("SELECT u.fname, u.lname, u.email, u.phone, COUNT(o.orderid) as noOfOrders FROM `user` u LEFT JOIN `order` o ON u.userid = o.userid WHERE u.usertype = 'customer' GROUP BY u.userid")
        #users = cur.fetchall()
        #cur.close()

        users = User.query.with_entities(User.userid, User.fname, User.lname, User.email, User.phone).filter(User.usertype == 'customer') \
        .outerjoin(Order, Order.userid == User.userid) \
        .add_columns(func.count(Order.orderid).label('noOfOrders')).group_by(User.userid, User.fname, User.lname, User.email, User.phone).all()

        return render_template('adminUsers.html', users= users, isAdmin=isAdmin)
    return redirect(url_for('index'))


@app.route("/admin/orders")
def getOrders():
    if isUserAdmin():
        isAdmin = True

        orderDetails = db.session.query(Order, OrderedProduct, Product, Size) \
        .join(OrderedProduct, Order.orderid==OrderedProduct.orderid) \
        .join(Product, Product.productid==OrderedProduct.productid) \
        .join(Size, Size.productid==OrderedProduct.productid) \
        .all()

        #products = Product.query.all()
        return render_template('adminOrders.html', orderDetails=orderDetails, isAdmin=isAdmin)
    return redirect(url_for('index'))


@app.route("/removeFromCart")
def removeFromCart():
    if isUserLoggedIn():
        productId = int(request.args.get('productId'))
        sizeId = int(request.args.get('sizeId'))
        removeProductFromCart(productId, sizeId)
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
    email, username, ordernumber, address, full_name, phonenumber = extractOrderdetails(request, totalsum)
    #if email:
     #   sendEmailconfirmation(email, username, ordernumber, phonenumber)

    return render_template("checkout2.html", email=email, username=username, ordernumber=ordernumber,
                                   address=address, fullname=full_name, phonenumber=phonenumber, isAdmin=isAdmin)


@app.route("/seeTrends", methods=['GET', 'POST'])
def seeTrends():
    if isUserAdmin():
        isAdmin = True
        trendtype = str(request.args.get('trend'))
        #cur = mysql.connection.cursor()
        
        if(trendtype=="least"):
            cur.execute("SELECT ordered_product.productid, sum(ordered_product.quantity) AS TotalQuantity,product.product_name \
                            FROM  ordered_product INNER JOIN product ON ordered_product.productid=product.productid  \
                            GROUP BY ordered_product.productid, ordered_product.quantity,product.product_name \
                             ORDER BY TotalQuantity ASC ")
        else:
            trendtype="most"
            cur.execute("SELECT ordered_product.productid, sum(ordered_product.quantity) AS TotalQuantity,product.product_name \
                            FROM  ordered_product INNER JOIN product ON ordered_product.productid=product.productid  \
                            GROUP BY ordered_product.productid, ordered_product.quantity,product.product_name \
                             ORDER BY TotalQuantity DESC ")

        products = cur.fetchall()
        x = []
        y = []

        for item in products:
            x.append(item[2])

            y.append(item[1])

        my_plot_div = plot([go.Bar(x=x, y=y)], output_type='div')

        return render_template('trends.html',
                               div_placeholder=Markup(my_plot_div),trendtype=trendtype, isAdmin=isAdmin
                               )
    return redirect(url_for('index'))

@app.route("/contact")
def contact():
    isAdmin = isUserAdmin()
    return render_template("contact.html", isAdmin=isAdmin)
