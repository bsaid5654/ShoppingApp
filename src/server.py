import sqlite3 as sql
from wtforms import Form, BooleanField, TextField, PasswordField, validators, IntegerField
from wtforms.fields.html5 import EmailField
from passlib.hash import sha256_crypt
from flask import Flask, redirect, url_for, render_template, request, flash, session


app=Flask(__name__)
app.secret_key="CSVK"


@app.route("/")
@app.route("/home")
def home():
    create_table()
    if 'logged_in' in session:
        if session['usertype'] == 'customer':
            with sql.connect('database.db') as con:
                cur=con.cursor()
                cur.execute('select Following from Follow where Follower = ?',[session['username']])
                followings = cur.fetchall()
                recProducts = []
                for following in followings:
                    cur.execute('select * from buyProducts where CustomerName = ? ',[following[0]])
                    srecp= cur.fetchall()
                    for recp in srecp:
                        cur.execute("select * from products where UploadedBy = ? and Size = ? and Name  = ?",[recp[1],recp[5],recp[0]])
                        product = cur.fetchone()
                        if product is not None:
                            recProducts.append(product)
                if recProducts != []:
                    return render_template("Homepage.html",rows = recProducts)
                else:
                    cur.execute('select * from products')
                    rows = cur.fetchall()
                    return render_template("Homepage.html",rows = rows)
        elif session['usertype'] == 'seller':
            return render_template('Homepage_seller.html')
        elif session['usertype'] == 'Admin':
                return redirect(url_for('admin_page'))
    else:
        session['usertype'] = 'Guest'
        session['username'] =  'Guest123'
        with sql.connect('database.db') as con:
            sqlQuery = "select * from products"
            cur=con.cursor()
            cur.execute(sqlQuery)
            rows = cur.fetchall()
            return render_template("Homepage.html", rows = rows)


@app.route('/shop')
def shop():
    with sql.connect('database.db') as con:
        sqlQuery = "select * from products"
        cur=con.cursor()
        cur.execute(sqlQuery)
        rows = cur.fetchall()
    return render_template('shop.html',rows = rows)


@app.route("/register", methods=['GET', 'POST'])
def register(checks = "None"):
    if 'logged_in' in session:
        return redirect(url_for("home"))
    else:
        form=RegisterForm_customers(request.form)
        if request.method == "POST" and form.validate():
            with sql.connect('database.db') as con:
                username = form.username.data
                email = form.email.data
                address =  form.address.data
                phone = form.phone.data
                password = sha256_crypt.encrypt((str(form.password.data)))
                sqlQuery = "select Username from bcustomers where Username ='" + username + "';"
                cur=con.cursor()
                sqlQuery1 = "select Username from bsellers where Username ='" + username + "';"
                cur.execute(sqlQuery)
                row_cus = cur.fetchone()
                cur.execute(sqlQuery1)
                row_sell = cur.fetchone()
                sqlQuery = "select Email_ID from bcustomers where Email_ID ='" + email + "';"
                cur.execute(sqlQuery)
                row1 = cur.fetchone()
                if row_cus:
                    return render_template('login_customer.html', form=form, checks="presentuser", type="Register")
                elif row_sell:
                    return render_template('login_customer.html', form=form, checks="presentuser", type="Register")
                elif row1:
                    return render_template('login_customer.html', form=form, checks="presentemail", type="Register")
                else:
                    cur.execute("INSERT INTO customers (Username, Email_ID, Password, Address, Phone)  VALUES (?,?,?,?,?)",(username, email, password, address, phone))
                    cur.execute("INSERT INTO bcustomers (Username, Email_ID, Password, Address, Phone)  VALUES (?,?,?,?,?)",(username, email, password, address, phone))
                    con.commit()
                    flash('Registered successfully...!!!!','success')
                    return redirect(url_for('home'))
        elif request.method == "POST":
            return render_template("login_customer.html", form = form, checks="Invalid", type="Register")
        else:
            return render_template("login_customer.html", form = form, checks="None", type="Register")


@app.route("/login",methods=['GET','POST'])
def login():
    form = LoginForm(request.form)
    if 'logged_in' in session:
        return redirect(url_for("home"))
    else:
        create_table()
        if request.method == "POST" and form.validate():
            with sql.connect('database.db') as con:
                username = form.username.data
                password = form.password.data
                cur = con.cursor()
                result = cur.execute("select * from customers where Username ='" + username + "';")
                row = cur.fetchone()
                if row is not None:
                    Password_req = row[2]
                    if sha256_crypt.verify(password, Password_req):
                        session['logged_in'] = True
                        session['username'] = username
                        session['usertype'] = 'customer'
                        if username == "admin_bcskd":
                            session['usertype'] = 'Admin'
                            return redirect(url_for('admin_page'))
                        else:
                            return redirect(url_for('home'))
                    else:
                        return render_template('login_customer.html', checks = "Invalid", type = "Login")

                else:
                    return render_template('login_customer.html', checks = "Invalid", type = "Login")
        elif request.method == "POST":
            return render_template('login_customer.html', checks = "Invalid", type = "Login")
        else:
            return render_template('login_customer.html', checks = "None", type = "Login")


                     ######   CART   ######


