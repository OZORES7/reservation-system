# 🎬 Cinema Online Ticket Reservation System

## 👥 Team Details

| Name | Student ID | GitHub Username |
|------------|------------------|-----------------------------|
| Ziad Hatem Wahba | 220513665 | OZORES7 |
| Habibe Hasanoglu | 230513532 | HabiHas |
| Abdulrahman Bahraq | 220513559 | SaBo10K |
| Hasan Albehadili | 210513486 | H190K |
| Zein Alabdin Nashaat | 220513072 | izeinnn |

---

## 📌 Project Introduction

The *Cinema Online Reservation System* is a web-based system designed to make movie ticket booking easier and more efficient.  
The system helps reduce long queues at the cinema and provides cinema management with the necessary tools to manage reservations, schedules, and customers effectively.

---

## 🏗️ System Architecture


🔗 [Architecture Documentation](https://raw.githubusercontent.com/OZORES7/reservation-system/refs/heads/main/ARCHITECTURE.md)

---

## 🗄️ Database Backend

This repo now includes the SQLite + FastAPI backend from the older Movie web version.

To run it locally:

```bash
pip install -r requirements.txt
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

The auth pages and seat booking page talk to `http://127.0.0.1:8000`.
