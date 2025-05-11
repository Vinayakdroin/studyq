from datetime import datetime
from enum import Enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


class Role(Enum):
    STUDENT = "student"
    TUTOR = "tutor"
    ADMIN = "admin"


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(Role), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with other models
    tutor_profile = db.relationship('TutorProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    bookings_as_student = db.relationship('Booking', foreign_keys='Booking.student_id', backref='student')
    reviews_given = db.relationship('Review', foreign_keys='Review.student_id', backref='student')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_student(self):
        return self.role == Role.STUDENT
        
    def is_tutor(self):
        return self.role == Role.TUTOR
        
    def is_admin(self):
        return self.role == Role.ADMIN


class TutorProfile(db.Model):
    __tablename__ = 'tutor_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    hourly_rate = db.Column(db.Float, nullable=False, default=25.0)
    years_experience = db.Column(db.Integer, nullable=True)
    profile_image = db.Column(db.String(200), nullable=True)
    proficiency_level = db.Column(db.String(50), nullable=True)  # Beginner, Intermediate, Advanced, Native
    specialization = db.Column(db.String(100), nullable=True)  # Conversation, Grammar, Business German, etc.
    
    # Relationships
    availability = db.relationship('Availability', backref='tutor_profile', cascade='all, delete-orphan')
    bookings = db.relationship('Booking', backref='tutor_profile', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='tutor_profile', cascade='all, delete-orphan')
    
    @property
    def avg_rating(self):
        if not self.reviews:
            return 0
        return sum(review.rating for review in self.reviews) / len(self.reviews)
    
    @property
    def review_count(self):
        return len(self.reviews)


class Availability(db.Model):
    __tablename__ = 'availability'
    
    id = db.Column(db.Integer, primary_key=True)
    tutor_profile_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0 = Monday, 6 = Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)


class BookingStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Booking(db.Model):
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tutor_profile_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.Enum(BookingStatus), default=BookingStatus.PENDING)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with payment
    payment = db.relationship('Payment', backref='booking', uselist=False, cascade='all, delete-orphan')


class PaymentStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    REFUNDED = "refunded"
    FAILED = "failed"


class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="EUR")
    platform_fee = db.Column(db.Float, nullable=False)  # 20% of amount
    tutor_payout = db.Column(db.Float, nullable=False)  # 80% of amount
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_id = db.Column(db.String(100), nullable=True)
    payment_date = db.Column(db.DateTime, nullable=True)
    
    @staticmethod
    def calculate_fee(amount):
        """Calculate platform fee (20%) and tutor payout (80%)"""
        fee = round(amount * 0.2, 2)
        payout = round(amount * 0.8, 2)
        return fee, payout


class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tutor_profile_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