@app.route('/cart')
def cart():
    if 'logged_in' in session:
        if session['usertype'] == 'seller' or session['usertype'] == 'Admin':
            return redirect(url_for('seller_home'))
        else:
            with sql.connect('database.db') as con:
                sqlQuery=("select * from cart where CustomerName ='"+ session['username'] +"';")
                cur = con.cursor()
                cur.execute(sqlQuery)
                rows = cur.fetchall()
                row_products=[]
                row_checks=[]
                if rows != []:
                    i=0
                    ans1=0
                    for row in rows:
                        cur.execute("select * from products where Name='"+ row[1] +"' and UploadedBy = '"+ row[2] +"';")
                        ans=cur.fetchone()
                        if ans is not None:
                            row_products.append(ans)
                            temp = row[4] * ans[4]
                            ans1 = ans1 + temp
                            temp1=[]
                            temp1.append(row[4])
                            temp1.append(temp)
                            row_checks.append(temp1)
                    length=len(row_products)
                    if ans1 < 900:
                        shipping_tax = 100
                    else:
                        shipping_tax = 0
                    totalm = ans1 + shipping_tax
                    print ("yes")
                    print (totalm, shipping_tax)
                    return render_template('cart.html',row_product = row_products, length = length , ans = ans1, row_checks = row_checks, tax = shipping_tax, tm = totalm)
                else:
                    return render_template('cart.html',row_product = None)
    else:
        with sql.connect('database.db') as con:
            sqlQuery=("select * from cart where CustomerName ='"+ session['username'] +"';")
            cur = con.cursor()
            cur.execute(sqlQuery)
            rows = cur.fetchall()
            row_products=[]
            row_checks=[]
            if rows != []:
                i=0
                ans1=0
                for row in rows:
                    cur.execute("select * from products where Name='"+ row[1] +"' and UploadedBy = '"+ row[2] +"' and Size = ?",[row[3]])
                    ans=cur.fetchone()
                    if ans is not None:
                        row_products.append(ans)
                        temp = row[4] * ans[4]
                        ans1 = ans1 + temp
                        temp1=[]
                        temp1.append(row[4])
                        temp1.append(temp)
                        row_checks.append(temp1)
                length=len(row_products)
                if ans1 < 900:
                    shipping_tax = 100
                else:
                    shipping_tax = 0
                totalm = ans1 + shipping_tax
                print ("yes")
                print (totalm, shipping_tax)
                return render_template('cart.html',row_product = row_products, length = length , ans = ans1, row_checks = row_checks,type = 'feedback', tax = shipping_tax, tm = totalm)
            else:
                return render_template('cart.html', row_product = None,type = 'feedback')


@app.route('/addQuantity/<proName>/<sellerName>/<int:size>/<customerName>')
def addQuantity(proName = None, sellerName = None ,customerName = None, size = None):
    if 'logged_in' in session:
        if session['username'] == customerName :
            with sql.connect('database.db') as con:
                cur=con.cursor()
                cur.execute("select * from cart where ProductName = '"+ proName +"' and SellerName ='"+ sellerName +"' and CustomerName = '"+ customerName +"' and Size = ?",[size])
                row = cur.fetchone()
                cur.execute("select * from products where Name = '"+ proName +"' and UploadedBy ='"+ sellerName +"' and Size = ?",[size])
                row1 = cur.fetchone()
                ans = row[4] + 1
                if ans > row1[5]:
                    ans = row1[5]
                cur.execute("UPDATE 'cart' SET 'Quantity' = ? WHERE ProductName = ? and SellerName = ? and CustomerName = ? and Size = ?",[ans,proName,sellerName,customerName,size])
                return redirect(url_for('cart'))
    else:
        if session['username'] == customerName:
            with sql.connect('database.db') as con:
                cur=con.cursor()
                cur.execute("select * from cart where ProductName = '"+ proName +"' and SellerName ='"+ sellerName +"' and CustomerName = '"+ customerName +"' and Size = ?",[size])
                row = cur.fetchone()
                cur.execute("select * from products where Name = '"+ proName +"' and UploadedBy ='"+ sellerName +"' and Size = ?",[size])
                row1 = cur.fetchone()
                ans = row[4] + 1
                if ans > row1[5]:
                    ans = row1[5]
                cur.execute("UPDATE 'cart' SET 'Quantity' = ? WHERE ProductName = ? and SellerName = ? and CustomerName = ? and Size = ?",[ans,proName,sellerName,customerName,size])
                return redirect(url_for('cart'))


@app.route('/reduceQuantity/<proName>/<sellerName>/<int:size>/<customerName>')
def reduceQuantity(proName = None, sellerName = None ,customerName = None, size = None):
    if 'logged_in' in session:
        if session['username'] == customerName :
            with sql.connect('database.db') as con:
                cur=con.cursor()
                cur.execute("select * from cart where ProductName = '"+ proName +"' and SellerName ='"+ sellerName +"' and CustomerName = '"+ customerName +"' and Size = ?",[size])
                row = cur.fetchone()
                ans = row[4] - 1
                if ans <= 0:
                    ans = 1;
                cur.execute("UPDATE 'cart' SET 'Quantity' = ? WHERE ProductName = ? and SellerName = ? and CustomerName = ? and Size = ?",[ans,proName,sellerName,customerName,size])
                return redirect(url_for('cart'))
    else:
        if session['username'] == customerName :
            with sql.connect('database.db') as con:
                cur=con.cursor()
                cur.execute("select * from cart where ProductName = '"+ proName +"' and SellerName ='"+ sellerName +"' and CustomerName = '"+ customerName +"' and Size = ?",[size])
                row = cur.fetchone()
                ans = row[4] - 1
                if ans <= 0:
                    ans = 1;
                cur.execute("UPDATE 'cart' SET 'Quantity' = ? WHERE ProductName = ? and SellerName = ? and CustomerName = ? and Size = ?",[ans,proName,sellerName,customerName,size])
    return redirect(url_for('cart'))


@app.route('/addcart/<proName>/<sellerName>/<int:size>')
def addcart(proName = None, sellerName = None, size = None):
    if proName is None or sellerName is None or size is None:
        return redirect(url_for('products'))
    else:
        with sql.connect('database.db') as con:
            cur = con.cursor()
            cur.execute("select * from products where Name ='"+ proName +"' and UploadedBy = '" + sellerName + "' and Size = ?",[size])
            row = cur.fetchone()
            if row is not None:
                print("yes")
                cur.execute("INSERT INTO cart (CustomerName, ProductName, SellerName, Size, Quantity) VALUES (?,?,?,?,?)",(session['username'],row[0],row[6],row[2],1))
                return redirect(url_for('products',proName = row[0], sellerName = row[6], size = row[2]))
            else:
                return redirect(url_for('products'))


