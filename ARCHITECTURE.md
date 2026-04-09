# Cinema Online Reservation System

## Title Page

**Document**: Software Architecture (4+1 View Model)
**Project**: Cinema Online Ticket Reservation System
**Repository**: `reservation-system`
**Version**: 1.0
**Date**: 2026-04-09

## Change History

| Date | Version | Author(s) | Change |
|---|---:|---|---|
| 2026-04-09 | 1.0 | Team | Reordered content to required template; aligned sections with 4+1 views; fixed diagram paths. |

## Table of Contents

- [Title Page](#title-page)
- [Change History](#change-history)
- [Table of Contents](#table-of-contents)
- [List of Figures](#list-of-figures)
- [1. Scope](#1-scope)
- [2. References](#2-references)
- [3. Software Architecture](#3-software-architecture)
- [4. Architectural Goals & Constraints](#4-architectural-goals--constraints)
- [5. Logical Architecture](#5-logical-architecture)
- [6. Process Architecture](#6-process-architecture)
- [7. Development Architecture](#7-development-architecture)
- [8. Physical Architecture](#8-physical-architecture)
- [9. Scenarios](#9-scenarios)
- [10. Size and Performance](#10-size-and-performance)
- [11. Quality](#11-quality)
- [Appendices](#appendices)
  - [Acronyms and Abbreviations](#acronyms-and-abbreviations)
  - [Definitions](#definitions)
  - [Design Principles](#design-principles)

## List of Figures

1. **Use Case Diagram** — `ARCHITECTURE%20IMGS/logical-use-case.png`
2. **ERD** — `ARCHITECTURE%20IMGS/logical-erd.jpeg`
3. **Concurrency** — `ARCHITECTURE%20IMGS/process-concurrency.png`
4. **Availability** — `ARCHITECTURE%20IMGS/process-availability.png`
5. **C4 Container** — `ARCHITECTURE%20IMGS/development-container.png`
6. **Deployment Diagram** — `ARCHITECTURE%20IMGS/physical-deployment.png`
7. **Successful Reservation** — `ARCHITECTURE%20IMGS/scenario-successful-reservation.png`
8. **Simultaneous Booking** — `ARCHITECTURE%20IMGS/scenario-simultaneous-booking.png`

## 1. Scope

The system provides:

- Online movie ticket booking with seat selection
- User account management (registration, login)
- Movie and showtime browsing
- Seat reservation with locking to prevent double-booking
- Booking confirmation via sandbox payment flow

## 2. References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [MDN Web Docs - HTML/CSS/JS](https://developer.mozilla.org/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- P. B. Kruchten, *Architectural Blueprints—The “4+1” View Model of Software Architecture*
- [4+1 architectural view model (Wikipedia)](https://en.wikipedia.org/wiki/4%2B1_architectural_view_model)

## 3. Software Architecture

This project uses a simple client-server setup:

- **Frontend**: HTML, CSS, and JavaScript files in `source code/`
- **Backend**: FastAPI application in `source code/api.py`
- **Database**: SQLite file `source code/cinema_home.db` (created by `source code/db_setup.py`)
- **Payment flow**: local sandbox logic in `source code/payment_gateway/`

At runtime, the browser UI calls the backend API to fetch movies/showtimes, retrieve seat availability, create a pending booking, and then confirm/cancel the booking through a sandbox payment flow.

## 4. Architectural Goals & Constraints

### Goals

- **Correctness**: prevent double-booking for the same showtime seat.
- **Usability**: keep the booking flow simple (browse → select seats → pay).
- **Maintainability**: keep payment handling isolated so providers can be swapped later.

### Constraints

- **Backend**: Python with FastAPI framework.
- **Frontend**: static HTML/CSS/JS (no SPA framework requirement).
- **Persistence**: SQLite database.
- **Payments**: sandbox only (no real payment processing).

## 5. Logical Architecture

The main functional view of the system (Kruchten’s logical view) is captured by the use cases and the domain data model.

![Use Case Diagram](ARCHITECTURE%20IMGS/logical-use-case.png)

The data model is implemented in SQLite tables such as `users`, `movies`, `showtimes`, `seats`, `bookings`, `booking_seats`, and `payments` (see `source code/db_setup.py`).

![ERD](ARCHITECTURE%20IMGS/logical-erd.jpeg)

## 6. Process Architecture

Runtime behavior and concurrency handling (Kruchten’s process view).

![Concurrency](ARCHITECTURE%20IMGS/process-concurrency.png)
![Availability](ARCHITECTURE%20IMGS/process-availability.png)

### Runtime Flow

1. The user opens the movie listing in the browser.
2. Clicking a movie sends the selected showtime and poster into the seat booking page.
3. The booking page requests seat availability from the FastAPI backend.
4. The user selects seats and creates a booking (status: `pending`).
5. The sandbox payment flow confirms (`confirmed`) or cancels (`canceled`) the booking.

### Data Flow and Concurrency Notes

- User accounts, bookings, seats, and payments are stored in SQLite.
- The API seeds sample movies, showtimes, and seats if the database is empty (startup in `source code/api.py`).
- Seat locking is handled through SQLite constraints and immediate transactions to ensure two users cannot confirm the same seat for the same showtime.

## 7. Development Architecture

How the codebase is organized (Kruchten’s development view).

![C4 Container](ARCHITECTURE%20IMGS/development-container.png)

- **Frontend**: HTML/CSS/JS pages under `source code/` (served via a static server).
- **Backend**: `source code/api.py` (FastAPI app) + helper modules (e.g., `source code/db_setup.py`, `source code/payment_gateway/`).
- **Docs**: `README.md`, `ARCHITECTURE.md`, and diagrams under `ARCHITECTURE%20IMGS/`.

Python is used for the backend because it is fast to develop with and fits the API/database workflow in this project.

## 8. Physical Architecture

How the application is deployed and accessed (Kruchten’s physical view).

![Deployment Diagram](ARCHITECTURE%20IMGS/physical-deployment.png)

### Local Deployment (Course Submission)

The included launch scripts run the app locally:

- `source code/run_app.bat` on Windows
- `source code/run_app.sh` on macOS/Linux

Both scripts start:

- **API**: `http://127.0.0.1:8000`
- **Frontend**: `http://127.0.0.1:3000`

## 9. Scenarios

Example booking outcomes (Kruchten’s “+1” view).

![Successful Reservation](ARCHITECTURE%20IMGS/scenario-successful-reservation.png)
![Simultaneous Booking](ARCHITECTURE%20IMGS/scenario-simultaneous-booking.png)

## 10. Size and Performance

- **Performance target**: reservation requests should complete quickly enough for a smooth booking flow.
- **Capacity target**: the system should support multiple users through database transactions and seat locking.

## 11. Quality

- **Security**: authentication, password hashing, and payment sandboxing.
- **Reliability**: ACID-style database behavior for bookings and seat allocation.
- **Flexibility**: payment handling is isolated so providers can be swapped later.

## Appendices

### Acronyms and Abbreviations

- ACID: Atomicity, Consistency, Isolation, Durability
- API: Application Programming Interface
- ORM: Object-Relational Mapping

### Definitions

- Double-booking: the same seat being reserved by more than one user for the same showtime.

### Design Principles

- Decoupling: UI and backend logic are separated.
- Abstraction: payment logic is isolated behind the gateway layer.