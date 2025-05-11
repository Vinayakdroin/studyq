import datetime
from models import Availability, Booking, BookingStatus


def calculate_session_price(hourly_rate, start_time, end_time):
    """Calculate the price of a session based on duration and hourly rate"""
    if isinstance(start_time, str):
        start_time = datetime.datetime.strptime(start_time, '%H:%M').time()
    if isinstance(end_time, str):
        end_time = datetime.datetime.strptime(end_time, '%H:%M').time()
    
    # Calculate duration in hours
    start_dt = datetime.datetime.combine(datetime.date.today(), start_time)
    end_dt = datetime.datetime.combine(datetime.date.today(), end_time)
    duration_hours = (end_dt - start_dt).total_seconds() / 3600
    
    # Calculate price
    price = round(hourly_rate * duration_hours, 2)
    return price


def get_available_slots(tutor_profile_id, date):
    """Get available time slots for a specific tutor on a specific date"""
    if isinstance(date, str):
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    
    day_of_week = date.weekday()  # 0 = Monday, 6 = Sunday
    
    # Get availability for this day of week
    availabilities = Availability.query.filter_by(
        tutor_profile_id=tutor_profile_id,
        day_of_week=day_of_week,
        is_available=True
    ).all()
    
    # Get existing bookings
    bookings = Booking.query.filter_by(
        tutor_profile_id=tutor_profile_id,
        booking_date=date,
        status=BookingStatus.CONFIRMED
    ).all()
    
    booked_slots = [(b.start_time, b.end_time) for b in bookings]
    
    # Filter out booked slots
    available_slots = []
    for slot in availabilities:
        # Check if slot overlaps with any booking
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
    
    return available_slots


def format_datetime(date, time):
    """Format date and time objects for display"""
    if isinstance(date, str):
        date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
    if isinstance(time, str):
        time = datetime.datetime.strptime(time, '%H:%M').time()
    
    dt = datetime.datetime.combine(date, time)
    return dt.strftime('%I:%M %p')  # 12-hour format with AM/PM
