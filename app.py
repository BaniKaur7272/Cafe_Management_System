from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy

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

class MenuItem(db.Model):
    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    category = db.Column(db.String(50))
    price = db.Column(db.Integer)
    stock = db.Column(db.Integer)
    image = db.Column(db.String(200))


class Tables(db.Model):
    __tablename__ = "tables"
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer)
    status = db.Column(db.String(20), default="available")


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_number = db.Column(db.Integer)
    items = db.Column(db.Text)
    total_price = db.Column(db.Integer)


# -----------------------------
# CREATE TABLES
# -----------------------------
with app.app_context():
    db.create_all()


# -----------------------------
# ROUTES
# -----------------------------

@app.route("/")
def home():
    return render_template("login.html")


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

@app.route("/tables")
def tables():
    tables = Tables.query.all()
    return render_template("tables.html", tables=tables)
import ast
@app.route("/place_order", methods=["POST"])
def place_order():

    table_number = request.form.get("table_number")
    items = session.get("cart", [])

    total_price = sum(item["price"] for item in items)

    order = Order(
        table_number=table_number,
        items=str(items),
        total_price=total_price
    )

    db.session.add(order)
    db.session.commit()

    session.pop("cart", None)

    return render_template(
        "order_success.html",
        items=items,
        total=total_price
    )
    
@app.route("/order_success")
def order_success():
    return render_template("order_success.html")


@app.route("/free_table/<int:table_number>")
def free_table(table_number):

    table = Table.query.filter_by(table_number=table_number).first()

    if table:
        table.status = "available"
        db.session.commit()

    return redirect("/tables")
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
@app.route("/login", methods=["POST"])
def login():

    role = request.form.get("role")
    email = request.form.get("email")
    password = request.form.get("password")

    if role == "admin":
        return redirect("/dashboard")

    elif role == "staff":
        return redirect("/menu")

    elif role == "customer":
        return redirect("/menu")

    return "Invalid login"


# -----------------------------
# RUN SERVER
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)