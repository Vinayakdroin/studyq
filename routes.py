import datetime
import uuid
from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from sqlalchemy import or_
from sqlalchemy.orm import aliased

from app import app, db
from models import User, Role, TutorProfile, Availability, Booking, BookingStatus, Payment, PaymentStatus, Review
from forms import LoginForm, RegistrationForm, TutorProfileForm, BookingForm, ReviewForm, AvailabilityForm, PaymentForm
from utils import calculate_session_price, get_available_slots


@app.route('/')
def index():
    # Featured tutors (top rated)
    featured_tutors = db.session.query(TutorProfile, User) \
        .join(User, User.id == TutorProfile.user_id) \
        .join(Review, Review.tutor_profile_id == TutorProfile.id, isouter=True) \
        .group_by(TutorProfile.id) \
        .order_by(db.func.avg(Review.rating).desc()) \
        .limit(4) \
        .all()
    
    return render_template('index.html', featured_tutors=featured_tutors)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            role=Role.STUDENT if form.role.data == 'student' else Role.TUTOR,
            created_at=datetime.datetime.utcnow()
        )
        user.set_password(form.password.data)
        db.session.add(user)
        
        # If user is a tutor, create empty profile
        if form.role.data == 'tutor':
            profile = TutorProfile(user=user, hourly_rate=25.0)
            db.session.add(profile)
            
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin():
        return redirect(url_for('admin_dashboard'))
    elif current_user.is_tutor():
        return redirect(url_for('tutor_dashboard'))
    else:
        return redirect(url_for('student_dashboard'))


@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if not current_user.is_student():
        flash('Access denied: You are not registered as a student', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get upcoming bookings
    upcoming_bookings = db.session.query(Booking, TutorProfile, User) \
        .join(TutorProfile, TutorProfile.id == Booking.tutor_profile_id) \
        .join(User, User.id == TutorProfile.user_id) \
        .filter(Booking.student_id == current_user.id) \
        .filter(Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING])) \
        .filter(Booking.booking_date >= datetime.date.today()) \
        .order_by(Booking.booking_date, Booking.start_time) \
        .all()
    
    # Get past bookings for review
    past_bookings = db.session.query(Booking, TutorProfile, User, Review) \
        .join(TutorProfile, TutorProfile.id == Booking.tutor_profile_id) \
        .join(User, User.id == TutorProfile.user_id) \
        .outerjoin(Review, (Review.booking_id == Booking.id) & (Review.student_id == current_user.id)) \
        .filter(Booking.student_id == current_user.id) \
        .filter(Booking.status == BookingStatus.COMPLETED) \
        .filter(or_(Review.id == None, Booking.booking_date < datetime.date.today())) \
        .order_by(Booking.booking_date.desc()) \
        .limit(5) \
        .all()
    
    return render_template('student/dashboard.html', 
                           upcoming_bookings=upcoming_bookings,
                           past_bookings=past_bookings)


