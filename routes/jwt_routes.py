
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

jwt_bp = Blueprint("jwt", __name__)


@jwt_bp.route("/api/me", methods=["GET"])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()

    return jsonify({
        "message": "You are authenticated",
        "user_id": user_id
    }), 200

