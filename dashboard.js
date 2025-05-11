document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts for earnings dashboard
    initializeEarningsChart();
    
    // Handle star rating selection on review form
    initializeStarRating();
    
    // Toggle mobile dashboard menu
    const dashboardToggle = document.getElementById('dashboard-menu-toggle');
    if (dashboardToggle) {
        dashboardToggle.addEventListener('click', function() {
            const dashboardSidebar = document.getElementById('dashboard-sidebar');
            dashboardSidebar.classList.toggle('show');
        });
    }
});

function initializeEarningsChart() {
    const earningsChart = document.getElementById('earnings-chart');
    if (!earningsChart) return;
    
    // Get chart data from element attributes
    const labels = JSON.parse(earningsChart.dataset.labels || '[]');
    const data = JSON.parse(earningsChart.dataset.values || '[]');
    
    // Create earnings chart
    new Chart(earningsChart, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Earnings (€)',
                data: data,
                backgroundColor: 'rgba(75, 192, 192, 0.5)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return '€' + value;
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return '€' + context.raw;
                        }
                    }
                }
            }
        }
    });
}

function initializeStarRating() {
    const ratingContainer = document.querySelector('.rating-selector');
    if (!ratingContainer) return;
    
    const stars = ratingContainer.querySelectorAll('.star-rating');
    const ratingInput = document.getElementById('rating');
    
    // Set initial rating display
    if (ratingInput && ratingInput.value) {
        updateStars(parseInt(ratingInput.value));
    }
    
    // Add click event to stars
    stars.forEach(function(star) {
        star.addEventListener('click', function() {
            const rating = parseInt(this.dataset.rating);
            ratingInput.value = rating;
            updateStars(rating);
        });
        
        // Add hover effect
        star.addEventListener('mouseenter', function() {
            const rating = parseInt(this.dataset.rating);
            
            stars.forEach(function(s) {
                const starRating = parseInt(s.dataset.rating);
                if (starRating <= rating) {
                    s.classList.add('hover');
                } else {
                    s.classList.remove('hover');
                }
            });
        });
    });
    
    // Remove hover effect when mouse leaves container
    ratingContainer.addEventListener('mouseleave', function() {
        stars.forEach(function(s) {
            s.classList.remove('hover');
        });
        
        // Restore selected rating
        if (ratingInput && ratingInput.value) {
            updateStars(parseInt(ratingInput.value));
        }
    });
    
    // Update stars display based on selected rating
    function updateStars(rating) {
        stars.forEach(function(star) {
            const starRating = parseInt(star.dataset.rating);
            if (starRating <= rating) {
                star.classList.add('selected');
                star.querySelector('i').className = 'fas fa-star';
            } else {
                star.classList.remove('selected');
                star.querySelector('i').className = 'far fa-star';
            }
        });
    }
}