@app.route('/student/tutors')
@login_required
def student_tutor_list():
    if not current_user.is_student():
        flash('Access denied: You are not registered as a student', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get filter parameters
    min_price = request.args.get('min_price', type=float, default=0)
    max_price = request.args.get('max_price', type=float, default=1000)
    min_rating = request.args.get('min_rating', type=int, default=0)
    specialization = request.args.get('specialization', type=str, default=None)
    
    # Query tutors with filters
    query = db.session.query(TutorProfile, User) \
        .join(User, User.id == TutorProfile.user_id) \
        .filter(TutorProfile.hourly_rate >= min_price) \
        .filter(TutorProfile.hourly_rate <= max_price)
    
    if specialization:
        query = query.filter(TutorProfile.specialization == specialization)
    
    tutors = query.all()
    
    # Filter by rating (can't do this in SQL with avg calculation)
    if min_rating > 0:
        tutors = [(profile, user) for profile, user in tutors if profile.avg_rating >= min_rating]
    
    # Get all available specializations for filter dropdown
    specializations = db.session.query(TutorProfile.specialization) \
        .filter(TutorProfile.specialization != None) \
        .distinct() \
        .all()
    specializations = [s[0] for s in specializations if s[0]]
    
    return render_template('student/tutor_list.html', 
                           tutors=tutors,
                           specializations=specializations,
                           min_price=min_price,
                           max_price=max_price,
                           min_rating=min_rating,
                           current_specialization=specialization)


@app.route('/student/tutor/<int:tutor_id>')
@login_required
def student_tutor_profile(tutor_id):
    if not current_user.is_student():
        flash('Access denied: You are not registered as a student', 'danger')
        return redirect(url_for('dashboard'))
    
    tutor_profile = TutorProfile.query.get_or_404(tutor_id)
    tutor_user = User.query.get_or_404(tutor_profile.user_id)
    
    # Get tutor reviews
    reviews = db.session.query(Review, User) \
        .join(User, User.id == Review.student_id) \
        .filter(Review.tutor_profile_id == tutor_id) \
        .order_by(Review.created_at.desc()) \
        .all()
    
    # Get availability for next 7 days
    today = datetime.date.today()
    dates = [today + datetime.timedelta(days=i) for i in range(7)]
    availability = {}
    
    for date in dates:
        day_of_week = date.weekday()  # 0 = Monday, 6 = Sunday
        slots = Availability.query.filter_by(
            tutor_profile_id=tutor_id,
            day_of_week=day_of_week,
            is_available=True
        ).all()
        
        # Check if any slots are already booked
        date_bookings = Booking.query.filter_by(
            tutor_profile_id=tutor_id,
            booking_date=date,
            status=BookingStatus.CONFIRMED
        ).all()
        
        booked_slots = [(b.start_time, b.end_time) for b in date_bookings]
        available_slots = []
        
        for slot in slots:
            # Check if slot overlaps with any booked slots
            is_available = True
            for booked_start, booked_end in booked_slots:
                if not (slot.end_time <= booked_start or slot.start_time >= booked_end):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append({
                    'start': slot.start_time.strftime('%H:%M'),
                    'end': slot.end_time.strftime('%H:%M')
                })
        
        if available_slots:
            availability[date.strftime('%Y-%m-%d')] = available_slots
    
    return render_template('student/tutor_profile.html',
                           tutor_profile=tutor_profile,
                           tutor_user=tutor_user,
                           reviews=reviews,
                           availability=availability)


@app.route('/student/book/<int:tutor_id>', methods=['GET', 'POST'])
@login_required
def student_book_tutor(tutor_id):
    if not current_user.is_student():
        flash('Access denied: You are not registered as a student', 'danger')
        return redirect(url_for('dashboard'))
    
    tutor_profile = TutorProfile.query.get_or_404(tutor_id)
    tutor_user = User.query.get_or_404(tutor_profile.user_id)
    
    form = BookingForm()
    
    # Populate the available dates dropdown
    today = datetime.date.today()
    available_dates = []
    
    for i in range(14):  # Next 14 days
        check_date = today + datetime.timedelta(days=i)
        day_of_week = check_date.weekday()
        
        # Check if tutor has availability on this day
        if Availability.query.filter_by(
            tutor_profile_id=tutor_id,
            day_of_week=day_of_week,
            is_available=True
        ).first():
            available_dates.append((check_date.strftime('%Y-%m-%d'), check_date.strftime('%A, %b %d')))
    
    form.booking_date.choices = available_dates
    
    if form.validate_on_submit():
        # Parse date and times
        booking_date = datetime.datetime.strptime(form.booking_date.data, '%Y-%m-%d').date()
        start_time = datetime.datetime.strptime(form.start_time.data, '%H:%M').time()
        end_time = datetime.datetime.strptime(form.end_time.data, '%H:%M').time()
        
        # Check if slot is available
        day_of_week = booking_date.weekday()
        slot_available = Availability.query.filter_by(
            tutor_profile_id=tutor_id,
            day_of_week=day_of_week,
            is_available=True
        ).filter(
            Availability.start_time <= start_time,
            Availability.end_time >= end_time
        ).first()
        
        if not slot_available:
            flash('This time slot is not available', 'danger')
            return redirect(url_for('student_book_tutor', tutor_id=tutor_id))
        
        # Check if slot is already booked
        existing_booking = Booking.query.filter_by(
            tutor_profile_id=tutor_id,
            booking_date=booking_date,
            status=BookingStatus.CONFIRMED
        ).filter(
            or_(
                (Booking.start_time <= start_time) & (Booking.end_time > start_time),
                (Booking.start_time < end_time) & (Booking.end_time >= end_time),
                (Booking.start_time >= start_time) & (Booking.end_time <= end_time)
            )
        ).first()
        
        if existing_booking:
            flash('This time slot has already been booked', 'danger')
            return redirect(url_for('student_book_tutor', tutor_id=tutor_id))
        
        # Calculate duration and price
        start_dt = datetime.datetime.combine(booking_date, start_time)
        end_dt = datetime.datetime.combine(booking_date, end_time)
        duration_hours = (end_dt - start_dt).total_seconds() / 3600
        total_price = tutor_profile.hourly_rate * duration_hours
        
        # Create booking
        booking = Booking(
            student_id=current_user.id,
            tutor_profile_id=tutor_id,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            status=BookingStatus.PENDING
        )
        db.session.add(booking)
        db.session.commit()
        
        # Redirect to payment page
        return redirect(url_for('student_payment', booking_id=booking.id))
    
    return render_template('student/booking.html',
                           form=form,
                           tutor_profile=tutor_profile,
                           tutor_user=tutor_user)


@app.route('/student/get_available_times', methods=['POST'])
@login_required
def get_available_times():
    tutor_id = request.json.get('tutor_id')
    date_str = request.json.get('date')
    
    if not tutor_id or not date_str:
        return jsonify({'error': 'Missing parameters'}), 400
    
    booking_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    day_of_week = booking_date.weekday()
    
    # Get available slots for this day
    slots = Availability.query.filter_by(
        tutor_profile_id=tutor_id,
        day_of_week=day_of_week,
        is_available=True
    ).all()
    
    # Check for existing bookings
    bookings = Booking.query.filter_by(
        tutor_profile_id=tutor_id,
        booking_date=booking_date,
        status=BookingStatus.CONFIRMED
    ).all()
    
    booked_times = [(b.start_time, b.end_time) for b in bookings]
    
    # Format available times
    available_times = []
    for slot in slots:
        slot_start = slot.start_time
        slot_end = slot.end_time
        
        # Check if slot overlaps with any booking
        is_available = True
        for booked_start, booked_end in booked_times:
            if not (slot_end <= booked_start or slot_start >= booked_end):
                is_available = False
                break
        
        if is_available:
            available_times.append({
                'start': slot_start.strftime('%H:%M'),
                'end': slot_end.strftime('%H:%M')
            })
    
    return jsonify({'available_times': available_times})


@app.route('/student/payment/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def student_payment(booking_id):
    if not current_user.is_student():
        flash('Access denied: You are not registered as a student', 'danger')
        return redirect(url_for('dashboard'))
    
    booking = Booking.query.get_or_404(booking_id)
    
    # Verify this booking belongs to the current user
    if booking.student_id != current_user.id:
        flash('You do not have permission to access this booking', 'danger')
        return redirect(url_for('student_dashboard'))
    
    # Check if payment already exists
    if Payment.query.filter_by(booking_id=booking_id).first():
        flash('Payment has already been processed for this booking', 'info')
        return redirect(url_for('student_dashboard'))
    
    tutor_profile = TutorProfile.query.get(booking.tutor_profile_id)
    tutor = User.query.get(tutor_profile.user_id)
    
    # Calculate price
    start_dt = datetime.datetime.combine(booking.booking_date, booking.start_time)
    end_dt = datetime.datetime.combine(booking.booking_date, booking.end_time)
    duration_hours = (end_dt - start_dt).total_seconds() / 3600
    total_price = round(tutor_profile.hourly_rate * duration_hours, 2)
    
    platform_fee, tutor_payout = Payment.calculate_fee(total_price)
    
    form = PaymentForm()
    
    if form.validate_on_submit():
        # Process payment (mock)
        transaction_id = f"TRANS-{uuid.uuid4().hex[:8].upper()}"
        
        # Create payment record
        payment = Payment(
            booking_id=booking.id,
            amount=total_price,
            platform_fee=platform_fee,
            tutor_payout=tutor_payout,
            status=PaymentStatus.COMPLETED,
            transaction_id=transaction_id,
            payment_date=datetime.datetime.now()
        )
        
        # Update booking status
        booking.status = BookingStatus.CONFIRMED
        
        db.session.add(payment)
        db.session.commit()
        
        flash('Your payment has been processed and the session is confirmed!', 'success')
        return redirect(url_for('student_dashboard'))
    
    return render_template('student/payment.html',
                           booking=booking,
                           tutor_profile=tutor_profile,
                           tutor=tutor,
                           total_price=total_price,
                           platform_fee=platform_fee,
                           tutor_payout=tutor_payout,
                           form=form)


@app.route('/student/review/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def student_review(booking_id):
    if not current_user.is_student():
        flash('Access denied: You are not registered as a student', 'danger')
        return redirect(url_for('dashboard'))
    
    booking = Booking.query.get_or_404(booking_id)
    
    # Verify this booking belongs to the current user and is completed
    if booking.student_id != current_user.id:
        flash('You do not have permission to review this session', 'danger')
        return redirect(url_for('student_dashboard'))
    
    if booking.status != BookingStatus.COMPLETED:
        flash('You can only review completed sessions', 'warning')
        return redirect(url_for('student_dashboard'))
    
    # Check if already reviewed
    existing_review = Review.query.filter_by(booking_id=booking_id, student_id=current_user.id).first()
    if existing_review:
        flash('You have already reviewed this session', 'info')
        return redirect(url_for('student_dashboard'))
    
    tutor_profile = TutorProfile.query.get(booking.tutor_profile_id)
    tutor = User.query.get(tutor_profile.user_id)
    
    form = ReviewForm()
    
    if form.validate_on_submit():
        review = Review(
            student_id=current_user.id,
            tutor_profile_id=tutor_profile.id,
            booking_id=booking.id,
            rating=form.rating.data,
            comment=form.comment.data
        )
        db.session.add(review)
        db.session.commit()
        
        flash('Your review has been submitted. Thank you for your feedback!', 'success')
        return redirect(url_for('student_dashboard'))
    
    return render_template('student/review.html',
                           form=form,
                           booking=booking,
                           tutor_profile=tutor_profile,
                           tutor=tutor)


@app.route('/tutor/dashboard')
@login_required
def tutor_dashboard():
    if not current_user.is_tutor():
        flash('Access denied: You are not registered as a tutor', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get tutor profile
    tutor_profile = TutorProfile.query.filter_by(user_id=current_user.id).first()
    
    if not tutor_profile:
        # Create a basic profile if it doesn't exist
        tutor_profile = TutorProfile(user_id=current_user.id, hourly_rate=25.0)
        db.session.add(tutor_profile)
        db.session.commit()
    
    # Get upcoming bookings
    upcoming_bookings = db.session.query(Booking, User) \
        .join(User, User.id == Booking.student_id) \
        .filter(Booking.tutor_profile_id == tutor_profile.id) \
        .filter(Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING])) \
        .filter(Booking.booking_date >= datetime.date.today()) \
        .order_by(Booking.booking_date, Booking.start_time) \
        .all()
    
    # Get recent payments
    recent_payments = db.session.query(Payment, Booking, User) \
        .join(Booking, Booking.id == Payment.booking_id) \
        .join(User, User.id == Booking.student_id) \
        .filter(Booking.tutor_profile_id == tutor_profile.id) \
        .filter(Payment.status == PaymentStatus.COMPLETED) \
        .order_by(Payment.payment_date.desc()) \
        .limit(5) \
        .all()
    
    # Calculate total earnings
    total_earnings = db.session.query(db.func.sum(Payment.tutor_payout)) \
        .join(Booking, Booking.id == Payment.booking_id) \
        .filter(Booking.tutor_profile_id == tutor_profile.id) \
        .filter(Payment.status == PaymentStatus.COMPLETED) \
        .scalar() or 0
    
    # Get recent reviews
    recent_reviews = db.session.query(Review, User) \
        .join(User, User.id == Review.student_id) \
        .filter(Review.tutor_profile_id == tutor_profile.id) \
        .order_by(Review.created_at.desc()) \
        .limit(3) \
        .all()
    
    return render_template('tutor/dashboard.html',
                           tutor_profile=tutor_profile,
                           upcoming_bookings=upcoming_bookings,
                           recent_payments=recent_payments,
                           total_earnings=total_earnings,
                           recent_reviews=recent_reviews)


@app.route('/tutor/profile', methods=['GET', 'POST'])
@login_required
def tutor_profile():
    if not current_user.is_tutor():
        flash('Access denied: You are not registered as a tutor', 'danger')
        return redirect(url_for('dashboard'))
    
    tutor_profile = TutorProfile.query.filter_by(user_id=current_user.id).first()
    
    if not tutor_profile:
        tutor_profile = TutorProfile(user_id=current_user.id, hourly_rate=25.0)
        db.session.add(tutor_profile)
        db.session.commit()
    
    form = TutorProfileForm(obj=tutor_profile)
    
    if form.validate_on_submit():
        form.populate_obj(tutor_profile)
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('tutor_dashboard'))
    
    return render_template('tutor/profile.html', form=form, tutor_profile=tutor_profile)


@app.route('/tutor/schedule', methods=['GET', 'POST'])
@login_required
def tutor_schedule():
    if not current_user.is_tutor():
        flash('Access denied: You are not registered as a tutor', 'danger')
        return redirect(url_for('dashboard'))
    
    tutor_profile = TutorProfile.query.filter_by(user_id=current_user.id).first()
    
    if not tutor_profile:
        flash('You need to set up your profile first', 'warning')
        return redirect(url_for('tutor_profile'))
    
    form = AvailabilityForm()
    
    if form.validate_on_submit():
        day = form.day_of_week.data
        start_time = datetime.datetime.strptime(form.start_time.data, '%H:%M').time()
        end_time = datetime.datetime.strptime(form.end_time.data, '%H:%M').time()
        
        # Validate times
        if start_time >= end_time:
            flash('End time must be after start time', 'danger')
        else:
            # Check for overlapping slots
            overlapping = Availability.query.filter_by(
                tutor_profile_id=tutor_profile.id,
                day_of_week=day,
                is_available=True
            ).filter(
                or_(
                    (Availability.start_time <= start_time) & (Availability.end_time > start_time),
                    (Availability.start_time < end_time) & (Availability.end_time >= end_time),
                    (Availability.start_time >= start_time) & (Availability.end_time <= end_time)
                )
            ).first()
            
            if overlapping:
                flash('This time slot overlaps with an existing availability', 'danger')
            else:
                availability = Availability(
                    tutor_profile_id=tutor_profile.id,
                    day_of_week=day,
                    start_time=start_time,
                    end_time=end_time,
                    is_available=True
                )
                db.session.add(availability)
                db.session.commit()
                flash('Availability added successfully!', 'success')
    
    # Get current availability
    availabilities = {}
    for day in range(7):  # 0 = Monday, 6 = Sunday
        day_slots = Availability.query.filter_by(
            tutor_profile_id=tutor_profile.id,
            day_of_week=day,
            is_available=True
        ).order_by(Availability.start_time).all()
        
        availabilities[day] = day_slots
    
    # Get upcoming bookings
    upcoming_bookings = Booking.query.filter_by(
        tutor_profile_id=tutor_profile.id,
        status=BookingStatus.CONFIRMED
    ).filter(
        Booking.booking_date >= datetime.date.today()
    ).order_by(Booking.booking_date, Booking.start_time).all()
    
    return render_template('tutor/schedule.html',
                           form=form,
                           availabilities=availabilities,
                           upcoming_bookings=upcoming_bookings,
                           day_names=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])


