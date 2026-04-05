# Cinema Online Reservation System - Architecture Document

## 1. Scope
The purpose of this project is to develop a web-based system that simplifies ticket booking, reduces physical queues, and provides management tools for cinema administrators.

## 2. Software Architecture
The system follows a *Client-Server Architecture* to decouple the User Interface from the core business logic.

## 3. Architectural Goals & Constraints
* *Goals:* High performance (under 1s), security (credential management), and high usability (booking under 3 minutes).
* *Constraints:* Must use Python for Backend, HTML/CSS/JS for Frontend, and integrate with an external Payment Gateway API.

## 4. Logical Architecture + (Use Case + ERD)
This view focuses on the functional components and their relationships.
* *User Interface:* Responsive web design for cross-browser compatibility.
* *Business Logic:* Python-based API routes handling movie schedules and seat availability.
* *Data Management:* A relational database to ensure ACID compliance, preventing double-booking of seats.

## 5. Process Architecture + (Sequence Diagram)
Describes the system’s runtime behavior and concurrency handling.

* *Concurrency:* If two users attempt to book the same seat simultaneously, the system uses a *Row Lock* in the database.
* *Availability:* The system allows movie browsing even if the external Payment Gateway is down.