@app.route('/removecart/<proname>/<sellername>/<int:size>')
def removecart(proname = None, sellername = None, size = None):
    if proname is None or sellername is None or size is None:
        return redirect(url_for('cart'))
    else:
        with sql.connect('database.db') as con:
            cur = con.cursor()
            cur.execute("select * from cart where ProductName = '"+ proname +"' and SellerName = '" + sellername + "' and CustomerName ='" + session['username'] + "' and Size = ?",[size])
            row = cur.fetchone()
            if row is not None:
                cur.execute("DELETE FROM cart where (CustomerName = '"+ session['username'] +"' AND ProductName = '"+ proname +"' AND SellerName = '"+ sellername +"' AND Size = ?)",[size])
            return redirect(url_for('cart'))

                    #######  LOGOUT  ######


@app.route('/logout')
def logout():
    if 'logged_in' in session:
        session.pop('username',None)
        session.pop('usertype',None)
        session.pop('logged_in',None)
    return redirect(url_for('home'))


@app.route('/seller_home')
def seller_home():
    if 'logged_in' in session:
        if session['usertype'] == 'seller':
            return render_template('Homepage_seller.html', type = 'home')
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))


@app.route('/seller_login',methods=["GET","POST"])
def seller_login():
    form = LoginForm(request.form)
    if 'logged_in' in session:
        return redirect(url_for("seller_home"))
    else:
        if request.method == "POST" and form.validate():
            with sql.connect('database.db') as con:
                username = form.username.data
                password = form.password.data
                cur = con.cursor()
                result = cur.execute("select * from sellers where Username ='" + username + "';")
                row = cur.fetchone()
                if row is not None:
                    Password_req = row[6]

                    if sha256_crypt.verify(password, Password_req):
                        session['logged_in'] = True
                        session['username'] = username
                        session['usertype'] = 'seller'
                        return redirect(url_for('seller_home'))
                    else:
                        return render_template('login_customer.html', checks = "Invalid", type = "Seller_Login")
                else:
                    return render_template("login_customer.html", checks = "Invalid", type = "Seller_Login")
        elif request.method == "POST":
            return render_template('login_customer.html', checks = "Invalid", type = "Seller_Login")
        else:
            return render_template('login_customer.html', checks = "None", type = "Seller_Login")

    return render_template('login_customer.html', type = "Seller_Login", checks = "None")


@app.route('/seller_register',methods=["GET","POST"])
def seller_register(checks = "None"):
    form=RegisterForm_sellers(request.form)
    if 'logged_in' in session:
        if session['usertype'] == 'seller':
            return redirect(url_for('seller_home'))
        else:
            return redirect(url_for("home"))
    else:
        create_table()
        if request.method == "POST" and form.validate():
            with sql.connect('database.db') as con:
                name = form.name.data
                username = form.username.data
                email = form.email.data
                phone_number = form.phone.data
                address = form.address.data
                pincode = form.pincode.data
                password = sha256_crypt.encrypt((str(form.password.data)))
                sqlQuery = "select Username from bsellers where Username ='" + username + "';"
                sqlQuery1 = "select Username from bcustomers where Username ='" + username + "';"
                cur=con.cursor()
                cur.execute(sqlQuery)
                row_sell = cur.fetchone()
                cur.execute(sqlQuery1)
                row_cus = cur.fetchone()
                sqlQuery = "select Email_ID from bsellers where Email_ID ='" + email + "';"
                cur.execute(sqlQuery)
                row1 = cur.fetchone()
                print (username + " " + email + " " + password)
                if row_sell :
                    return render_template('login_customer.html', form = form, checks = "presentuser", type = "Seller_Register")
                elif row_cus:
                    return render_template('login_customer.html', form = form, checks = "presentuser", type = "Seller_Register")
                elif row1:
                    return render_template('login_customer.html', form = form, checks = "presentemail", type = "Seller_Register")
                else:
                    cur.execute("INSERT INTO sellers (Name, Username, Email_ID, Address, Pincode, Phone_no , Password)  VALUES (?,?,?,?,?,?,?)",(name,username, email, address,pincode, phone_number,password))
                    cur.execute("INSERT INTO bsellers (Name, Username, Email_ID, Address, Pincode, Phone_no , Password)  VALUES (?,?,?,?,?,?,?)",(name,username, email, address,pincode, phone_number,password))
                    con.commit()
                    return redirect(url_for('home'))
        elif request.method == "POST":
            return render_template("login_customer.html", form = form, checks="Invalid", type="Seller_Register")
        else:
            return render_template("login_customer.html", form = form, checks="None", type="Seller_Register")

    return render_template('login_customer.html', type = "Seller_Register", checks = "None")


@app.route('/admin_page')
def admin_page():
    if 'logged_in' in session:
        if session['username'] == "admin_bcskd":
            with sql.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("select * from buyProducts")
                rows = cur.fetchall()
                ans = 0
                tax = 0
                for row in rows:
                    ans = ans + row[4]*row[3]
                cur.execute("select * from charges")
                cols = cur.fetchall()
                for col in cols:
                    tax = tax + col[1]
            return render_template('Homepage_admin.html', rows = rows, ans = ans, tax =  tax)
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))


