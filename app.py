from flask import Flask, render_template, request, redirect, session, jsonify,flash
from flask_sqlalchemy import SQLAlchemy 
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1343@localhost/cafe_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# -----------------------------
# MODELS
# -----------------------------

# -----------------------
# MODELS
# -----------------------

class User(db.Model):
    _tablename_="users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))
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
with app.app_context():
    db.create_all()

# 🔹 Reservation auto-check
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

    if request.method == "POST":

        role = request.form.get("role")
        email = request.form.get("email")
        password = request.form.get("password")

        if role == "admin" and email == "admin@cafe.com" and password == "admin123":
            return redirect("/admin_dashboard")

        elif role == "staff" and email == "staff@cafe.com" and password == "staff123":
            return redirect("/staff_dashboard")

        elif role == "customer" and email == "customer@cafe.com" and password == "cust123":
            return redirect("/customer")

        else:
            return "Invalid Login"

    return render_template("login.html")

@app.route("/signup", methods=["GET","POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        user = User(
            name=name,
            email=email,
            password=password,
            role=role
        )

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("signup.html")

@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email, password=password).first()

        if user:

            session["user_id"] = user.id
            session["user_role"] = user.role

            # ⭐ YAHI ADD KARNA HAI
            if user.role == "admin":
                return redirect("/dashboard")

            elif user.role == "staff":
                return redirect("/staff_dashboard")

            else:
                return redirect("/menu")

        else:
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
import ast

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
    item = MenuItem.query.get(item_id)

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




from datetime import datetime, timedelta

@app.route("/book_table", methods=["POST"])
def book_table():

    name = request.form["name"]
    phone = request.form["phone"]
    date = request.form["date"]
    time = request.form["time"]
    table_number = request.form["table_number"]

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

    return redirect("/")




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
with app.app_context():
    db.create_all()

with app.app_context():

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


