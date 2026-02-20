from flask import Blueprint, request, redirect, flash
from flask_login import login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User
import mysql.connector

auth_bp = Blueprint("auth", __name__)

# ================= REGISTER =================
@auth_bp.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    confirm = request.form.get("confirm_password")

    if not username or not password:
        flash("Semua field wajib diisi", "danger")
        return redirect("/")

    if password != confirm:
        flash("Password tidak cocok", "danger")
        return redirect("/")

    if User.get_by_username(username):
        flash("Username sudah digunakan", "danger")
        return redirect("/")

    password_hash = generate_password_hash(password)

    try:
        User.create(username, password_hash)
        flash("Registrasi berhasil. Silakan login.", "success")
    except mysql.connector.Error:
        flash("Terjadi kesalahan database.", "danger")

    return redirect("/")


# ================= LOGIN =================
@auth_bp.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    user = User.get_by_username(username)

    if user and check_password_hash(user["password"], password):

        login_user(User(user["user_id"], user["username"], user["role"]))

        if user["role"] == "admin":
            return redirect("/admin")
        else:
            return redirect("/user")

    flash("Username atau password salah", "danger")
    return redirect("/")


# ================= LOGOUT =================
@auth_bp.route("/logout")
def logout():
    logout_user()
    return redirect("/")
