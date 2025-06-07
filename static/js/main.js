// Custom JavaScript for Airport Management System

$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);

    // Seat selection functionality
    $('.seat.available').click(function() {
        $('.seat').removeClass('selected');
        $(this).addClass('selected');
        var seatNumber = $(this).data('seat');
        $('#id_seat_number').val(seatNumber);
        updateBookingTotal();
    });

    // Flight search functionality
    $('#flight-search-form').submit(function(e) {
        showLoadingSpinner();
    });

    // Real-time flight status updates
    if (window.location.pathname.includes('flight-status')) {
        setInterval(updateFlightStatus, 30000); // Update every 30 seconds
    }

    // Form validation
    $('form').on('submit', function(e) {
        var isValid = true;
        
        // Check required fields
        $(this).find('input[required], select[required]').each(function() {
            if (!$(this).val()) {
                $(this).addClass('is-invalid');
                isValid = false;
            } else {
                $(this).removeClass('is-invalid');
            }
        });

        // Email validation
        $('input[type="email"]').each(function() {
            var email = $(this).val();
            var emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (email && !emailRegex.test(email)) {
                $(this).addClass('is-invalid');
                isValid = false;
            }
        });

        // Phone validation
        $('input[type="tel"]').each(function() {
            var phone = $(this).val();
            var phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
            if (phone && !phoneRegex.test(phone)) {
                $(this).addClass('is-invalid');
                isValid = false;
            }
        });

        if (!isValid) {
            e.preventDefault();
            showAlert('Please fill in all required fields correctly.', 'danger');
        }
    });

    // Booking confirmation
    $('#confirm-booking').click(function() {
        var bookingDetails = collectBookingDetails();
        showBookingConfirmation(bookingDetails);
    });

    // Check-in functionality
    $('.check-in-btn').click(function() {
        var bookingId = $(this).data('booking-id');
        initiateCheckIn(bookingId);
    });

    // Notification marking as read
    $('.notification-item').click(function() {
        var notificationId = $(this).data('notification-id');
        markNotificationAsRead(notificationId);
    });

    // Search functionality
    $('#search-input').on('keyup', function() {
        var searchTerm = $(this).val().toLowerCase();
        filterSearchResults(searchTerm);
    });

    // Date picker initialization
    $('input[type="date"], input[type="datetime-local"]').each(function() {
        // Set minimum date to today
        var today = new Date().toISOString().split('T')[0];
        $(this).attr('min', today);
    });

    // Animation on scroll
    $(window).scroll(function() {
        $('.fade-in').each(function() {
            var elementTop = $(this).offset().top;
            var elementBottom = elementTop + $(this).outerHeight();
            var viewportTop = $(window).scrollTop();
            var viewportBottom = viewportTop + $(window).height();

            if (elementBottom > viewportTop && elementTop < viewportBottom) {
                $(this).addClass('animated');
            }
        });
    });
});

// Utility Functions

function showLoadingSpinner() {
    $('body').append('<div class="spinner-overlay"><div class="spinner-border text-primary" role="status"></div></div>');
}

function hideLoadingSpinner() {
    $('.spinner-overlay').remove();
}

function showAlert(message, type = 'info') {
    var alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    $('.container').first().prepend(alertHtml);
}

function updateBookingTotal() {
    var seatPrice = parseFloat($('.seat.selected').data('price') || 0);
    var basePrice = parseFloat($('#base-price').val() || 0);
    var total = basePrice + seatPrice;
    $('#total-amount').text('$' + total.toFixed(2));
    $('#id_total_amount').val(total.toFixed(2));
}

function updateFlightStatus() {
    $.ajax({
        url: '/api/flight-status/',
        method: 'GET',
        success: function(data) {
            data.flights.forEach(function(flight) {
                var statusElement = $(`#flight-${flight.id} .flight-status`);
                if (statusElement.length) {
                    statusElement.removeClass().addClass(`flight-status status-${flight.status.toLowerCase()}`);
                    statusElement.text(flight.status);
                }
            });
        },
        error: function() {
            console.log('Failed to update flight status');
        }
    });
}

