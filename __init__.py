import hmac
import os
import secrets
from datetime import datetime
from urllib.parse import urlparse

from flask import Flask, abort, render_template, request, session
from markupsafe import Markup


def csrf_token():
  if "_csrf" not in session:
    session["_csrf"] = secrets.token_hex(16)
  return session["_csrf"]	


def csrf_field():
	"""Build a hidden form field containing the current CSRF token."""
	return Markup('<input type="hidden" name="_csrf" value="{}">').format(
		(csrf_token())
	)


def create_app(test_config=None):
	"""Create the Flask application and enable CSRF validation."""
	app = Flask(__name__,instance_relative_config=True)
	app.config.from_mapping(
    SECRET_KEY ="dev-only-change-me",
    DATABASE= os.path.join(app.instance_path, "bookmarkbox.sqlite"),
    SESSION_SAMESITE="Lax",
  )
if test_config is None:
  app.config.from_pyfile("config.py", silent=True)
else:
  app.config.from_mapping(test_config)

os.makedirs(app.instance_path, exist_ok=True)

from . import auth, bookmarks, db

db.init_app(app)
app.register_blueprint(auth.bp)
app.register_blueprint(bookmarks.bp)

@app.route("/hello")
def hello():
  return "Hello from Flask!"

@app.before_request
def check_csrf_token():
  if request.method == "POST":
    sent =request.form.get("_csrf", "").encode()
    expected = session.get("_csrf", "").encode()
    if not expected or not hmac.compare_digest(sent, expected):
      abort(400, "your form expired or was invalid. Please go back and try again.")

@app.after_request
def add_security_headers(response):
  response.headers["X-Content-Type-Options"] = "nosniff"
  return response

@app.errorhandler(400)
@app.errorhandler(403)
@app.errorhandler(404)
def show_error(error):
  return render_template("error.html", error=error), error.code

app.add_template_global(csrf_token)
app.add_template_global(csrf_field)

@app.context_processor
def inject_year():
  return {"year": datetime.now().year}

@app.template_filter("domain")
def domain_filters(url):
  return urlparse(url).netloc
  return app