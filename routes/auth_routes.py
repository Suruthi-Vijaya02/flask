from flask import Blueprint, request, jsonify, session, current_app
from flask_jwt_extended import create_access_token

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "Data is required"}), 400

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username:
        return jsonify({"message": "Username is required"}), 400
    if not email:
        return jsonify({"message": "Email is required"}), 400
    if not password:
        return jsonify({"message": "Password is required"}), 400

    db = current_app.config["db"]
    cursor = db.cursor()

    try:
        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return jsonify({"message": "Email already exists"}), 400

        # Saving password as plain text directly
        cursor.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
            (username, email, password)
        )
        db.commit()

        user_id = cursor.lastrowid
        session["user_id"] = user_id

        return jsonify({"message": "User registered successfully"}), 201

    except Exception:
        db.rollback()
        current_app.logger.exception("Registration failed")
        return jsonify({"message": "Registration failed"}), 500

    finally:
        cursor.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"message": "Data is required"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email:
        return jsonify({"email": "Email is required"}), 400
    if not password:
        return jsonify({"password": "Password is required"}), 400

    db = current_app.config["db"]
    cursor = db.cursor()

    try:
        cursor.execute(
            "SELECT id, password, role FROM users WHERE email=%s",
            (email,)
        )
        user = cursor.fetchone()
        cursor.fetchall()
        
        if not user:
            return jsonify({"message": "User not found"}), 401

        user_id, stored_password, role = user

        # Direct plain text comparison
        if password != stored_password:
            return jsonify({"message": "Invalid password"}), 401

        # Keep your existing session-based website working.
        session["user_id"] = user_id

        # Create a JWT for clients that use token authentication.
        access_token = create_access_token(
            identity=str(user_id),
            additional_claims={"role": role}
        )
        
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "role": role
        }), 200

    finally:
        cursor.close()