from flask import Flask, request, jsonify, session, render_template
import mysql.connector
import smtplib,random
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager
from routes.auth_routes import auth_bp
from routes.jwt_routes import jwt_bp
from routes.admin_routes import admin_bp
from routes.admin_routes import admin_required
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("DB_PASSWORD"),
    database="flasklearning"
)
print("Database connected successfully")

app.config["db"] = db

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

jwt = JWTManager(app)

app.register_blueprint(auth_bp)
app.register_blueprint(jwt_bp)
app.register_blueprint(admin_bp)

#register,login get
@app.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/onboarding",methods=["post"] )
def onboarding():
    data=request.json
    user_id=session.get("user_id")
    if not data:
        return jsonify({"message":"Data is required"}),400
    gender=data.get("gender")
    if not gender:
        return jsonify({"message":"Gender is required"}),400
    highest_qualification=data.get("highest_qualification")
    if not highest_qualification:
        return jsonify({"message":"Highest Qualification is required"}),400
    percentage=data.get("percentage")
    if not percentage:
        return jsonify({"message":"Percentage is required"}),400
    institute=data.get("institute")
    if not institute:
        return jsonify({"message":"Institute is required"}),400
    role=data.get("role")
    if not role:
        return jsonify({"message":"Role is required"}),400
    experience=data.get("experience")
    if not experience:
        return jsonify({"message":"Experience is required"}),400
    domain=data.get("domain")
    if not domain:
        return jsonify({"message":"Domain is required"}),400
    cursor=db.cursor()
    cursor.execute("insert into user_profile(user_id,gender,highest_qualification,percentage,institute,role,experience,domain) values(%s,%s,%s,%s,%s,%s,%s,%s)",(user_id,gender,highest_qualification,percentage,institute,role,experience,domain))
    db.commit()
    return jsonify({"message":"Onboarding successful"}),200

@app.route("/welcome",methods=["get"])
def welcome():
    cursor=db.cursor()
    cursor.execute(
        "select u.username,up.gender,up.highest_qualification,up.percentage,up.institute,up.role,up.experience,up.domain from users u inner join user_profile up on u.id=up.user_id where u.id=%s",(session.get("user_id"),)
    )
    user=cursor.fetchone()
    return render_template("welcome.html", user=user)


@app.route("/onboarding", methods=["GET"])
def onboarding_page():
    return render_template("onboarding.html")

@app.route("/forgot-password", methods=["POST"])
def forgot_password():

    data=request.json
    if not data:
        return jsonify({"message":"Data is required"}),400  
    email=data.get("email")
    if not email:
        return jsonify({"message":"Email is required"}),400
    cursor=db.cursor()
    cursor.execute("select id from users where email=%s",(email,))
    user=cursor.fetchone()
    if not user:
        return jsonify({"message":"User not found"}),404
    server=smtplib.SMTP("smtp.gmail.com",587)
    server.starttls()
    server.login("r.sruthirajeev688@gmail.com",os.getenv("SMTP_PASSWORD"))
    generate_otp=random.randint(100000,999999)
    otp=str(generate_otp)
    session["user_id"] = user[0]
    session["email"]=email
    session["otp"]=otp
    msg=MIMEText(f"Your OTP is {otp} don't share it with anyone")
    msg["Subject"]="confirmation mail"
    msg["From"]="r.sruthirajeev688@gmail.com"
    msg["To"]=email
    server.sendmail("r.sruthirajeev688@gmail.com",email,msg.as_string())
    server.quit()
    return jsonify({"message": "OTP sent successfully"}), 200
@app.route("/forgot-password", methods=["GET"])
def forgot_password_page():
    return render_template("forgot_password.html")

@app.route("/verify",methods=["post"])
def verify():
    data=request.json
    enteredotp=data.get("otp")
    if not enteredotp:
        return jsonify({"message":"OTP is required"}),400
    if enteredotp==session.get("otp"):
        return jsonify({"message":"OTP verified"}),200
    else:
        return jsonify({"message":"Invalid OTP"}),400
    
@app.route("/verify", methods=["GET"])
def verify_page():
    return render_template("vertify.html")
@app.route("/reset-password", methods=["POST"])
def reset_password():
    data=request.json
    password=data.get("password")
    if not password:
        return jsonify({"message":"Password is required"}),400
    cursor=db.cursor()
    cursor.execute("update users set password=%s where email=%s",(password,session.get("email")))
    db.commit()
    return jsonify({"message":"Password reset successful"}),200
@app.route("/reset-password", methods=["GET"])
def reset_password_page():
    return render_template("reset.html")

#products

@app.route("/products", methods=["GET"])
def products():
    cursor = db.cursor(dictionary=True, buffered=True)

    user_id = session.get("user_id")

    # Get the logged-in user's role
    cursor.execute(
        "SELECT role FROM users WHERE id = %s",
        (user_id,)
    )
    user = cursor.fetchone()
    role = user["role"] if user else None

    # Get all products
    cursor.execute(
        "SELECT prod_id, prod_name, des, price, image FROM products"
    )
    products = cursor.fetchall()

    # Get cart count
    cursor.execute(
        "SELECT SUM(quantity) AS count FROM cart WHERE user_id = %s",
        (user_id,)
    )
    cart_result = cursor.fetchone()
    cart_count = cart_result["count"] if cart_result and cart_result["count"] else 0

    cursor.close()

    return render_template(
        "products.html",
        role=role,
        cart_count=cart_count,
        products=products
    )

    
