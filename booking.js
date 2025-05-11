document.addEventListener('DOMContentLoaded', function() {
    const bookingDateSelect = document.getElementById('booking_date');
    const startTimeSelect = document.getElementById('start_time');
    const endTimeSelect = document.getElementById('end_time');
    const tutorIdInput = document.getElementById('tutor_id');
    const priceDisplay = document.getElementById('session_price');
    
    if (!bookingDateSelect || !startTimeSelect || !endTimeSelect) {
        return; // Not on the booking page
    }

    const tutorId = tutorIdInput ? tutorIdInput.value : document.querySelector('meta[name="tutor-id"]').content;
    const hourlyRate = parseFloat(document.querySelector('meta[name="hourly-rate"]').content || 0);
    
    // Load available times when date changes
    bookingDateSelect.addEventListener('change', function() {
        const selectedDate = this.value;
        if (!selectedDate) return;
        
        // Clear time dropdowns
        startTimeSelect.innerHTML = '<option value="">Select start time</option>';
        endTimeSelect.innerHTML = '<option value="">Select end time</option>';
        
        // Fetch available times for selected date
        fetch('/student/get_available_times', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                tutor_id: tutorId,
                date: selectedDate
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.available_times && data.available_times.length > 0) {
                data.available_times.forEach(timeSlot => {
                    // Add start time options
                    const startOption = document.createElement('option');
                    startOption.value = timeSlot.start;
                    startOption.textContent = formatTime(timeSlot.start);
                    startTimeSelect.appendChild(startOption);
                    
                    // Add end time options with the same value (will be filtered based on start time selection)
                    const endOption = document.createElement('option');
                    endOption.value = timeSlot.end;
                    endOption.textContent = formatTime(timeSlot.end);
                    endOption.dataset.start = timeSlot.start;
                    endTimeSelect.appendChild(endOption);
                });
            } else {
                // No available times
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No available times for this date';
                startTimeSelect.appendChild(option);
            }
        })
        .catch(error => {
            console.error('Error fetching available times:', error);
        });
    });
    
    // Filter end time options based on selected start time
    startTimeSelect.addEventListener('change', function() {
        const selectedStart = this.value;
        if (!selectedStart) {
            endTimeSelect.innerHTML = '<option value="">Select end time</option>';
            updatePrice();
            return;
        }
        
        // Clear and repopulate end time options
        endTimeSelect.innerHTML = '<option value="">Select end time</option>';
        
        // Get all possible end times
        const endOptions = Array.from(document.querySelectorAll('#end_time option[data-start]'));
        
        // Filter to only show end times after the selected start time
        endOptions.forEach(option => {
            if (option.dataset.start <= selectedStart && option.value > selectedStart) {
                const endOption = document.createElement('option');
                endOption.value = option.value;
                endOption.textContent = formatTime(option.value);
                endTimeSelect.appendChild(endOption);
            }
        });
        
        updatePrice();
    });
    
    // Update price when end time changes
    endTimeSelect.addEventListener('change', function() {
        updatePrice();
    });
    
    // Calculate and update session price
    function updatePrice() {
        const startTime = startTimeSelect.value;
        const endTime = endTimeSelect.value;
        
        if (startTime && endTime) {
            // Calculate duration in hours
            const startMinutes = timeToMinutes(startTime);
            const endMinutes = timeToMinutes(endTime);
            const durationHours = (endMinutes - startMinutes) / 60;
            
            // Calculate price
            const price = (hourlyRate * durationHours).toFixed(2);
            priceDisplay.textContent = `€${price}`;
        } else {
            priceDisplay.textContent = '€0.00';
        }
    }
    
    // Helper function to convert time to minutes
    function timeToMinutes(timeStr) {
        const [hours, minutes] = timeStr.split(':').map(Number);
        return hours * 60 + minutes;
    }
    
    // Helper function to format time (24h to 12h)
    function formatTime(timeStr) {
        const [hours, minutes] = timeStr.split(':');
        const hour = parseInt(hours, 10);
        const suffix = hour >= 12 ? 'PM' : 'AM';
        const displayHour = hour % 12 || 12;
        return `${displayHour}:${minutes} ${suffix}`;
    }
});