@app.route('/addproducts',methods = ['GET','POST'])
def addproducts():
    if 'logged_in' in session:
        if session['usertype'] == 'seller' or session['usertype'] == 'Admin':
            form = AddProducts(request.form)
            if request.method == 'POST' and form.validate():
                with sql.connect('database.db') as con:
                    productname = form.name.data
                    brand = form.brand.data
                    size =  form.size.data
                    actual_cost = form.mrp.data
                    selling_at = form.sellingAt.data
                    no_of_items = form.quantity.data
                    added_by = session['username']
                    img1 = form.Image1.data
                    img2 = form.Image2.data
                    img3 = form.Image3.data
                    cur = con.cursor()
                    cur.execute("select * from products WHERE Name = ? AND UploadedBy = ? AND Size = ? AND Brand = ?",[productname,added_by,size,brand])
                    row = cur.fetchone()
                    if row is None:
                        cur.execute('INSERT INTO products (Name, Brand, Size, MRP, SellingAt, Quantity, UploadedBy, Sold, Img1, Img2, Img3)  VALUES (?,?,?,?,?,?,?,"no",?,?,?)',(productname, brand, size, actual_cost,selling_at, no_of_items, added_by, img1, img2, img3))
                    else:
                        temp = no_of_items + row[5]
                        cur.execute("UPDATE 'products' SET Quantity = ? WHERE Name = ? AND UploadedBy = ? AND Size = ? AND  Brand = ?",[temp,productname,added_by,size,brand])
                    if session['usertype'] == 'seller':
                        return render_template('add_products.html', type = 'addproducts', form = form)
                    elif session['usertype'] == 'Admin':
                        return render_template('add_products.html', type = 'addproducts', form = form)

            else:
                if session['usertype'] == 'seller':
                    return render_template('add_products.html', type = 'addproducts', form = form)
                elif session['usertype'] == 'Admin':
                    return render_template('add_products.html', type = 'addproducts', form = form)
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))


@app.route('/products/<proName>/<sellerName>/<int:size>')
def products(proName = None,sellerName = None, size = None):
    if proName is None:
        return redirect(url_for('home'))
    else:
        with sql.connect('database.db') as con:
            cur = con.cursor()
            cur.execute(" select * from products where Name ='"+ proName +"' and UploadedBy = '"+ sellerName +"' and Size = ?;",[size])
            row = cur.fetchone()
            cur.execute(" select * from feedback where ProductName ='"+ proName +"' and SellerName = '"+ sellerName +"' and Size = ?;",[size])
            fandr=cur.fetchall()
            ratings=0
            lor=0
            if fandr != []:
                for rating in fandr:
                    ratings = ratings + rating[5]
                lor=len(fandr)
                ratings = ratings/lor

            if row is not None:
                cur.execute("select * from cart where CustomerName ='"+ session['username'] +"' and ProductName ='" + proName + "' and SellerName ='" + sellerName + "' and Size = ?",[size])
                checking_cart = cur.fetchone()
                if checking_cart is None:
                    return render_template('products.html', row = row, check_cart = "no", ratings = ratings, lor = lor, fandr = fandr)
                else:
                    return render_template('products.html', row = row, check_cart = "yes",  ratings = ratings, lor = lor, fandr = fandr)
            else:
                return render_template('products.html', row = None)


@app.route('/search', methods=["POST","GET"])
def search():
    if request.method == 'POST':
        with sql.connect('database.db') as con:
            if 'logged_in' in session:
                if session['usertype'] == 'seller':
                    return redirect(url_for('seller_home'))
            cur = con.cursor()
            form = SearchForm(request.form)
            searchName = form.searchName.data
            cur.execute("select * from products where Name like ?", ('%'+searchName+'%',))
            rows = cur.fetchall()
            cur.execute("select * from products where Brand like ?", ('%'+searchName+'%',))
            rows1 = cur.fetchall()
            if rows != []:
                return render_template('search.html', products = rows)
            elif rows1 != []:
                return render_template('search.html', products = rows1)
            else:
                return render_template('search.html', products = None)


@app.route('/search_seller', methods=["POST","GET"])
def search_seller():
    if request.method == 'POST':
        if 'logged_in' in session:
            if session['usertype'] == 'seller':
                with sql.connect('database.db') as con:
                    cur = con.cursor()
                    form = SearchForm(request.form)
                    searchName = form.searchName.data
                    cur.execute("select * from products where UploadedBy = '"+ session['username'] +"' and Name like ?", ('%'+searchName+'%',))
                    rows = cur.fetchall()
                    cur.execute("select * from products where UploadedBy = '"+ session['username'] +"' and Brand like ?", ('%'+searchName+'%',))
                    rows1 = cur.fetchall()
                    if rows != []:
                        return render_template('search.html', products = rows)
                    elif rows1 != []:
                        return render_template('search.html', products = rows1)
                    else:
                        return render_template('search.html', products = None)


@app.route('/updateProfile',methods = ["GET", "POST"])
def updateProfile():
    form = UpdateForm_customers(request.form)
    with sql.connect('database.db') as con:
        if 'logged_in' in session:
            if session['usertype'] == 'customer':
                cur = con.cursor()
                if request.method == "POST":
                    address = form.address.data
                    phone = form.phone.data
                    print (address)
                    cur.execute("UPDATE 'customers' SET 'Address' = ? , 'Phone' = ? WHERE Username = ?",[address, phone, session['username']])
                    return redirect(url_for('home'))
                else:
                    cur.execute("select * from customers where Username = '"+ session["username"] +"'")
                    row  = cur.fetchone()
                    return render_template('editprofile.html', profileData = row,type = 'editProfile')
            else:
                return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))


@app.route('/updateProfile_seller',methods = ["GET", "POST"])
def updateProfile_seller():
    form = UpdateForm_sellers(request.form)
    with sql.connect('database.db') as con:
        if 'logged_in' in session:
            if session['usertype'] == 'seller':
                cur = con.cursor()
                if request.method == "POST":
                    name = form.name.data
                    address = form.address.data
                    pincode = form.pincode.data
                    phone = form.phone.data
                    print (address)
                    cur.execute("UPDATE 'sellers' SET 'Address' = ? , 'Phone_no' = ?, 'Name' = ?, 'Pincode' = ? WHERE Username = ?",[address, phone, name, pincode, session['username']])
                    return redirect(url_for('home'))
                else:
                    cur.execute("select * from sellers where Username = '"+ session["username"] +"'")
                    row  = cur.fetchone()
                    return render_template('editprofile.html', profileData = row,type = 'editProfile')
            else:
                return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))


