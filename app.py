from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy 
import json

app = Flask(__name__)
app.secret_key = "cafe_secret_key"

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:bani@localhost/cafe_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# -----------------------------
# MODELS
# -----------------------------

# -----------------------
# MODELS
# -----------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))


class Tables(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer)
    status = db.Column(db.String(20))

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
    total_price = db.Column(db.Integer)

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


# -----------------------------
# ROUTES
# -----------------------------
@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        role = request.form.get("role")
        email = request.form.get("email")
        password = request.form.get("password")

        if role == "admin" and email == "admin@cafe.com" and password == "admin123":
            return redirect("/dashboard")

        elif role == "staff" and email == "staff@cafe.com" and password == "staff123":
            return redirect("/staff_dashboard")

        elif role == "customer" and email == "customer@cafe.com" and password == "cust123":
            return redirect("/customer")

        else:
            return "Invalid Login"

    return render_template("login.html")

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
    total_price = request.form.get("total_price")

    if items:
        items_list = json.loads(items)
    else:
        items_list = []

    return render_template(
        "order_success.html",
        items=items_list,
        total=total_price
    
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




@app.route("/book_table", methods=["POST"])
def book_table():

    name = request.form.get("name")
    phone = request.form.get("phone")
    date = request.form.get("date")
    time = request.form.get("time")
    table_number = request.form.get("table_number")

    table = Tables.query.filter_by(table_number=table_number).first()

    if not table:
        return "Table not found"

    if table.status == "occupied":
        return "Table already occupied"

    table.status = "occupied"
    db.session.commit()

    return render_template(
        "booking_success.html",
        name=name,
        table=table_number,
        date=date,
        time=time
    )



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
    app.run(debug=True)


