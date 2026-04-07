var API_BASE_URL = window.APP_CONFIG
  ? window.APP_CONFIG.apiBaseUrl
  : (window.location.protocol + '//' + (window.location.hostname || 'localhost') + ':8000');

var PAYMENT_ENDPOINTS = {
  initiate: '/payments/initiate',
  confirm: '/payments/confirm',
  fail: '/payments/fail'
};

var TEST_CARD_PROFILES = {
  visa_success: {
    label: 'Visa success',
    brand: 'Visa',
    outcome: 'success',
    number: '4242 4242 4242 4242',
    expiry: '12/34',
    cvc: '123',
    name: 'Test Visa Success'
  },
  visa_failure: {
    label: 'Visa failure',
    brand: 'Visa',
    outcome: 'failure',
    number: '4000 0000 0000 0002',
    expiry: '01/34',
    cvc: '123',
    name: 'Test Visa Failure'
  },
  mastercard_success: {
    label: 'MasterCard success',
    brand: 'MasterCard',
    outcome: 'success',
    number: '5555 5555 5555 4444',
    expiry: '11/34',
    cvc: '321',
    name: 'Test MasterCard Success'
  },
  mastercard_failure: {
    label: 'MasterCard failure',
    brand: 'MasterCard',
    outcome: 'failure',
    number: '5105 1051 0510 5100',
    expiry: '02/34',
    cvc: '321',
    name: 'Test MasterCard Failure'
  }
};

var checkoutState = {
  reservation: null,
  activeProfile: null,
  paymentBusy: false,
  testMode: 'success',
  selectedBrand: 'visa',
  posterLocked: false
};
var seatPageEventsBound = false;
var seatPageInitialized = false;