@app.route('/changePassword',methods = ["GET", "POST"])
def changePassword():
    if 'logged_in' in session:
        form = changePassword_form(request.form)
        if request.method == "POST":
            oldPassword = form.oldPassword.data
            newPassword = form.newPassword.data
            with sql.connect('database.db') as con:
                cur = con.cursor()
                if session['usertype'] == 'customer' or session['usertype'] == 'Admin':
                    cur.execute("select Password from customers WHERE Username = ?",[session['username']])
                    password_check = cur.fetchone()
                    if sha256_crypt.verify(oldPassword,password_check[0]):
                        newPassword = sha256_crypt.encrypt((str(newPassword)))
                        cur.execute("UPDATE 'customers' SET Password = ? WHERE Username = ?",[newPassword,session['username']] )
                        return redirect(url_for('home'))
                    else:
                        return render_template('changePassword.html', type ="WRONG")
                elif session['usertype'] == 'seller':
                    cur.execute("select Password from sellers WHERE Username = ?",[session['username']])
                    password_check = cur.fetchone()
                    if sha256_crypt.verify(oldPassword,password_check[0]):
                        newPassword = sha256_crypt.encrypt((str(newPassword)))
                        cur.execute("UPDATE 'sellers' SET Password = ? WHERE Username = ?",[newPassword,session['username']])
                        return redirect(url_for('home'))
                    else:
                        return render_template('changePassword.html', type ="WRONG", checks = 'Invalid')
        else:
            return render_template('changePassword.html')
    else:
        return redirect(url_for('home'))


@app.route('/checkout')
def checkout():
    with sql.connect('database.db') as con:
        create_table()
        if 'logged_in' in session:
            cur = con.cursor()
            cur.execute("select * from cart where CustomerName = '"+ session["username"] + "'")
            names = cur.fetchall()
            ans = 0
            if names != []:
                ans = 0
                for name in names:
                    change = 0
                    cur.execute("select * from products where UploadedBy = '"+ name[2] +"' and Name = '"+ name[1] +"' and Size = ?",[name[3]])
                    product = cur.fetchone()
                    change = product[5]-name[4]
                    if change == 0:
                        cur.execute("UPDATE 'products' SET 'Sold' = ? WHERE UploadedBy = ? AND Name = ? AND Size = ?",["Yes",name[2],name[1],name[3]])
                    print('Yes')
                    ans = ans + product[4]*name[4]
                    cur.execute("UPDATE 'products' SET 'Quantity' = ? WHERE UploadedBy = ? AND Name = ? AND Size = ?",[change,name[2],name[1],name[3]])
                    cur.execute("INSERT INTO buyProducts (CustomerName, SellerName, ProductName, Quantity, Cost, Size, Feedback, Img1, Img2, Img3) VALUES (?,?,?,?,?,?,?,?,?,?)",(session['username'], name[2], name[1], name[4],product[4],product[2],"No",product[8],product[9],product[10]))
                    cur.execute("INSERT INTO soldProducts (CustomerName, SellerName, ProductName, Quantity, Cost, Size) VALUES (?,?,?,?,?,?)",(session['username'], name[2], name[1], name[4],product[4], product[2]))
                    cur.execute("DELETE FROM cart WHERE CustomerName = ? AND SellerName = ? AND ProductName = ? AND Size = ?",[name[0],name[2],name[1],name[3]])
                print (ans)
                if ans < 900:
                    ans = 0
                    cur.execute('select * from charges where Username  = ?',[session['username']])
                    row = cur.fetchone()
                    if row is not None:
                        ans = 100 + row[1]
                        cur.execute("UPDATE charges SET charge  = ? where Username = ?",[ans,session['username']])
                    else:
                        cur.execute("INSERT INTO charges (Username,charge) VALUES (?,?)",(session['username'],ans))
                else:
                    ans = 0
                    cur.execute('select * from charges where Username  = ?',[session['username']])
                    row = cur.fetchone()
                    if row is not None:
                        ans = row[1]
                        cur.execute("UPDATE charges SET charge  = ? where Username = ?",[ans,session['username']])
                    else:
                        cur.execute("INSERT INTO charges (Username,charge) VALUES (?,?)",(session['username'],ans))

                return redirect(url_for('cart'))
            else:
                return redirect(url_for('cart'))
        else:
            return redirect(url_for('register_now'))


@app.route('/register_now',methods=["GET","POST"])
def register_now():
    if 'logged_in' in session:
        return redirect(url_for("home"))
    else:
        form=RegisterForm_customers(request.form)
        if request.method == "POST" and form.validate():
            with sql.connect('database.db') as con:
                username = form.username.data
                email = form.email.data
                address =  form.address.data
                phone = form.phone.data
                password = sha256_crypt.encrypt((str(form.password.data)))
                sqlQuery = "select Username from customers where Username ='" + username + "';"
                cur=con.cursor()
                sqlQuery1 = "select Username from sellers where Username ='" + username + "';"
                cur.execute(sqlQuery)
                row_cus = cur.fetchone()
                cur.execute(sqlQuery1)
                row_sell = cur.fetchone()
                sqlQuery = "select Email_ID from customers where Email_ID ='" + email + "';"
                cur.execute(sqlQuery)
                row1 = cur.fetchone()
                if row_cus:
                    return render_template('login_customer.html', form=form, checks="presentuser", type="Register_now")
                elif row_sell:
                    return render_template('login_customer.html', form=form, checks="presentuser", type="Register_now")
                elif row1:
                    return render_template('login_customer.html', form=form, checks="presentemail", type="Register_now")
                else:
                    cur.execute("INSERT INTO customers (Username, Email_ID, Password, Address, Phone)  VALUES (?,?,?,?,?)",(username, email, password, address, phone))
                    session['logged_in'] = True
                    session['username'] = username
                    session['usertype'] = 'customer'
                    cur.execute("select * from cart where CustomerName = ?",["Guest123"])
                    names = cur.fetchall()
                    if names != []:
                        for name in names:
                            print (name)
                            cur.execute("UPDATE 'cart' SET CustomerName = ? WHERE ProductName = ? AND SellerName = ? AND CustomerName = ?",[session["username"],name[1],name[2],name[0]])
                    return redirect(url_for('checkout'))
        elif request.method == "POST":
            return render_template("login_customer.html", form = form, checks="Invalid", type="Register_now")
        else:
            return render_template("login_customer.html", form = form, checks="None", type="Register_now")