@app.route("/add_product",methods=["GET"])
def add_product_page():
    return render_template("add_product.html")
@app.route("/add_product",methods=["POST"])
@admin_required()
def add_product():

    data= request.json;
    if data is None:
        return jsonify({"message":"Data required"},400)
    prod_name=data.get("prod_name")
    des=data.get("des")
    price=data.get("price")
    image=data.get("image")
    cursor=db.cursor()
    cursor.execute("insert into products(prod_name,des,price,image) values(%s,%s,%s,%s)",(prod_name,des,price,image))
    db.commit()
    return jsonify({"message":"Product added successfully"}),200

#cart
@app.route("/cart", methods=["GET"])
def view_cart():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"message": "User not logged in"}), 401

    cursor = db.cursor(dictionary=True)

    query = """
        SELECT
            c.prod_id,
            p.prod_name,
            p.price,
            p.image,
            c.quantity
        FROM cart AS c
        INNER JOIN products AS p
            ON c.prod_id = p.prod_id
        WHERE c.user_id = %s
    """

    cursor.execute(query, (user_id,))
    items = cursor.fetchall()
    cursor.close()

    total = sum(
        item["price"] * item["quantity"]
        for item in items
    )

    return render_template(
        "cart.html",
        items=items,
        total=total
    )

@app.route("/cart", methods=["POST"])
def cart():
    data = request.json

    if data is None:
        return jsonify({"message": "Data required"}), 400

    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"message": "User not logged in"}), 401

    prod_id = data.get("prod_id")
    quantity = data.get("quantity", 1)

    
    if not prod_id:
        return jsonify({"message": "Product ID is required"}), 400

    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
        return jsonify({"message": "Quantity must be a positive integer"}), 400
    if quantity > 10:
        return jsonify({"message": "Quantity must be less than or equal to 10"}), 400
    cursor = db.cursor()

    try:
        cursor.execute(
            "SELECT prod_id, prod_name, des, price, image "
            "FROM products WHERE prod_id = %s",
            (prod_id,)
        )

        product = cursor.fetchone()
        if not product:
            return jsonify({"message": "Product not found"}), 404

        prod_name = product[1]
        price = product[3]

       
        query = """
            INSERT INTO cart (user_id, prod_id, quantity)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                quantity = quantity + %s
        """

        cursor.execute(
            query,
            (user_id, prod_id, quantity, quantity)
        )

        db.commit()


        return jsonify({"message": "Product added successfully"}), 200

    except mysql.connector.Error:
        db.rollback()
        app.logger.exception("Failed to add product to cart")
        return jsonify({"message": "Unable to update cart"}), 500

    finally:
        cursor.close()

@app.route("/cart/increase/<int:prod_id>", methods=["PUT"])
def increase_quantity(prod_id):
    cursor = db.cursor()
    try:
        cursor.execute(
            "UPDATE cart SET quantity = quantity + 1 WHERE prod_id = %s AND user_id = %s",
            (prod_id, session.get("user_id"))
        )
        db.commit()
        cursor.close()
        return jsonify({"success": True, "message": "Product quantity updated"}), 200
    except mysql.connector.Error:
        db.rollback()
        cursor.close()
        app.logger.exception("Failed to update product quantity")
        return jsonify({"success": False, "message": "Unable to update product quantity"}), 500

@app.route("/cart/decrease/<int:prod_id>", methods=["PUT"])
def decrease_quantity(prod_id):
    cursor = db.cursor()
    try:
        # Optional: Use GREATEST to prevent quantity from going below 1
        cursor.execute(
            "UPDATE cart SET quantity = GREATEST(quantity - 1, 1) WHERE prod_id = %s AND user_id = %s",
            (prod_id, session.get("user_id"))
        )
        db.commit()
        cursor.close()
        return jsonify({"success": True, "message": "Product quantity updated"}), 200
    except mysql.connector.Error:
        db.rollback()
        cursor.close()
        app.logger.exception("Failed to update product quantity")
        return jsonify({"success": False, "message": "Unable to update product quantity"}), 500

@app.route("/cart/<int:prod_id>", methods=["DELETE"])
def remove_from_cart(prod_id):
    cursor = db.cursor()
    try:
        cursor.execute(
            "DELETE FROM cart WHERE prod_id = %s AND user_id = %s",
            (prod_id, session.get("user_id"))
        )
        db.commit()
        cursor.close()
        return jsonify({"success": True, "message": "Product removed from cart"}), 200
    except mysql.connector.Error:
        db.rollback()
        cursor.close()
        app.logger.exception("Failed to remove product from cart")
        return jsonify({"success": False, "message": "Unable to remove product from cart"}), 500