@app.route('/tutor/availability/delete/<int:availability_id>', methods=['POST'])
@login_required
def delete_availability(availability_id):
    if not current_user.is_tutor():
        flash('Access denied: You are not registered as a tutor', 'danger')
        return redirect(url_for('dashboard'))
    
    availability = Availability.query.get_or_404(availability_id)
    tutor_profile = TutorProfile.query.filter_by(user_id=current_user.id).first()
    
    if availability.tutor_profile_id != tutor_profile.id:
        flash('You do not have permission to delete this availability', 'danger')
        return redirect(url_for('tutor_schedule'))
    
    db.session.delete(availability)
    db.session.commit()
    
    flash('Availability removed successfully!', 'success')
    return redirect(url_for('tutor_schedule'))


@app.route('/tutor/earnings')
@login_required
def tutor_earnings():
    if not current_user.is_tutor():
        flash('Access denied: You are not registered as a tutor', 'danger')
        return redirect(url_for('dashboard'))
    
    tutor_profile = TutorProfile.query.filter_by(user_id=current_user.id).first()
    
    if not tutor_profile:
        flash('You need to set up your profile first', 'warning')
        return redirect(url_for('tutor_profile'))
    
    # Get all completed payments
    payments = db.session.query(Payment, Booking, User) \
        .join(Booking, Booking.id == Payment.booking_id) \
        .join(User, User.id == Booking.student_id) \
        .filter(Booking.tutor_profile_id == tutor_profile.id) \
        .filter(Payment.status == PaymentStatus.COMPLETED) \
        .order_by(Payment.payment_date.desc()) \
        .all()
    
    # Calculate total earnings
    total_earnings = sum(payment.tutor_payout for payment, _, _ in payments)
    
    # Calculate monthly earnings for chart
    monthly_earnings = {}
    for payment, booking, _ in payments:
        month = payment.payment_date.strftime('%B %Y')
        if month in monthly_earnings:
            monthly_earnings[month] += payment.tutor_payout
        else:
            monthly_earnings[month] = payment.tutor_payout
    
    # Sort months chronologically
    sorted_months = sorted(monthly_earnings.keys(), 
                          key=lambda x: datetime.datetime.strptime(x, '%B %Y'))
    chart_data = {
        'labels': sorted_months,
        'data': [monthly_earnings[month] for month in sorted_months]
    }
    
    return render_template('tutor/earnings.html',
                           tutor_profile=tutor_profile,
                           payments=payments,
                           total_earnings=total_earnings,
                           chart_data=chart_data)


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin():
        flash('Access denied: You are not an administrator', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get stats
    tutor_count = User.query.filter_by(role=Role.TUTOR).count()
    student_count = User.query.filter_by(role=Role.STUDENT).count()
    booking_count = Booking.query.filter_by(status=BookingStatus.CONFIRMED).count()
    total_revenue = db.session.query(db.func.sum(Payment.platform_fee)) \
        .filter(Payment.status == PaymentStatus.COMPLETED) \
        .scalar() or 0
    
    Student = aliased(User)
    Tutor = aliased(User)

    recent_bookings = db.session.query(Booking, Student, TutorProfile, Tutor) \
        .join(Student, Student.id == Booking.student_id) \
        .join(TutorProfile, TutorProfile.id == Booking.tutor_profile_id) \
        .join(Tutor, Tutor.id == TutorProfile.user_id) \
        .filter(Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])) \
        .order_by(Booking.created_at.desc()) \
        .limit(10) \
        .all()

    
    Student = aliased(User)
    Tutor = aliased(User)

    recent_payments = db.session.query(Payment, Booking, Student, Tutor) \
        .join(Booking, Booking.id == Payment.booking_id) \
        .join(Student, Student.id == Booking.student_id) \
        .join(TutorProfile, TutorProfile.id == Booking.tutor_profile_id) \
        .join(Tutor, Tutor.id == TutorProfile.user_id) \
        .filter(Payment.status == PaymentStatus.COMPLETED) \
        .order_by(Payment.payment_date.desc()) \
        .limit(10) \
        .all()

    
    # Top tutors by booking count
    top_tutors = db.session.query(
            TutorProfile, 
            User, 
            db.func.count(Booking.id).label('booking_count'),
            db.func.sum(Payment.tutor_payout).label('earnings')
        ) \
        .join(User, User.id == TutorProfile.user_id) \
        .join(Booking, Booking.tutor_profile_id == TutorProfile.id) \
        .join(Payment, Payment.booking_id == Booking.id) \
        .filter(Payment.status == PaymentStatus.COMPLETED) \
        .group_by(TutorProfile.id) \
        .order_by(db.func.count(Booking.id).desc()) \
        .limit(5) \
        .all()
    
    return render_template('admin/dashboard.html',
                           tutor_count=tutor_count,
                           student_count=student_count,
                           booking_count=booking_count,
                           total_revenue=total_revenue,
                           recent_bookings=recent_bookings,
                           recent_payments=recent_payments,
                           top_tutors=top_tutors)