@app.route('/login_now',methods=["GET","POST"])
def login_now():
    form = LoginForm(request.form)
    if 'logged_in' in session:
        return redirect(url_for("home"))
    else:
        create_table()
        if request.method == "POST" and form.validate():
            with sql.connect('database.db') as con:
                username = form.username.data
                password = form.password.data
                cur = con.cursor()
                result = cur.execute("select * from customers where Username ='" + username + "';")
                print (result)
                row = cur.fetchone()
                if row is not None:
                    Password_req = row[2]
                    if sha256_crypt.verify(password, Password_req):
                        session['logged_in'] = True
                        session['username'] = username
                        session['usertype'] = 'customer'
                        if username == "admin_bcskd":
                            session['usertype'] = 'Admin'
                            return redirect(url_for('admin_page'))
                        else:
                            cur.execute("select * from cart where CustomerName = ?",["Guest123"])
                            names = cur.fetchall()
                            if names != []:
                                for name in names:
                                    cur.execute("UPDATE 'cart' SET CustomerName = ? WHERE ProductName = ? AND SellerName = ? AND CustomerName = ?",[session["username"],name[1],name[2],name[0]])

                            return redirect(url_for('checkout'))
                    else:
                        return render_template('login_customer.html', checks = "Invalid", type = "Login_now")

                else:
                    return render_template('login_customer.html', checks = "Invalid", type = "Login_now")
        elif request.method == "POST":
            print ("Yes")
            return render_template('login_customer.html', checks = "Invalid", type = "Login_now")
        else:
            print ("yes")
            return render_template('login_customer.html', checks = "None", type = "Login_now")


@app.route('/mysellings')
def mysellings():
    if 'logged_in' in session:
        if session['usertype'] == 'customer':
            print('yes')
            return redirect(url_for('home'))
        else:
            with sql.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("select * from soldProducts where SellerName = ?",[session['username']])
                rows = cur.fetchall()
                if rows == []:
                    return render_template('mysellings.html', sellings = None, type = "mySellings", length =0)
                else:
                    add = []
                    ans = 0
                    for row in rows:
                        add.append(row[4]*row[3])
                        ans = ans + row[4]*row[3]
                    length = len(rows)
                    return render_template('mysellings.html', sellings = rows, length = length, type = "mySellings", Earnings = add, Answer = ans)
    else:
        return redirect(url_for('home'))


@app.route('/myProducts')
def myProducts():
    if 'logged_in' in session:
        if session['usertype'] == 'customer':
            return redirect(url_for('home'))
        else:
            with sql.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("select * from products where UploadedBy = ?",[session['username']])
                rows = cur.fetchall()
                if rows == []:
                    return render_template('myProducts.html', sellings = None, type = "myProducts")
                else:
                    return render_template('myProducts.html', sellings = rows, type = "myProducts")
    else:
        return redirect(url_for('home'))

@app.route('/myOrders')
def myOrders():
    if 'logged_in' in session:
        if session['usertype'] == 'seller' or session['usertype'] == 'Admin':
            return redirect(url_for('home'))
        else:
            with sql.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("select * from buyProducts where CustomerName = ?",[session['username']])
                rows = cur.fetchall()
                if rows == []:
                    return render_template('myOrders.html', items = None, length = 0)
                else:
                    add = []
                    ans =0
                    for row in rows:
                        ans = ans + row[4]*row[3]
                        add.append(row[4]*row[3])
                    length = len(rows)
                    cur.execute("select * from charges where Username = ?",[session['username']])
                    charges = cur.fetchone()
                    ans = ans + charges[1]
                    return render_template('myOrders.html', items = rows, Earnings = add, length = length, Answer = ans ,taxes = charges[1])
    else:
        return redirect(url_for('home'))


@app.route('/feedback/<proname>/<sellername>/<int:size>',methods=["GET","POST"])
def feedback(proname = None, sellername = None, size = None):
    if 'logged_in' in session:
        if session['usertype'] == 'customer':
            with sql.connect('database.db') as con:
                cur = con.cursor()
                cur.execute('select * from buyProducts where CustomerName = ? AND SellerName = ? AND ProductName = ? AND Size = ?',[session['username'],sellername,proname,size])
                row = cur.fetchone()
                if row is None:
                    return redirect(url_for('home'))
                else:
                    image = row[7]
                    if row[6] == "Yes":
                        return render_template('feedback.html', feedBack = "Yes", proname = proname, sellername = sellername, size = size,image = image )
                    else:
                        form = Feedback_form(request.form)
                        if request.method == "POST":
                            feedback = form.feedback.data
                            ratings = form.ratings.data
                            cur.execute("UPDATE 'buyProducts' SET 'Feedback' = ? WHERE CustomerName = ? AND SellerName = ? AND ProductName = ? AND Size = ?",["Yes",session['username'],sellername,proname,size])
                            cur.execute("INSERT INTO 'feedback' (feedBack,Ratings,SellerName,ProductName,CustomerName,Size) VALUES (?,?,?,?,?,?)",[feedback,ratings,sellername,proname,session['username'],size])
                            return redirect(url_for('home'))
                        else:
                            return render_template('feedback.html', proname = proname, sellername = sellername, size = size,image = image )
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@app.route('/addFollow/<Following>/<Follower>')
def addFollow(Following = None,Follower = None):
    if 'logged_in' in session:
        if session['usertype'] == 'customer':
            if Follower != None and Following != None:
                with sql.connect('database.db') as con:
                    cur = con.cursor()
                    cur.execute("INSERT INTO Follow (Following, Follower) VALUES (?,?)",(Following, Follower))
                    return redirect(url_for('followusers'))
            else:
                return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@app.route('/removeFollow/<Following>/<Follower>')