function collectBookingDetails() {
    return {
        flight: $('#selected-flight').text(),
        passenger: $('#id_passenger_name').val(),
        seat: $('#id_seat_number').val(),
        class: $('#id_seat_class').val(),
        total: $('#id_total_amount').val()
    };
}

function showBookingConfirmation(details) {
    var confirmationHtml = `
        <div class="modal fade" id="bookingConfirmationModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">Confirm Booking</h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <h6>Flight: ${details.flight}</h6>
                        <p><strong>Passenger:</strong> ${details.passenger}</p>
                        <p><strong>Seat:</strong> ${details.seat} (${details.class})</p>
                        <p><strong>Total:</strong> $${details.total}</p>
                        <p class="text-muted">Please review your booking details before confirming.</p>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" id="final-confirm">Confirm Booking</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    $('body').append(confirmationHtml);
    $('#bookingConfirmationModal').modal('show');
    
    $('#final-confirm').click(function() {
        $('#booking-form').submit();
    });
}

function initiateCheckIn(bookingId) {
    $.ajax({
        url: `/bookings/check-in/${bookingId}/`,
        method: 'POST',
        headers: {
            'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (response.success) {
                showAlert('Check-in successful! Your boarding pass is ready.', 'success');
                setTimeout(function() {
                    window.location.href = response.boarding_pass_url;
                }, 2000);
            } else {
                showAlert(response.message, 'danger');
            }
        },
        error: function() {
            showAlert('Check-in failed. Please try again.', 'danger');
        }
    });
}

function markNotificationAsRead(notificationId) {
    $.ajax({
        url: `/notifications/mark-read/${notificationId}/`,
        method: 'POST',
        headers: {
            'X-CSRFToken': $('[name=csrfmiddlewaretoken]').val()
        },
        success: function() {
            $(`#notification-${notificationId}`).removeClass('unread');
            updateNotificationCount();
        }
    });
}

function updateNotificationCount() {
    var unreadCount = $('.notification-item.unread').length;
    var badge = $('.navbar .badge');
    if (unreadCount > 0) {
        badge.text(unreadCount).show();
    } else {
        badge.hide();
    }
}

function filterSearchResults(searchTerm) {
    $('.searchable').each(function() {
        var text = $(this).text().toLowerCase();
        if (text.includes(searchTerm)) {
            $(this).show();
        } else {
            $(this).hide();
        }
    });
}

// Flight booking seat map generation
function generateSeatMap(aircraftType, bookedSeats = []) {
    var seatMap = $('#seat-map');
    seatMap.empty();
    
    var rows = aircraftType === 'A380' ? 60 : aircraftType === 'B777' ? 42 : 30;
    var seatsPerRow = 6;
    
    for (var row = 1; row <= rows; row++) {
        for (var col = 0; col < seatsPerRow; col++) {
            var seatLetter = String.fromCharCode(65 + col); // A, B, C, D, E, F
            var seatNumber = row + seatLetter;
            var isBooked = bookedSeats.includes(seatNumber);
            var seatClass = row <= 5 ? 'first' : row <= 15 ? 'business' : 'economy';
            
            var seatElement = $(`
                <div class="seat ${isBooked ? 'occupied' : 'available'}" 
                     data-seat="${seatNumber}" 
                     data-class="${seatClass}"
                     data-price="${getSeatPrice(seatClass)}">
                    ${seatNumber}
                </div>
            `);
            
            seatMap.append(seatElement);
        }
    }
}

function getSeatPrice(seatClass) {
    switch (seatClass) {
        case 'first': return 500;
        case 'business': return 200;
        case 'economy': return 0;
        default: return 0;
    }
}

// Print boarding pass
function printBoardingPass() {
    window.print();
}

// Download boarding pass as PDF
function downloadBoardingPass() {
    // This would require a PDF generation library
    showAlert('PDF download feature coming soon!', 'info');
}

// Refresh page data
function refreshData() {
    location.reload();
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Format date and time
function formatDateTime(dateString) {
    return new Date(dateString).toLocaleString();
}

// Validate form fields
function validateField(field, value) {
    switch (field) {
        case 'email':
            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
        case 'phone':
            return /^[\+]?[1-9][\d]{0,15}$/.test(value);
        case 'passport':
            return /^[A-Z0-9]{6,9}$/.test(value);
        default:
            return value.length > 0;
    }
}
