from flask import Blueprint, render_template, session, redirect, url_for, jsonify, current_app, request
from functools import wraps

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/api/admin"
)

def admin_required():
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get("user_id")
            if not user_id:
                return redirect(url_for("login_page"))
            
            db = current_app.config["db"]
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT role FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            cursor.close()
            
            if not user or user["role"] != "admin":
                return jsonify({"message": "Admins only!"}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@admin_bp.route("/test", methods=["GET"])
@admin_required()
def admin_test():
    return jsonify({
        "message": "Welcome, admin"
    }), 200

@admin_bp.route("/admin/products", methods=["GET"])
@admin_required()
def admin_products():
    db = current_app.config["db"]
    cursor = db.cursor(dictionary=True, buffered=True)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.close()
    return render_template("admin_products.html", products=products)

@admin_bp.route("/admin/product/delete/<int:prod_id>", methods=["DELETE"])
@admin_required()
def delete_product(prod_id):
    db = current_app.config["db"]
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM products WHERE prod_id = %s", (prod_id,))
        db.commit()
        return jsonify({"message": "Product deleted successfully!"}), 200
    except Exception:
        db.rollback()
        current_app.logger.exception("Failed to delete product")
        return jsonify({"message": "Failed to delete product"}), 500
    finally:
        cursor.close()

@admin_bp.route("/admin/product/edit/<int:prod_id>", methods=["POST"])
@admin_required()
def edit_product(prod_id):
    data = request.json
    if not data:
        return jsonify({"message": "Data required"}), 400

    prod_name = data.get("prod_name")
    des = data.get("des")
    price = data.get("price")
    image = data.get("image")

    db = current_app.config["db"]
    cursor = db.cursor()

    try:
        cursor.execute(
            """
            UPDATE products 
            SET prod_name = %s, des = %s, price = %s, image = %s 
            WHERE prod_id = %s
            """,
            (prod_name, des, price, image, prod_id)
        )
        db.commit()
        return jsonify({"message": "Product updated successfully!"}), 200

    except Exception:
        db.rollback()
        current_app.logger.exception("Failed to update product")
        return jsonify({"message": "Update failed"}), 500

    finally:
        cursor.close()

@admin_bp.route("/admin/customers", methods=["GET"])
@admin_required()
def customers():
    db = current_app.config["db"]
    cursor = db.cursor(dictionary=True, buffered=True)
    
    cursor.execute("SELECT id, username, email FROM users WHERE role = 'user'")
    users = cursor.fetchall()
    
    cursor.close()
    
    return render_template("admin_customers.html", users=users)

@admin_bp.route("/admin/orders", methods=["GET"])
@admin_required()
def admin_orders():
    db = current_app.config["db"]
    cursor = db.cursor(dictionary=True, buffered=True)
    
    cursor.execute("""
        SELECT o.order_id, o.total_amount, o.payment_status, o.created_at, 
               COALESCE(c.username, 'Unknown User') AS user_name 
        FROM orders o 
        LEFT JOIN users c ON o.user_id = c.id
        ORDER BY o.order_id DESC
    """)
    orders = cursor.fetchall()
    cursor.close()
    
    return render_template("admin_orders.html", orders=orders)