def removeFollow(Following = None,Follower = None):
    if 'logged_in' in session:
        if session['usertype'] == 'customer':
            if Follower != None and Following != None:
                with sql.connect('database.db') as con:
                    cur = con.cursor()
                    cur.execute("DELETE FROM Follow where Following = ? AND Follower = ?",[Following,Follower])
                    return redirect(url_for('followusers'))
            else:
                return redirect(url_for('home'))
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@app.route('/followusers')
def followusers():
    if 'logged_in' in session:
        if session['usertype'] == 'customer':
            with sql.connect('database.db') as con:
                cur = con.cursor()
                cur.execute('select Username from customers')
                users = cur.fetchall()
                totalusers = []
                Final_following=[]
                if users != []:
                    for user in users:
                        if user[0] != session['username']:
                            totalusers.append(user)
                    cur.execute('select * from Follow where Follower = ?',[session['username']])
                    following = cur.fetchall()
                    for user in totalusers:
                        check = 0
                        for follows in following:
                            if follows[1] == user[0]:
                                check = 1
                        if check == 1:
                            temp = []
                            temp.append(user)
                            temp.append('Yes')
                        else:
                            temp = []
                            temp.append(user)
                            temp.append('No')
                        Final_following.append(temp)
                return render_template('follow.html', followings = Final_following)
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@app.route('/blockcustomer/<Username>')
def blockcustomer(Username = None):
    if 'logged_in' in session:
        if session['usertype'] == 'Admin':
            with sql.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("DELETE FROM customers where Username = ?",[Username])
                return redirect(url_for('block'))
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@app.route('/blockseller/<Username>')
def blockseller(Username = None):
    if 'logged_in' in session:
        if session['usertype'] == 'Admin':
            with sql.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("DELETE FROM sellers where Username = ?",[Username])
                return redirect(url_for('block'))
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@app.route('/unblockcustomer/<Username>')
def unblockcustomer(Username = None):
    if 'logged_in' in session:
        if session['usertype'] == 'Admin':
            with sql.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("select * from bcustomers where Username = ?",[Username])
                row = cur.fetchone()
                cur.execute("INSERT INTO customers (Username, Email_ID, Password, Address, Phone)  VALUES (?,?,?,?,?)",(row[0], row[1], row[2], row[3], row[4]))
                return redirect(url_for('block'))
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))

@app.route('/unblockseller/<Username>')
def unblockseller(Username = None):
    if 'logged_in' in session:
        if session['usertype'] == 'Admin':
            with sql.connect('database.db') as con:
                cur = con.cursor()
                cur.execute("select * from bsellers where Username = ?",[Username])
                row = cur.fetchone()
                cur.execute("INSERT INTO sellers (Name, Username, Email_ID, Address, Pincode, Phone_no , Password)  VALUES (?,?,?,?,?,?,?)",(row[0],row[1],row[2],row[3],row[4],row[5],row[6]))
                return redirect(url_for('block'))
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))


@app.route('/block')
def block():
    if 'logged_in'in session:
        if  session['usertype'] == 'Admin':
            with sql.connect('database.db') as con:
                cur = con.cursor()
                cur.execute('select Username from bsellers')
                seller_user = cur.fetchall()
                seller_users = []
                customer_users = []
                for i in seller_user:
                    cur.execute('select * from sellers where Username = ?',[i[0]])
                    row = cur.fetchone()
                    temp = []
                    temp.append(i[0])
                    if row is None:
                        temp.append("Yes")
                    else:
                        temp.append("No")
                    seller_users.append(temp)
                cur.execute('select Username from bcustomers')
                customer_user = cur.fetchall()
                print (customer_user)
                for i in customer_user:
                    if i[0] != 'admin_bcskd':
                        cur.execute('select * from customers where Username = ?',[i[0]])
                        row = cur.fetchone()
                        temp = []
                        temp.append(i[0])
                        if row is None:
                            temp.append("Yes")
                        else:
                            temp.append("No")
                        customer_users.append(temp)
                print (customer_users)
                return render_template('block.html',sellers = seller_users, customers = customer_users )
        else:
            return redirect(url_for('home'))
    else:
        return redirect(url_for('home'))


class RegisterForm_sellers(Form):
    name = TextField("",[validators.required(),
                                validators.Length(min=4)])
    username = TextField("", [validators.required(),
                                      validators.Length(min = 4, max = 17)])
    email = EmailField("", [validators.required(),
                                    validators.Email()])
    phone = TextField("",[validators.required(),
                                    validators.Length(min = 10)])
    pincode = IntegerField("",[validators.required()])

    address = TextField("",[validators.required()])

    password = PasswordField("", [validators.required(),
                                  validators.Length(min = 5, max = 20),
                                  validators.EqualTo('confirm', message = "Password must match")])
    confirm = PasswordField("")

class LoginForm(Form):
    username = TextField("",[validators.required(),
                             validators.Length(min = 4, max = 17)])
    password = PasswordField("",[validators.required(),
                                 validators.Length(min = 5, max = 20)])

