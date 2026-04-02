var API_BASE_URL = 'http://127.0.0.1:8000';

function onLoaderFunc()
{
  var savedUsername = localStorage.getItem('username');
  if (savedUsername) {
    $('#Username').val(savedUsername);
  }

  $(".seatStructure *").prop("disabled", true);
  $(".displayerBoxes *").prop("disabled", true);
}

function takeData()
{
  var showtimeId = parseInt($("#ShowtimeId").val(), 10);
  if (( $("#Username").val().length == 0 ) || ( $("#Numseats").val().length == 0 ) || !Number.isInteger(showtimeId) || showtimeId <= 0)
  {
    alert("Please enter a valid name, showtime ID and number of seats");
  }
  else
  {
    $(".inputForm *").prop("disabled", true);
    $(".seatStructure *").prop("disabled", false);
    document.getElementById("notification").innerHTML = "Please Select your Seats NOW!";
    loadReservedSeats();
  }
}

async function loadReservedSeats() {
  var showtimeId = $('#ShowtimeId').val();

  try {
    var response = await fetch(API_BASE_URL + '/showtimes/' + showtimeId + '/seats');
    var data = await response.json();

    if (!response.ok) {
      alert(data.detail || 'Could not load seat map for this showtime');
      return;
    }

    $('.seats').prop('disabled', false);
    $('.seats').prop('checked', false);
    $('.seats').data('reserved', false);

    data.booked_seats.forEach(function(seatLabel) {
      $(".seats[value='" + seatLabel + "']").prop('disabled', true).data('reserved', true);
    });
  } catch (error) {
    alert('Cannot connect to API. Make sure FastAPI server is running.');
  }
}

async function updateTextArea() {

  if ($("input:checked").length == (($("#Numseats").val())))
    {
      $(".seatStructure *").prop("disabled", true);

     var allNameVals = [];
     var allNumberVals = [];
     var allSeatsVals = [];

     allNameVals.push($("#Username").val());
     allNumberVals.push($("#Numseats").val());
     $('#seatsBlock :checked').each(function() {
       allSeatsVals.push($(this).val());
     });

     $('#nameDisplay').val(allNameVals);
     $('#NumberDisplay').val(allNumberVals);
     $('#seatsDisplay').val(allSeatsVals);

     await submitBooking(allSeatsVals);
    }
  else
    {
      alert("Please select " + (($("#Numseats").val())) + " seats")
    }
  }

async function submitBooking(selectedSeats) {
  var token = localStorage.getItem('access_token');
  if (!token) {
    alert('Please login first.');
    window.location.href = 'login.html';
    return;
  }

  var showtimeId = parseInt($('#ShowtimeId').val(), 10);
  if (!Number.isInteger(showtimeId) || showtimeId <= 0) {
    alert('Please enter a valid showtime ID.');
    return;
  }

  try {
    var response = await fetch(API_BASE_URL + '/bookings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
      },
      body: JSON.stringify({
        showtime_id: showtimeId,
        seat_labels: selectedSeats
      })
    });

    var data = await response.json();
    if (!response.ok) {
      alert(data.detail || 'Booking failed');
      return;
    }

    alert('Booking confirmed. Code: ' + data.booking_code);
  } catch (error) {
    alert('Cannot connect to API. Make sure FastAPI server is running.');
  }
}


$(':checkbox').click(function() {
  if ($("input:checked").length == (($("#Numseats").val()))) {
    $('.seats:not(:checked)').prop('disabled', true);
  }
  else
    {
      $('.seats').each(function() {
        if (!$(this).data('reserved')) {
          $(this).prop('disabled', false);
        }
      });
    }
});