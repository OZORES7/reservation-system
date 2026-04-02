# Cinema Home Database Guide

## Overview

The app uses a SQLite database named `cinema_home.db`. The backend creates and seeds it automatically on startup through `db_setup.py` and `api.py`.

## Tables

Core tables include `users`, `password_reset_tokens`, `movies`, `theaters`, `screens`, `seats`, `showtimes`, `bookings`, `booking_seats`, `payments`, and `newsletter_subscribers`.

## Booking Flow

- Signup stores a user in `users` with a hashed password.
- Login returns a JWT and does not write to the database.
- Seat availability comes from `seats` minus `booking_seats` for the selected showtime.
- Creating a booking inserts one row into `bookings` and one row per seat into `booking_seats`.
- The `UNIQUE(showtime_id, seat_id)` constraint prevents double-booking.

## Run Locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python db_setup.py
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

The API is available at `http://127.0.0.1:8000`, and docs are at `/docs`.

## Useful Endpoints

- `POST /auth/signup`
- `POST /auth/login`
- `POST /auth/forgot-password`
- `GET /movies`
- `GET /showtimes`
- `GET /showtimes/{id}/seats`
- `POST /bookings`
- `GET /bookings/{id}`
- `POST /payments/initiate`
- `POST /payments/confirm`

## Notes

- Delete `cinema_home.db` to reset all local data.
- Change `JWT_SECRET` in `api.py` before deploying.