class RegisterForm_customers(Form):
    username = TextField("", [validators.required(),
                                      validators.Length(min = 4, max = 17)])
    email = EmailField("", [validators.required(),
                                    validators.Email()])
    address = TextField("", [validators.required()])

    phone = TextField("",[validators.required(),
                          validators.Length(min=10)])
    password = PasswordField("", [validators.required(),
                                  validators.Length(min = 5, max = 20),
                                  validators.EqualTo('confirm', message = "Password must match")])
    confirm = PasswordField("")

class UpdateForm_customers(Form):
    username = TextField("", [validators.required(),
                                      validators.Length(min = 4, max = 17)])
    email = EmailField("", [validators.required(),
                                    validators.Email()])
    address = TextField("", [validators.required()])

    phone = TextField("",[validators.required(),
                          validators.Length(min=10)])

class UpdateForm_sellers(Form):
    name = TextField("", [validators.required()])

    username = TextField("", [validators.required(),
                                      validators.Length(min = 4, max = 17)])
    email = EmailField("", [validators.required(),
                                    validators.Email()])
    address = TextField("", [validators.required()])

    phone = TextField("",[validators.required(),
                          validators.Length(min=10)])
    pincode = TextField("",[validators.required()])

class AddProducts(Form):
    name = TextField("Product Name",[validators.required()])

    brand = TextField("Brand",[validators.required()])

    size = IntegerField("size",[validators.required()])

    mrp = IntegerField("MRP",[validators.required()])

    sellingAt = IntegerField("Selling Price",[validators.required()])

    quantity = IntegerField("Quantity",[validators.required()])

    Image1 = TextField("Image1",[validators.required()])

    Image2 = TextField("Image2",[validators.required()])

    Image3 = TextField("Image3",[validators.required()])

class SearchForm(Form):
    searchName = TextField("",[validators.required()])

class changePassword_form(Form):
    oldPassword = PasswordField("", [validators.required()])
    newPassword = PasswordField("", [validators.required(),
                                    validators.Length(min = 5, max=20),
                                    validators.EqualTo('confirm', message = "Password must match")])
    confirm = PasswordField("")

class Feedback_form(Form):
    feedback = TextField("",[validators.required()])

    ratings = IntegerField("", [validators.required()])


def create_table():
 try:
   with sql.connect("database.db") as con:
     con.execute('''CREATE TABLE IF NOT EXISTS customers (Username TEXT NOT NULL,
                   Email_ID TEXT NOT NULL,
                   Password TEXT NOT NULL,
                   Address TEXT NOT NULL,
                   Phone INT NOT NULL);''')
     con.execute('''CREATE TABLE IF NOT EXISTS sellers (Name TEXT NOT NULL,
                   Username TEXT NOT NULL,
                   Email_ID TEXT NOT NULL,
                   Address TEXT NOT NULL,
                   Pincode INT NOT NULL,
                   Phone_no INT NOT NULL,
                   Password TEXT NOT NULL);''')
     con.execute('''CREATE TABLE IF NOT EXISTS bcustomers (Username TEXT NOT NULL,
                   Email_ID TEXT NOT NULL,
                   Password TEXT NOT NULL,
                   Address TEXT NOT NULL,
                   Phone INT NOT NULL);''')
     con.execute('''CREATE TABLE IF NOT EXISTS bsellers (Name TEXT NOT NULL,
                   Username TEXT NOT NULL,
                   Email_ID TEXT NOT NULL,
                   Address TEXT NOT NULL,
                   Pincode INT NOT NULL,
                   Phone_no INT NOT NULL,
                   Password TEXT NOT NULL);''')
     con.execute('''CREATE TABLE IF NOT EXISTS products (Name Text  NOT NULL,
                    Brand Text NOT NULL,
                    Size INT NOT NULL,
                    MRP INT NOT NULL,
                    SellingAt INT NOT NULL,
                    Quantity INT NOT NULL,
                    UploadedBy Text NOT NULL,
                    Sold Text NOT NULL,
                    Img1 Text NOT NULL,
                    Img2 Text NOT NULL,
                    Img3 Text NOT NULL);''')
     con.execute('''CREATE TABLE IF NOT EXISTS cart (CustomerName Text NOT NULL,
                    ProductName Text NOT NULL,
                    SellerName Text NOT NULL,
                    Size INT NOT NULL,
                    Quantity INT NOT NULL);''')
     con.execute('''CREATE TABLE IF NOT EXISTS feedback(ProductName Text NOT NULL,
                    SellerName Text NOT NULL,
                    CustomerName Text NOT NULL,
                    Size INT NOT NULL,
                    FeedBack Text NOT NULL,
                    Ratings INT NOT NULL);''')
     con.execute('''CREATE TABLE IF NOT EXISTS soldProducts(ProductName Text NOT NULL,
                    SellerName Text NOT NULL,
                    CustomerName Text NOT NULL,
                    Quantity INT NOT NULL,
                    Cost INT NOT NULL,
                    Size INT NOT NULL);''')
     con.execute('''CREATE TABLE IF NOT EXISTS buyProducts(ProductName Text NOT NULL,
                    SellerName Text NOT NULL,
                    CustomerName Text NOT NULL,
                    Quantity INT NOT NULL,
                    Cost INT NOT NULL,
                    Size INT NOT NULL,
                    Feedback Text NOT NULL,
                    Img1 Text NOT NULL,
                    Img2 Text NOT NULL,
                    Img3 Text NOT NULL);''')
     con.execute('''CREATE TABLE IF NOT EXISTS Follow(Follower Text NOT NULL,
                    Following Text NOT NULL);''')
     con.execute('''CREATE TABLE IF NOT EXISTS charges(Username Text NOT NULL,
                    charge INT NOT NULL);''')

 except:
   print ("Table already exists")


if __name__ == '__main__':
    app.run(debug=True)
