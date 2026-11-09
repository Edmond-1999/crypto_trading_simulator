
import re

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)
from app.services.auth_service import authenticate_user

from app.extensions import db
from app.models import User

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/api/v1/auth"
)


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send a JSON request body."}), 400

    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({
            "error": "Email and password are required."
        }), 400

    email = email.strip().lower()

    if len(email) > 255 or not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+", email
    ):
        return jsonify({"error": "Enter a valid email address."}), 400

    if len(password) < 12 or len(password) > 128:
        return jsonify({
            "error": "Password must be between 12 and 128 characters."
        }), 400

    user = User(
        email=email,
        password_hash=generate_password_hash(password)
    )

    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "error": "An account with that email already exists."
        }), 409

    return jsonify({
        "message": "Account created successfully.",
        "user": {
            "id": user.id,
            "email": user.email
        }
    }), 201

@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send a JSON request body."}), 400

    email = data.get("email")
    password = data.get("password")

    if not isinstance(email, str) or not isinstance(password, str):
        return jsonify({"error": "Email and password are required."}), 400

    if len(email) > 255 or len(password) > 128:
        return jsonify({"error": "Invalid email or password"}), 401

    user = authenticate_user(email, password)

    if user is None:
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = create_access_token(identity=str(user.id))

    return jsonify({
        "message": "Login successful.",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email
        }
    }), 200

@auth_bp.get("/me")
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()

    user = db.session.get(User, int(user_id))

    if user is None:
        return jsonify({"error": "User not found."}), 404

    return jsonify({
        "user": {
            "id": user.id,
            "email": user.email,
            "created_at": user.created_at.isoformat()
        }
    }), 200
