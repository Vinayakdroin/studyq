from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, FloatField, IntegerField, HiddenField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = RadioField('Register as', choices=[('student', 'Student'), ('tutor', 'Tutor')], default='student')
    submit = SubmitField('Register')


class TutorProfileForm(FlaskForm):
    bio = TextAreaField('Bio (Tell students about yourself and your teaching approach)', validators=[Length(max=1000)])
    hourly_rate = FloatField('Hourly Rate (€)', validators=[DataRequired(), NumberRange(min=5, max=200)])
    years_experience = IntegerField('Years of Experience', validators=[Optional(), NumberRange(min=0, max=50)])
    specialization = SelectField('Specialization', choices=[
        ('', 'Select Specialization'),
        ('Conversation', 'Conversation Practice'), 
        ('Grammar', 'Grammar'), 
        ('Business German', 'Business German'),
        ('Exam Preparation', 'Exam Preparation'),
        ('Beginners', 'Beginners'),
        ('Children', 'Teaching Children'),
        ('Culture', 'German Culture')
    ], validators=[Optional()])
    proficiency_level = SelectField('Proficiency Level', choices=[
        ('', 'Select Level'),
        ('Beginner', 'Beginner (A1-A2)'),
        ('Intermediate', 'Intermediate (B1-B2)'),
        ('Advanced', 'Advanced (C1-C2)'),
        ('Native', 'Native Speaker')
    ], validators=[Optional()])
    profile_image = StringField('Profile Image URL', validators=[Optional()])
    submit = SubmitField('Update Profile')


class BookingForm(FlaskForm):
    booking_date = SelectField('Select Date', validators=[DataRequired()])
    start_time = SelectField('Start Time', validators=[DataRequired()])
    end_time = SelectField('End Time', validators=[DataRequired()])
    submit = SubmitField('Book Session')


class AvailabilityForm(FlaskForm):
    day_of_week = SelectField('Day of Week', choices=[
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday')
    ], coerce=int, validators=[DataRequired()])
    start_time = StringField('Start Time (HH:MM)', validators=[DataRequired()]) 
    end_time = StringField('End Time (HH:MM)', validators=[DataRequired()])
    submit = SubmitField('Add Availability')


class ReviewForm(FlaskForm):
    rating = RadioField('Rating', choices=[
        ('5', '5 - Excellent'),
        ('4', '4 - Very Good'),
        ('3', '3 - Good'),
        ('2', '2 - Fair'),
        ('1', '1 - Poor')
    ], validators=[DataRequired()], coerce=int)
    comment = TextAreaField('Comment', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Submit Review')


class PaymentForm(FlaskForm):
    card_number = StringField('Card Number', validators=[DataRequired(), Length(min=16, max=16)])
    card_expiry = StringField('Expiry (MM/YY)', validators=[DataRequired(), Length(min=5, max=5)])
    card_cvc = StringField('CVC', validators=[DataRequired(), Length(min=3, max=3)])
    cardholder_name = StringField('Cardholder Name', validators=[DataRequired()])
    submit = SubmitField('Pay Now')
