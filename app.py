from flask import Flask, render_template, request, redirect, session, jsonify,flash, url_for
from flask_sqlalchemy import SQLAlchemy 
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# LOAD ENV VARIABLES
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("mysecretkey")

UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# -----------------------------
# MODELS
# -----------------------------

# -----------------------
# MODELS
# -----------------------

class User(db.Model):
    __tablename__="users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(255))
    role = db.Column(db.String(20))


class Tables(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer)
    status = db.Column(db.String(20))
    reserved_by = db.Column(db.String(100))
    reserved_until = db.Column(db.DateTime)

class MenuItem(db.Model):

    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    category = db.Column(db.String(50))
    price = db.Column(db.Integer)
    stock = db.Column(db.Integer)
    image = db.Column(db.String(200))


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    table_number = db.Column(db.Integer)
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer)
    items = db.Column(db.Text)
    total= db.Column(db.Integer)

class TableBooking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    table_number = db.Column(db.Integer)
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))



# -----------------------------
# CREATE TABLES
# -----------------------------
# with app.app_context():
#     db.create_all()

#  Reservation auto-check
@app.before_request
def check_reservations():

    tables = Tables.query.all()

    for table in tables:

        if table.status == "reserved" and table.reserved_until:

            if datetime.now() > table.reserved_until:

                table.status = "available"
                table.reserved_by = None
                table.reserved_until = None

    db.session.commit()

# -----------------------------
# ROUTES
# -----------------------------
@app.route("/", methods=["GET","POST"])
def home():
    return redirect("/login")

@app.route("/signup", methods=["GET","POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        role = request.form["role"]

        # prevent admin signup
        if role == "admin":
            return "Admin accounts cannot be created from signup"
        
        user = User(
            name=name,
            email=email,
            password=password,
            role=role
        )

        db.session.add(user)
        db.session.commit()

        flash("Account created. Please login.")
        return redirect("/login")

    return render_template("signup.html")

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]
        selected_role = request.form["role"]

        # hardcoded admin login
        if email == "admin@cafe.com" and password == "admin123":
            session["user_role"] = "admin"
            session["user_name"] = "Admin"
            return redirect("/admin_dashboard")
        
        # database login for staff and customer
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            # role validation
            if user.role != selected_role:
                flash("You selected wrong role")
                return redirect("/login")
            
            session["user_id"] = user.id
            session["user_role"] = user.role

            if user.role == "admin":
                return redirect("/dashboard")

            elif user.role == "staff":
                return redirect("/staff_dashboard")

            else:
                return redirect("/customer")

        else:
            flash("Invalid email or password")
            return "Invalid login"

    return render_template("login.html")

@app.route("/admin_dashboard")
def admin_dashboard():

    orders = Order.query.all()
    tables = Tables.query.all()

    return render_template(
        "admin_dashboard.html",
        orders=orders,
        tables=tables
    )

@app.route("/customer")
def customer():
    return render_template("customer.html")



@app.route("/menu")
def menu():
    items = MenuItem.query.all()
    tables = Tables.query.all()
    cart = session.get("cart", [])

    total = sum(item["price"] for item in cart)

    return render_template(
        "menu.html",
        items=items,
        tables=tables,
        total=total
    
    )
    
# admin dashboard
@app.route("/admin/menu")
def admin_menu():
    # if session.get("role") != "admin":
    #     return redirect(url_for("login"))

    items = MenuItem.query.all()
    return render_template("admin_menu.html", items=items)

@app.route("/admin/add_item", methods=["GET", "POST"])
def add_item():
    if request.method == "POST":
        name = request.form["name"]
        category = request.form["category"]
        price = request.form["price"]
        stock = request.form["stock"]
        
        image_file = request.files.get("image")

        # if no image provided, use default
        if image_file and image_file.filename != "":
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], image_file.filename)
            image_file.save(filepath)
            image = image_file.filename
        else:
            image = "default.jpg"
        
        new_item = MenuItem(
            name=name,
            category=category,
            price=price,
            stock=stock,
            image=image
        )

        db.session.add(new_item)
        db.session.commit()

        return redirect(url_for("admin_menu"))

    return render_template("add_item.html", item=None)

