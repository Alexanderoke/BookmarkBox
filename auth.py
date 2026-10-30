import functools
import sqlite3

from flask import (Blueprint, flash, g, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash
from .db import get_db

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.route("/register", methods =("GET", "POST"))
def register():
  if request.method =="POST":
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    error = None
    if not username:
      error ="Username is required."
    elif len(password) < 6:
      error = "password must be atleast 6 characters."

    if error is None:
      db = get_db()
      try:
        db.execute(
          "INSERT INTO user (username, password_hash) VALUES (?, ?)",
          (username, generate_password_hash(password)),
        )
        db.commit()
      except sqlite3.IntegrityError:
        error = f"The username {username} is already taken."
      else:
        flash("Account created. Please log in.")
        return redirect(url_for("auth.login"))

      flash(error)

    return render_template("auth/register.html")

@bp.route("/login", methods=("GET", "POST"))
def login():
  if request.method == "POST":
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    user = get_db().execute(
      "SELECT * FROM user WHERE username = ?", (username,)
    ).fetchone()

    if user is None or not check_password_hash(user["password_hash"], password):
      flash("Incorrect username or password.")
    else:
      session.clear()
      session["user_id"] =user["id"]
      return redirect(url_for("bookmarks.index"))

return render_template("auth/login.html")


@bp.route("/logout", methods=("POST",))
def logout():
  session.clear()
  flash("You have been logged out")
  return redirect(url_for("auth.login"))

@bp.before_app_request
def load_logged_in_user():
  user_id = session.get("user_id")
  if user_id is None:
    g.user =None
  else:
    g.user = get_db().execute(
      "SELECT id, username FROM user WHERE id = ?", (user_id,)     
    ).fetchone()

def login_required(view):
  
  @functools.wraps(view)
  def wrapped_view(**kwargs):
    if g.user is None:
      flash("Please login first.")
      return redirect(url_for("auth.login"))
    return view(**kwargs)

  return wrapped_view    
