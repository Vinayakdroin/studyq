document.addEventListener('DOMContentLoaded', function() {
    // Enable tooltips everywhere
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Enable popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Add scroll animation to smooth-scroll links
    document.querySelectorAll('a.smooth-scroll').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 100,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Handle mobile menu toggle
    const menuToggle = document.getElementById('navbarToggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            const navbarMenu = document.getElementById('navbarNav');
            if (navbarMenu.classList.contains('show')) {
                navbarMenu.classList.remove('show');
            } else {
                navbarMenu.classList.add('show');
            }
        });
    }

    // Flash message auto-dismissal
    setTimeout(function() {
        const flashMessages = document.querySelectorAll('.alert-dismissible');
        flashMessages.forEach(function(message) {
            const bsAlert = new bootstrap.Alert(message);
            bsAlert.close();
        });
    }, 5000);  // Auto-dismiss after 5 seconds

    // Star rating display
    document.querySelectorAll('.rating-display').forEach(function(container) {
        const rating = parseFloat(container.dataset.rating || 0);
        const stars = container.querySelectorAll('.star');
        
        stars.forEach(function(star, index) {
            if (index < Math.floor(rating)) {
                star.classList.add('fas', 'fa-star');
            } else if (index < rating) {
                star.classList.add('fas', 'fa-star-half-alt');
            } else {
                star.classList.add('far', 'fa-star');
            }
        });
    });

    // Handle booking and session actions
    setupSessionActions();
});

function setupSessionActions() {
    // Complete session buttons
    document.querySelectorAll('.btn-complete-session').forEach(button => {
        button.addEventListener('click', function() {
            const bookingId = this.dataset.bookingId;
            if (confirm('Mark this session as completed?')) {
                fetch(`/api/complete_booking/${bookingId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred. Please try again.');
                });
            }
        });
    });

    // Cancel session buttons
    document.querySelectorAll('.btn-cancel-session').forEach(button => {
        button.addEventListener('click', function() {
            const bookingId = this.dataset.bookingId;
            if (confirm('Are you sure you want to cancel this session? This action cannot be undone.')) {
                fetch(`/api/cancel_booking/${bookingId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Error: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred. Please try again.');
                });
            }
        });
    });
}