@app.route("/checkout", methods=["POST"])
def checkout():
    user_id = session.get("user_id")
    data = request.json

    if data is None:
        return jsonify({"message": "Data required"}), 400
    payment_method=data.get("payment_method")

    if not user_id:
        return jsonify({"message": "Please login first"}), 401

    cursor = db.cursor(dictionary=True)

    try:
        # 1. Get cart items and product details
        cursor.execute("""
            SELECT p.prod_id, p.prod_name, p.price, c.quantity
            FROM cart c
            JOIN products p ON c.prod_id = p.prod_id
            WHERE c.user_id = %s
        """, (user_id,))

        cart_items = cursor.fetchall()

        if not cart_items:
            return jsonify({"message": "Your cart is empty"}), 400

        # 2. Calculate total and prepare order summary
        total = 0
        order_summary = []
        status="SUCCESS"
        for item in cart_items:
            subtotal = float(item["price"]) * item["quantity"]
            if payment_method == "COD":
                total += subtotal + 50
                status="pending"
            else:
                total += subtotal

            order_summary.append({
                "prod_id": item["prod_id"],
                "product": item["prod_name"],
                "price": float(item["price"]),
                "quantity": item["quantity"],
                "subtotal": subtotal
            })

        # 3. Get the user's email
        cursor.execute(
            "SELECT email FROM users WHERE id = %s",
            (user_id,)
        )
        user = cursor.fetchone()

        if not user:
            return jsonify({"message": "User not found"}), 404


        # 4. Save the dummy order
        cursor.execute("""
            INSERT INTO orders (user_id, total_amount, payment_status,payment_method)
            VALUES (%s, %s, %s, %s)
        """, (user_id, total, status,payment_method))

        order_id = cursor.lastrowid
        order_items_data = [
            (order_id, item["prod_id"], item["prod_name"], item["price"], item["quantity"])
            for item in cart_items
        ]
        
        cursor.executemany("""
            INSERT INTO order_items (order_id, product_id, product_name, price, quantity)
            VALUES (%s, %s, %s, %s, %s)
        """, order_items_data)

        # 5. Prepare the email
        lines = [
            f"Order ID: {order_id}",
            "",
            "Your order summary:",
            ""
        ]

        for item in order_summary:
            lines.append(
                f"{item['product']} | "
                f"Price: Rs. {item['price']:.2f} | "
                f"Quantity: {item['quantity']} | "
                f"Subtotal: Rs. {item['subtotal']:.2f}"
            )

        lines.extend([
            "",
            f"Total amount: Rs. {total:.2f}",
            "Dummy payment status: SUCCESS",
            "",
            "Thank you for your order!"
        ])

        message = MIMEText("\n".join(lines))
        message["Subject"] = f"Order Confirmation #{order_id}"
        message["From"] = "r.sruthirajeev688@gmail.com"
        message["To"] = user["email"]

        # 6. Send the email using Gmail SMTP
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login("r.sruthirajeev688@gmail.com",os.getenv("SMTP_PASSWORD"))

            server.send_message(message)
        #adding items to roder table
        
        # 7. Clear this user's cart only after email succeeds
        cursor.execute(
            "DELETE FROM cart WHERE user_id = %s",
            (user_id,)
        )

        db.commit()

        return jsonify({
            "message": "Dummy payment successful! Order summary sent to your email.",
            "order_id": order_id,
            "total": round(total, 2),
            "order_summary": order_summary
        }), 200

    except Exception as e:
        db.rollback()
        print("Checkout error:", e)
        return jsonify({
            "message": "Checkout failed. Please try again."
        }), 500

    finally:
        cursor.close()

@app.route("/checkout-page", methods=["GET"])
def checkout_page():
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({"message": "Please login first"}), 401

    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("""SELECT p.prod_id, p.prod_name, p.price, p.image, c.quantity FROM cart AS c INNER JOIN products AS p ON c.prod_id = p.prod_id WHERE c.user_id = %s""", (user_id,))
        items = cursor.fetchall()
        if not items:
            return "Your cart is empty. Please add products first."
        total = sum(
            item["price"] * item["quantity"]
            for item in items
        )
        return render_template("checkout.html", cart_items=items,  total=total)

    finally:
        cursor.close()

@app.route("/orders", methods=["GET"])
def orders():
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login") # or handle unauthorized access

    # Use dictionary=True so we can use order['order_id'] instead of indices
    cursor = db.cursor(dictionary=True)
    
    # We join orders with order_items to get a comma-separated summary of items per order
    cursor.execute("""
        SELECT o.order_id, o.total_amount, o.payment_status, o.payment_method,
               GROUP_CONCAT(CONCAT(oi.product_name, ' (x', oi.quantity, ')') SEPARATOR ', ') AS items_summary
        FROM orders o
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.user_id = %s
        GROUP BY o.order_id
        ORDER BY o.order_id DESC;
    """, (user_id,))
    
    user_orders = cursor.fetchall()  
    cursor.close()         
    
    return render_template("order.html", orders=user_orders)


@app.route("/admin", methods=["GET"])
@admin_required()
def admin_dashboard():
    return render_template("admin.html")

if __name__ == '__main__':
    app.run(debug=True)