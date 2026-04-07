from pathlib import Path
import sqlite3

import db_setup


def main() -> None:
    db_path = Path(__file__).resolve().parent / db_setup.DB_NAME
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")

    booking_count = conn.execute("SELECT COUNT(*) FROM bookings").fetchone()[0]
    seat_count = conn.execute("SELECT COUNT(*) FROM booking_seats").fetchone()[0]
    payment_count = conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0]

    with conn:
        conn.execute("DELETE FROM payments")
        conn.execute("DELETE FROM booking_seats")
        conn.execute("DELETE FROM bookings")

    print(f"Cleared bookings={booking_count}, booking_seats={seat_count}, payments={payment_count}")
    print(f"Database reset complete: {db_path}")


if __name__ == "__main__":
    main()
