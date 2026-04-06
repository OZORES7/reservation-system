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

## 6. Development Architecture + (C4 Level 2 (Container))
Focuses on the software organization and the development environment.

### Structure
* *Frontend:* HTML, CSS, and JS files.
* *Backend:* Python scripts and API routes.
* *docs/:* Documentation and architectural diagrams.

*Rationale:* Python was selected for rapid development and its robust library support for ORM and API handling.

## 7. Physical Architecture (Deployment) + (Deployment Diagram)
Describes the physical distribution of components.

* *Environment:* A web-based platform accessible through modern browsers.
* *Deployment:* The Backend and Frontend are hosted on a web server, connecting over the network to a Relational Database and an external Payment Gateway.

## 8. Scenarios
* *Successful Reservation:* User clicks book -> Frontend checks seat -> Backend queries DB -> Success returned.
* *Simultaneous Booking:* Two users click "Book" for seat A1 -> System locks row; User 1 succeeds, User 2 receives error.


## 9. Size and Performance
* *Performance:* All reservation requests must complete in less than 1 second.
* *Capacity:* Designed to handle multiple concurrent users via efficient database transactions.

## 10. Quality
* *Security:* External payment gateway integration and credential management.
* *Reliability:* ACID properties guarantee that transactions are processed reliably.
* *Risk Mitigation:* An abstraction layer is implemented to allow switching between payment providers if needed.

## Appendices

### Acronyms and Abbreviations
* *ACID:* Atomicity, Consistency, Isolation, Durability
* *API:* Application Programming Interface
* *ORM:* Object-Relational Mapping

### Definitions
* *Double-Booking:* A failure state where one seat is sold to two different customers.

### Design Principles
* *Decoupling:* Separating the UI from logic via Client-Server architecture.
* *Abstraction:* Using layers to reduce dependency on external third-party services.