@app.route("/admin/edit_item/<int:item_id>", methods=["GET", "POST"])
def edit_item(item_id):
    item = MenuItem.query.get_or_404(item_id)

    if request.method == "POST":
        item.name = request.form["name"]
        item.category = request.form["category"]
        item.price = request.form["price"]
        item.stock = request.form["stock"]
        image_file = request.files.get("image")
        
        if image_file and image_file.filename != "":
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], image_file.filename)
            image_file.save(filepath)
            item.image = image_file.filename

        db.session.commit()
        return redirect(url_for("admin_menu"))

    return render_template("edit_item.html", item=item)

@app.route("/admin/delete_item/<int:item_id>")
def delete_item(item_id):
    # if session.get("role") != "admin":
    #     return redirect(url_for("login"))

    item = MenuItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()

    return redirect(url_for("admin_menu"))

@app.route("/reports")
def reports():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    return render_template("reports.html")

@app.route("/prebook")
def prebook():

    tables = Tables.query.all()

    print("TABLES FROM DB:", tables)

    return render_template("prebook.html", tables=tables)
@app.route("/dashboard")
def dashboard():

    tables = Tables.query.all()
    items = MenuItem.query.all()
    orders = Order.query.all()

    return render_template(
        "dashboard.html",
        tables=tables,
        items=items,
        orders=orders
    )
@app.route("/tables")
def tables():
    tables = Tables.query.all()
    print("TABLES:", tables)  
    return render_template("tables.html", tables=tables)
# import ast

@app.route("/place_order", methods=["POST"])
def place_order():

    items = request.form.get("items")
    total = request.form.get("total_price")

    items_list = json.loads(items)

    # reserved table number
    table_number = session.get("table_number")

    new_order = Order(
        table_number=table_number,
        items=items,
        total=total
    )

    db.session.add(new_order)
    db.session.commit()

    return render_template(
        "order_success.html",
        items=items_list,
        total=total
    )
@app.route("/order_success")
def order_success():
    return render_template("order_success.html")

@app.route("/add_to_cart", methods=["POST"])
def add_to_cart():

    item_id = request.form.get("item_id")
    item = MenuItem.query.get_or_404(item_id)

    if "cart" not in session:
        session["cart"] = []

    cart = session["cart"]

    cart.append({
        "name": item.name,
        "price": item.price
    })

    session["cart"] = cart

    return redirect("/menu")
@app.route("/free_table/<int:table_number>")
def free_table(table_number):

    table = Tables.query.filter_by(table_number=table_number).first()

    table.status = "available"
    db.session.commit()

    return "<script>alert('Table is now free'); window.location='/tables';</script>"




# from datetime import datetime, timedelta

@app.route("/book_table", methods=["POST"])
def book_table():

    name = request.form["name"]
    phone = request.form["phone"]
    date = request.form["date"]
    time = request.form["time"]
    table_number = int(request.form["table_number"])

    table = Tables.query.filter_by(table_number=table_number).first()

    # combine date + time
    date = request.form["date"]
    time = request.form["time"]
    reserve_time = datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M")

    table.status = "reserved"
    table.reserved_by = name
    table.reserved_until = reserve_time

    db.session.commit()

    session["table_number"] = table_number
    session["customer_name"] = name

    flash(f"Table {table_number} reserved for {time}. You can now order food.")

    return redirect("/menu")

'''@app.route("/book_table", methods=["POST"])
def book_table():

    name = request.form["name"]

    phone = request.form["phone"]

    table = request.form["table"]

    date = request.form["date"]

    time = request.form["time"]

    booking = TableBooking(
        name=name,
        phone=phone,
        table_number=table,
        date=date,
        time=time
    )

    db.session.add(booking)
    db.session.commit()

    return "<script>alert('Table Booked Successfully');window.location='/'</script>" '''
@app.route('/logout')
def logout():
    session.clear()
    return redirect("/login")




@app.route('/orders')
def orders():

    orders = Order.query.all()

    return render_template("orders.html", orders=orders)

@app.route("/customer_book")
def customer_book():

    tables = Tables.query.all()

    return render_template("customer_book.html", tables=tables)

@app.route("/staff_dashboard")
def staff_dashboard():
    return render_template("staff_dashboard.html")

# -----------------------------
# RUN SERVER
# -----------------------------
# with app.app_context():
#     db.create_all()

with app.app_context():
    db.create_all()
    if Tables.query.count() == 0:

        for i in range(1,11):

            table = Tables(
                table_number=i,
                status="available"
            )

            db.session.add(table)

        db.session.commit()

        print("Tables inserted successfully")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