@app.route('/api/complete_booking/<int:booking_id>', methods=['POST'])
@login_required
def complete_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Verify permission
    if current_user.is_student() and booking.student_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403
    
    if current_user.is_tutor():
        tutor_profile = TutorProfile.query.filter_by(user_id=current_user.id).first()
        if not tutor_profile or booking.tutor_profile_id != tutor_profile.id:
            return jsonify({'error': 'Permission denied'}), 403
    
    # Update booking status
    booking.status = BookingStatus.COMPLETED
    db.session.commit()
    
    return jsonify({'success': True})


@app.route('/api/cancel_booking/<int:booking_id>', methods=['POST'])
@login_required
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Verify permission
    if current_user.is_student() and booking.student_id != current_user.id:
        return jsonify({'error': 'Permission denied'}), 403
    
    if current_user.is_tutor():
        tutor_profile = TutorProfile.query.filter_by(user_id=current_user.id).first()
        if not tutor_profile or booking.tutor_profile_id != tutor_profile.id:
            return jsonify({'error': 'Permission denied'}), 403
    
    # Update booking status
    booking.status = BookingStatus.CANCELLED
    
    # Refund payment if exists
    payment = Payment.query.filter_by(booking_id=booking.id).first()
    if payment and payment.status == PaymentStatus.COMPLETED:
        payment.status = PaymentStatus.REFUNDED
    
    db.session.commit()
    
    return jsonify({'success': True})
