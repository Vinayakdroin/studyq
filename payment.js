document.addEventListener('DOMContentLoaded', function() {
    const paymentForm = document.getElementById('payment-form');
    if (!paymentForm) return; // Not on the payment page
    
    const cardNumberInput = document.getElementById('card_number');
    const cardExpiryInput = document.getElementById('card_expiry');
    const cardCvcInput = document.getElementById('card_cvc');
    const submitButton = document.querySelector('#payment-form button[type="submit"]');
    
    // Format card number input (add spaces)
    if (cardNumberInput) {
        cardNumberInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            // Add space after every 4 digits
            if (value.length > 0) {
                value = value.match(/.{1,4}/g).join(' ');
            }
            
            // Max length: 16 digits + 3 spaces = 19
            if (value.length > 19) {
                value = value.substr(0, 19);
            }
            
            e.target.value = value;
        });
    }
    
    // Format expiry date (MM/YY)
    if (cardExpiryInput) {
        cardExpiryInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            if (value.length > 0) {
                if (value.length > 2) {
                    value = value.substring(0, 2) + '/' + value.substring(2);
                }
                
                // Max length: 4 digits + 1 slash = 5
                if (value.length > 5) {
                    value = value.substr(0, 5);
                }
            }
            
            e.target.value = value;
        });
    }
    
    // Validate card CVC (3 digits)
    if (cardCvcInput) {
        cardCvcInput.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            // Max length: 3 digits
            if (value.length > 3) {
                value = value.substr(0, 3);
            }
            
            e.target.value = value;
        });
    }
    
    // Form validation
    paymentForm.addEventListener('submit', function(e) {
        let valid = true;
        let errorMessage = '';
        
        // Reset validation state
        document.querySelectorAll('.is-invalid').forEach(el => {
            el.classList.remove('is-invalid');
        });
        
        // Validate card number
        const cardNumber = cardNumberInput.value.replace(/\s/g, '');
        if (cardNumber.length !== 16 || !/^\d+$/.test(cardNumber)) {
            cardNumberInput.classList.add('is-invalid');
            errorMessage = 'Please enter a valid 16-digit card number';
            valid = false;
        }
        
        // Validate expiry date
        const expiry = cardExpiryInput.value;
        if (!/^\d{2}\/\d{2}$/.test(expiry)) {
            cardExpiryInput.classList.add('is-invalid');
            errorMessage = errorMessage || 'Please enter a valid expiry date (MM/YY)';
            valid = false;
        } else {
            const [month, year] = expiry.split('/').map(Number);
            const currentDate = new Date();
            const currentYear = currentDate.getFullYear() % 100;
            const currentMonth = currentDate.getMonth() + 1;
            
            if (month < 1 || month > 12 || 
                year < currentYear || 
                (year === currentYear && month < currentMonth)) {
                cardExpiryInput.classList.add('is-invalid');
                errorMessage = errorMessage || 'Card has expired';
                valid = false;
            }
        }
        
        // Validate CVC
        if (!/^\d{3}$/.test(cardCvcInput.value)) {
            cardCvcInput.classList.add('is-invalid');
            errorMessage = errorMessage || 'Please enter a valid 3-digit CVC code';
            valid = false;
        }
        
        // Display error and prevent form submission if invalid
        if (!valid) {
            e.preventDefault();
            
            const errorAlert = document.getElementById('payment-error');
            if (errorAlert) {
                errorAlert.textContent = errorMessage;
                errorAlert.classList.remove('d-none');
            } else {
                alert(errorMessage);
            }
        } else {
            // Show loading state if valid
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Processing...';
        }
    });
});
