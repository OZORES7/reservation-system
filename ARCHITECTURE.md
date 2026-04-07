# Cinema Online Reservation System - Architecture

## Overview

This project uses a simple client-server setup:

- Frontend: HTML, CSS, and JavaScript files in `source code/`
- Backend: FastAPI application in `source code/api.py`
- Database: SQLite file in `source code/cinema_home.db`
- Payment flow: local sandbox logic in `source code/payment_gateway/`

## Scope

The system provides:

- Online movie ticket booking with seat selection
- User account management (registration, login)
- Movie and showtime browsing
- Seat reservation with locking to prevent double-booking
- Booking confirmation via sandbox payment flow

## Constraints

- Python backend with FastAPI framework
- HTML/CSS/JS frontend (static files)
- SQLite database for persistence
- Sandbox payment integration (no real payments)

## Logical Architecture

The main functional view of the system.

![Use Case Diagram](ARCHITECTURE%20IMGS/logical-use-case.png)
![ERD](ARCHITECTURE%20IMGS/logical-erd.jpeg)

## Process Architecture

Runtime behavior and concurrency handling.

![Concurrency](ARCHITECTURE%20IMGS/process-concurrency.png)
![Availability](ARCHITECTURE%20IMGS/process-availability.png)

### Runtime Flow

1. The user opens the movie listing in the browser.
2. Clicking a movie sends the selected showtime and poster into the seat booking page.
3. The booking page requests seat availability from the FastAPI backend.
4. The user selects seats and creates a booking.
5. The sandbox payment flow confirms or cancels the booking.

### Data Flow

- User accounts, bookings, seats, and payments are stored in SQLite.
- The API seeds sample movies, showtimes, and seats if the database is empty.
- Seat locking is handled by the database so two users cannot confirm the same seat at the same time.

## Development Architecture

How the codebase is organized.

![C4 Container](ARCHITECTURE%20IMGS/development-container.png)

- Frontend: HTML, CSS, and JavaScript pages.
- Backend: Python API routes and helper modules.
- Docs: architecture notes and payment flow documentation.

Python is used for the backend because it is fast to develop with and fits the API/database workflow in this project.

## Physical Architecture

How the application is deployed and accessed.

![Deployment Diagram](ARCHITECTURE%20IMGS/physical-deployment.png)

## Size & Performance

- Performance target: reservation requests should complete quickly enough for a smooth booking flow.
- Capacity target: the system should support multiple users through database transactions and seat locking.

## Quality

- Security: authentication, password hashing, and payment sandboxing.
- Reliability: ACID-style database behavior for bookings and seat allocation.
- Flexibility: payment handling is isolated so providers can be swapped later.

## Scenarios

Example booking outcomes.

![Successful Reservation](ARCHITECTURE%20IMGS/scenario-successful-reservation.png)
![Simultaneous Booking](ARCHITECTURE%20IMGS/scenario-simultaneous-booking.png)

## Deployment

The included launch scripts run the app locally:

- `run_app.bat` on Windows
- `run_app.sh` on macOS/Linux

Both scripts start the API on port `8000` and a static frontend server on port `3000`.

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [MDN Web Docs - HTML/CSS/JS](https://developer.mozilla.org/)
- [Uvicorn Documentation](https://www.uvicorn.org/)

## Appendices

### Acronyms

- ACID: Atomicity, Consistency, Isolation, Durability
- API: Application Programming Interface
- ORM: Object-Relational Mapping

### Definitions

- Double-booking: the same seat being reserved by more than one user.

### Design Principles

- Decoupling: UI and backend logic are separated.
- Abstraction: payment logic is isolated behind the gateway layer.