function setBookingBackdropImage(posterUrl) {
  var fallbackPoster = "url('img/seatsback.png')";
  var resolvedPoster = (posterUrl || '').trim();

  if (!resolvedPoster) {
    document.body.style.setProperty('--booking-poster', fallbackPoster);
    return;
  }

  document.body.style.setProperty(
    '--booking-poster',
    'url("' + resolvedPoster.replace(/"/g, '\\"') + '")'
  );
}

function initializeSeatPage() {
  if (seatPageInitialized) {
    return;
  }
  seatPageInitialized = true;
  onLoaderFunc();
}

function onLoaderFunc() {
  var savedUsername = localStorage.getItem('username');
  var showtimeFromQuery = new URLSearchParams(window.location.search).get('showtime');
  if (savedUsername) {
    $('#Username').val(savedUsername);
  }
  if (showtimeFromQuery) {
    $('#ShowtimeId').val(showtimeFromQuery);
  }
  var posterFromQuery = new URLSearchParams(window.location.search).get('poster');
  checkoutState.posterLocked = Boolean(posterFromQuery);
  setBookingBackdropImage(posterFromQuery);

  // Initialize test mode and brand
  checkoutState.testMode = 'success';
  checkoutState.selectedBrand = 'visa';
  $('.modeButton[data-mode="success"]').addClass('is-success');
  $('.brandCard[data-brand="visa"]').addClass('is-selected');

  hideCheckoutPanel();
  $('#sandboxBadge').addClass('is-hidden');
  setCheckoutStatus('idle', 'Waiting for checkout', 'Select seats to reveal the sandbox payment form.');
  setCheckoutResult('Select a test card to autofill the sandbox form.', 'idle');
  syncReservationSummary(null);
  bindSeatPageEvents();
  updateSelectionSummary();
  loadReservedSeats();
}

function takeData() {
  loadReservedSeats();
}

function bindSeatPageEvents() {
  if (seatPageEventsBound) {
    return;
  }

  seatPageEventsBound = true;

  $('#ShowtimeId').on('change', function() {
    loadReservedSeats();
  });

  $('#Username').on('input', function() {
    updateSelectionSummary();
  });

  $('#seatsBlock').on('change', 'input.seats', function() {
    updateSelectionSummary();
  });

  window.addEventListener('pageshow', function(event) {
    if (!event.persisted) {
      return;
    }

    updateSelectionSummary();
    if (!checkoutState.reservation) {
      loadReservedSeats();
    }
  });
}

function clearSeatMap() {
  $('.seats').prop('checked', false).prop('disabled', true).data('reserved', false);
  $('#continueButton').prop('disabled', true);
  updateSelectionSummary();
}

function updateSelectionSummary() {
  var selectedSeats = getSelectedSeats();
  var selectedCount = selectedSeats.length;
  var selectedSeatText = selectedCount ? selectedSeats.join(', ') : 'Choose any available seats from the map.';

  $('#seatSelectionCount').text(selectedCount + (selectedCount === 1 ? ' seat selected' : ' seats selected'));
  $('#seatSelectionList').text(selectedSeatText);
  $('#nameDisplay').val($('#Username').val().trim());
  $('#NumberDisplay').val(selectedCount ? String(selectedCount) : '');
  $('#seatsDisplay').val(selectedCount ? selectedSeats.join(', ') : '');
  $('#continueButton').prop('disabled', selectedCount === 0 || checkoutState.reservation !== null);
}

async function loadReservedSeats() {
  var showtimeId = $('#ShowtimeId').val();

  if (!showtimeId) {
    clearSeatMap();
    document.getElementById("notification").innerHTML = "Enter a showtime ID to load available seats.";
    return;
  }

  document.getElementById("notification").innerHTML = "Loading available seats...";
  clearSeatMap();

  try {
    // Add cache-busting timestamp to prevent browser caching
    var cacheBuster = '?_t=' + Date.now();
    var response = await fetch(API_BASE_URL + '/showtimes/' + showtimeId + '/seats' + cacheBuster);
    var data = await response.json();

    if (!response.ok) {
      document.getElementById("notification").innerHTML = "Could not load seats for this showtime.";
      alert(data.detail || 'Could not load seat map for this showtime');
      return;
    }

    data.booked_seats.forEach(function(seatLabel) {
      $(".seats[value='" + seatLabel + "']").prop('disabled', true).data('reserved', true);
    });

    if (!checkoutState.posterLocked && data.poster_url) {
      setBookingBackdropImage(data.poster_url);
    }

    $('.seats').each(function() {
      if (!$(this).data('reserved')) {
        $(this).prop('disabled', false);
      }
    });

    document.getElementById("notification").innerHTML = "Select one or more seats to continue to payment.";
    syncReservationSummary(null);
    hideCheckoutPanel();
    setCheckoutStatus('idle', 'Waiting for checkout', 'Select seats to reveal the sandbox payment form.');
    setCheckoutResult('Select a test card to autofill the sandbox form.', 'idle');
    updateSelectionSummary();
  } catch (error) {
    document.getElementById("notification").innerHTML = "Cannot connect to API. Make sure the backend is running.";
    alert('Cannot connect to API. Make sure FastAPI server is running.');
  }
}

async function updateTextArea() {
  var selectedSeats = getSelectedSeats();
  if (!selectedSeats.length) {
    alert("Please select at least one seat");
    return;
  }

  $('#nameDisplay').val($("#Username").val());
  $('#NumberDisplay').val(String(selectedSeats.length));
  $('#seatsDisplay').val(selectedSeats.join(', '));

  await createReservation(selectedSeats);
}

function getSelectedSeats() {
  var selectedSeats = [];
  $('#seatsBlock :checked').each(function() {
    selectedSeats.push($(this).val());
  });
  return selectedSeats;
}

function getAuthHeaders() {
  var token = localStorage.getItem('access_token');
  if (!token) {
    return null;
  }

  return {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + token
  };
}

function formatCurrency(amount) {
  var numericAmount = Number(amount || 0);
  return '$' + numericAmount.toFixed(2);
}

function sanitizeCardNumber(value) {
  return (value || '').replace(/[^0-9]/g, '').replace(/(.{4})/g, '$1 ').trim();
}

function getActiveProfile() {
  if (checkoutState.activeProfile) {
    return TEST_CARD_PROFILES[checkoutState.activeProfile];
  }

  return inferProfileFromCard($('#cardNumber').val());
}

function inferProfileFromCard(cardNumber) {
  var normalized = (cardNumber || '').replace(/\s+/g, '');
  if (normalized === '4242424242424242') {
    return TEST_CARD_PROFILES.visa_success;
  }
  if (normalized === '4000000000000002') {
    return TEST_CARD_PROFILES.visa_failure;
  }
  if (normalized === '5555555555554444') {
    return TEST_CARD_PROFILES.mastercard_success;
  }
  if (normalized === '5105105105105100') {
    return TEST_CARD_PROFILES.mastercard_failure;
  }
  return null;
}

function parseExpiry(expiryValue) {
  var parts = (expiryValue || '').split('/');
  if (parts.length !== 2) {
    return null;
  }

  var month = parseInt(parts[0].trim(), 10);
  var year = parseInt(parts[1].trim(), 10);
  if (Number.isNaN(month) || Number.isNaN(year)) {
    return null;
  }

  if (year < 100) {
    year = 2000 + year;
  }

  return {
    month: month,
    year: year
  };
}

function syncReservationSummary(reservation) {
  if (!reservation) {
    $('#reservationCode').text('-');
    $('#reservationSeats').text('-');
    $('#reservationAmount').text('-');
    $('#reservationShowtime').text('-');
    return;
  }

  $('#reservationCode').text(reservation.booking_code || '-');
  $('#reservationSeats').text((reservation.seat_labels || []).join(', ') || '-');
  $('#reservationAmount').text(formatCurrency(reservation.total_amount));
  $('#reservationShowtime').text('Showtime #' + reservation.showtime_id);
}

function setCheckoutStatus(kind, title, detail) {
  var pill = $('#paymentStatusPill');
  pill.removeClass('is-idle is-ready is-processing is-success is-failure');
  pill.addClass('is-' + kind);
  pill.text(title);

  $('#paymentDescription').text(detail);
}

function setCheckoutResult(text, kind) {
  var result = $('#paymentResult');
  result.removeClass('is-idle is-success is-failure');
  result.addClass('is-' + kind);
  result.text(text);
}

function setPaymentBusy(isBusy) {
  checkoutState.paymentBusy = isBusy;
  $('#payButton').prop('disabled', isBusy);
  $('#cardholderName').prop('disabled', isBusy);
  $('#cardNumber').prop('disabled', isBusy);
  $('#cardExpiry').prop('disabled', isBusy);
  $('#cardCvc').prop('disabled', isBusy);
  $('.testCard').prop('disabled', isBusy);
}

function showCheckoutPanel() {
  $('#checkoutPanel').removeClass('is-hidden');
  $('#sandboxBadge').removeClass('is-hidden');
  document.getElementById('checkoutPanel').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function hideCheckoutPanel() {
  $('#checkoutPanel').addClass('is-hidden');
}

function fillTestCard(profileKey) {
  var profile = TEST_CARD_PROFILES[profileKey];
  if (!profile) {
    return;
  }

  checkoutState.activeProfile = profileKey;
  $('#cardholderName').val(profile.name);
  $('#cardNumber').val(profile.number);
  $('#cardExpiry').val(profile.expiry);
  $('#cardCvc').val(profile.cvc);

  $('.testCard').removeClass('is-selected');
  $(".testCard[data-test-card='" + profileKey + "']").addClass('is-selected');

  setCheckoutStatus('ready', 'Test card loaded', profile.label + ' is ready to submit.');
  setCheckoutResult('Autofilled ' + profile.label + '.', 'idle');
}

function setTestMode(mode) {
  checkoutState.testMode = mode;
  $('.modeButton').removeClass('is-success is-failure');
  $('.modeButton[data-mode="' + mode + '"]').addClass(mode === 'success' ? 'is-success' : 'is-failure');

  // Update card selection based on mode
  updateCardSelection();
}

function selectCardBrand(brand) {
  checkoutState.selectedBrand = brand;
  $('.brandCard').removeClass('is-selected');
  $('.brandCard[data-brand="' + brand + '"]').addClass('is-selected');

  // Update card selection based on mode
  updateCardSelection();
}

function updateCardSelection() {
  var profileKey = checkoutState.selectedBrand + '_' + checkoutState.testMode;
  fillTestCard(profileKey);

  // Show/hide floating badge
  if ($('#checkoutPanel').length && !$('#checkoutPanel').hasClass('is-hidden')) {
    $('#sandboxBadge').removeClass('is-hidden');
  } else {
    $('#sandboxBadge').addClass('is-hidden');
  }
}

async function createReservation(selectedSeats) {
  try {
    var result = await requestJson('/bookings', {
      showtime_id: parseInt($('#ShowtimeId').val(), 10),
      seat_labels: selectedSeats
    });

    var data = result.data;

    checkoutState.reservation = data;
    syncReservationSummary(data);
    showCheckoutPanel();
    $('.seats').prop('disabled', true);
    $('#continueButton').prop('disabled', true);
    $('#Username').prop('disabled', true);
    $('#ShowtimeId').prop('disabled', true);
    $('#refreshSeatMapButton').prop('disabled', true);
    setCheckoutStatus('ready', 'Reservation created', 'Choose a sandbox card to complete payment and confirm the booking.');
    setCheckoutResult('Reservation created. Payment is still required.', 'idle');
  } catch (error) {
    if (error.message === 'Please login first.') {
      alert(error.message);
      window.location.href = 'login.html';
      return;
    }

    alert(error.message || 'Cannot connect to API. Make sure FastAPI server is running.');
  }
}

async function requestJson(path, payload, options) {
  var requestOptions = {
    method: 'POST',
    headers: getAuthHeaders(),
    body: JSON.stringify(payload)
  };

  if (!requestOptions.headers) {
    throw new Error('Please login first.');
  }

  var response = await fetch(API_BASE_URL + path, requestOptions);
  var rawText = await response.text();
  var data = {};

  if (rawText) {
    try {
      data = JSON.parse(rawText);
    } catch (error) {
      data = { raw: rawText };
    }
  }

  if (!response.ok) {
    if (options && options.allow404 && response.status === 404) {
      return {
        response: response,
        data: data,
        missing: true
      };
    }

    throw new Error(data.detail || data.message || 'Request failed');
  }

  return {
    response: response,
    data: data,
    missing: false
  };
}

async function submitPayment() {
  if (!checkoutState.reservation) {
    setCheckoutResult('Create a reservation before paying.', 'failure');
    setCheckoutStatus('failure', 'Reservation missing', 'Select seats first, then open checkout.');
    return;
  }

  var cardholderName = $('#cardholderName').val().trim();
  var cardNumber = sanitizeCardNumber($('#cardNumber').val());
  var cardExpiry = $('#cardExpiry').val().trim();
  var cardCvc = $('#cardCvc').val().trim();
  var activeProfile = getActiveProfile();

  if (!cardholderName || !cardNumber || !cardExpiry || !cardCvc) {
    setCheckoutResult('Complete the card fields before paying.', 'failure');
    return;
  }

  var parsedExpiry = parseExpiry(cardExpiry);
  if (!parsedExpiry) {
    setCheckoutResult('Enter expiry as MM/YY or MM/YYYY.', 'failure');
    return;
  }

  if (!activeProfile) {
    activeProfile = { label: 'Selected card' };
  }

  setPaymentBusy(true);
  setCheckoutStatus('processing', 'Processing payment', 'Submitting the sandbox card to the gateway.');
  setCheckoutResult('Transaction is being processed.', 'idle');

  try {
    var initiatePayload = {
      booking_id: checkoutState.reservation.booking_id,
      provider: 'stripe_sandbox'
    };

    var initiate = await requestJson(PAYMENT_ENDPOINTS.initiate, initiatePayload);
    var confirm = await requestJson(PAYMENT_ENDPOINTS.confirm, {
      payment_id: initiate.data.payment_id,
      cardholder_name: cardholderName,
      card_number: cardNumber,
      expiry_month: parsedExpiry.month,
      expiry_year: parsedExpiry.year,
      cvc: cardCvc
    });

    if (confirm.data.status === 'paid') {
      setCheckoutStatus('success', 'Payment approved', 'Reservation confirmed for the client.');
      var successMessage = 'Success! Reservation ' + checkoutState.reservation.booking_code + ' is confirmed.';
      setCheckoutResult(
        successMessage + ' Reference: ' + confirm.data.provider_ref + '.',
        'success'
      );
      $('#paymentDescription').text('All set. The reservation is complete.');
      $('#payButton').prop('disabled', true);
      $('.testCard').prop('disabled', true);

      // Generate and download booking confirmation PDF
      generateBookingPDF(confirm.data, checkoutState.reservation);
    } else {
      checkoutState.reservation = null;
      setCheckoutStatus('failure', 'Payment declined', 'Sandbox gateway rejected the card and released the reservation.');
      setCheckoutResult(
        'Failure. ' + activeProfile.label + ' was declined. The seats were released for another attempt.',
        'failure'
      );
    }
  } catch (error) {
    setCheckoutStatus('failure', 'Payment error', error.message || 'The gateway request failed.');
    setCheckoutResult(error.message || 'Unable to process payment.', 'failure');
  } finally {
    setPaymentBusy(false);
  }
}

// Generate Booking Confirmation PDF
function generateBookingPDF(paymentData, reservation) {
  var username = localStorage.getItem('username') || 'Guest';
  var timestamp = new Date().toLocaleString();
  var seats = reservation.seat_labels ? reservation.seat_labels.join(', ') : '-';
  var amount = formatCurrency(reservation.total_amount);

  var pdfContent = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Booking Confirmation - ${reservation.booking_code}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .header { background: linear-gradient(135deg, #ff2c1f, #c41f1a); color: white; padding: 30px; text-align: center; }
        .header h1 { font-size: 28px; margin-bottom: 5px; }
        .header p { opacity: 0.9; font-size: 14px; }
        .content { padding: 40px; }
        .success-icon { width: 80px; height: 80px; background: #22c55e; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 30px; }
        .success-icon svg { width: 40px; height: 40px; fill: white; }
        .booking-code { font-size: 32px; font-weight: bold; color: #ff2c1f; text-align: center; margin-bottom: 30px; letter-spacing: 2px; }
        .section { margin-bottom: 30px; }
        .section-title { font-size: 14px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 15px; border-bottom: 2px solid #ff2c1f; padding-bottom: 10px; display: inline-block; }
        .info-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }
        .info-item { padding: 15px; background: #f9f9f9; border-radius: 8px; }
        .info-label { font-size: 12px; color: #888; margin-bottom: 5px; }
        .info-value { font-size: 16px; font-weight: 600; color: #333; }
        .seats-display { background: #fff3cd; border: 2px dashed #ffc107; padding: 20px; border-radius: 8px; text-align: center; margin-top: 20px; }
        .seats-display p { font-size: 18px; color: #856404; font-weight: 600; }
        .footer { background: #333; color: white; padding: 30px; text-align: center; }
        .footer p { font-size: 12px; opacity: 0.7; }
        .total-amount { font-size: 36px; font-weight: bold; color: #22c55e; text-align: center; margin: 30px 0; }
        @media print { body { background: white; } .container { box-shadow: none; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>CINEMA HOME</h1>
            <p>Booking Confirmation</p>
        </div>
        <div class="content">
            <div class="success-icon">
                <svg viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/></svg>
            </div>
            <div class="booking-code">${reservation.booking_code}</div>
            <p style="text-align: center; color: #22c55e; font-size: 16px; margin-bottom: 30px;">
                ✓ Your reservation has been confirmed
            </p>

            <div class="total-amount">${amount}</div>

            <div class="section">
                <div class="section-title">Booking Details</div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Booking Code</div>
                        <div class="info-value">${reservation.booking_code}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Transaction ID</div>
                        <div class="info-value">${paymentData.provider_ref}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Showtime ID</div>
                        <div class="info-value">#${reservation.showtime_id}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Payment Method</div>
                        <div class="info-value">${paymentData.card_brand} •••• ${paymentData.card_last4}</div>
                    </div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Reserved Seats</div>
                <div class="seats-display">
                    <p>${seats}</p>
                    <small style="color: #856404; font-weight: normal;">${reservation.seats_count || reservation.seat_labels?.length || 0} seat(s) reserved</small>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Customer Information</div>
                <div class="info-grid">
                    <div class="info-item">
                        <div class="info-label">Name</div>
                        <div class="info-value">${username}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label">Booking Date</div>
                        <div class="info-value">${timestamp}</div>
                    </div>
                </div>
            </div>
        </div>
        <div class="footer">
            <p>Thank you for choosing Cinema Home!</p>
            <p>Please show this confirmation at the theater</p>
            <p style="margin-top: 10px;">Generated on ${timestamp}</p>
        </div>
    </div>
    <script>
        setTimeout(function() { window.print(); }, 500);
    </script>
</body>
</html>
  `;

  // Create a temporary window and load the content
  var printWindow = window.open('', '_blank');
  if (printWindow) {
    printWindow.document.write(pdfContent);
    printWindow.document.close();
  } else {
    // Fallback: Create download link
    var blob = new Blob([pdfContent], { type: 'text/html' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = 'Booking_Confirmation_' + reservation.booking_code + '.html';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }
}

async function resetCheckout() {
  if (checkoutState.reservation && checkoutState.reservation.status !== 'confirmed') {
    try {
      await requestJson('/bookings/' + checkoutState.reservation.booking_id + '/cancel', {});
    } catch (error) {
      if (error.message !== 'Booking not found' && error.message !== 'Reservation already released') {
        console.warn(error.message);
      }
    }
  }

  checkoutState.reservation = null;
  checkoutState.activeProfile = null;
  checkoutState.paymentBusy = false;

  $('.testCard').removeClass('is-selected');
  $('.brandCard').removeClass('is-selected');
  $('#cardholderName').val('');
  $('#cardNumber').val('');
  $('#cardExpiry').val('');
  $('#cardCvc').val('');
  $('#paymentResult').text('Select a test card to autofill the sandbox form.');
  $('#payButton').prop('disabled', false);
  $('#cardholderName').prop('disabled', false);
  $('#cardNumber').prop('disabled', false);
  $('#cardExpiry').prop('disabled', false);
  $('#cardCvc').prop('disabled', false);

  hideCheckoutPanel();
  $('#sandboxBadge').addClass('is-hidden');
  setCheckoutStatus('idle', 'Waiting for checkout', 'Select seats to reveal the sandbox payment form.');
  setCheckoutResult('Select a test card to autofill the sandbox form.', 'idle');

  // Reset test mode and brand
  checkoutState.testMode = 'success';
  checkoutState.selectedBrand = 'visa';
  $('.modeButton').removeClass('is-success is-failure');
  $('.modeButton[data-mode="success"]').addClass('is-success');
  $('.brandCard[data-brand="visa"]').addClass('is-selected');

  $('#Username').prop('disabled', false);
  $('#ShowtimeId').prop('disabled', false);
  $('#refreshSeatMapButton').prop('disabled', false);
  loadReservedSeats();
}

// Initialize seat page when DOM is ready (for reliable navigation from main.html)
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeSeatPage);
} else {
  initializeSeatPage();
}
