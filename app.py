import os
import logging
from datetime import datetime as dt
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize SQLAlchemy with a base class
class Base(DeclarativeBase):
    pass

# Initialize Flask extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create Flask application
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "german-tutors-dev-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///german_tutors.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Custom Jinja filter
def format_datetime(value, format='%Y-%m-%d'):
    if isinstance(value, dt):
        return value.strftime(format)
    try:
        return dt.strptime(value, '%Y-%m-%d').strftime(format)
    except Exception as e:
        return value

# Register it with Jinja
app.jinja_env.filters['datetime'] = format_datetime

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Import routes after app is created to avoid circular imports
from routes import *  # noqa: E402, F403
import models  # noqa: E402, F401

# Create database tables
with app.app_context():
    db.create_all()
    
    # Check if admin user exists, create if not
    from models import User, Role
    admin = User.query.filter_by(username="admin").first()
    if not admin:
        from werkzeug.security import generate_password_hash
        admin_user = User(
            username="admin",
            password_hash=generate_password_hash("admin123"),
            email="admin@germantutors.com",
            role=Role.ADMIN,
            created_at=dt.utcnow()
        )
        db.session.add(admin_user)
        db.session.commit()
        app.logger.info("Admin user created")

if __name__ == "__main__":
    app.run(debug=True)