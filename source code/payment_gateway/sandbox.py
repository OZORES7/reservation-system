from __future__ import annotations

from datetime import datetime, timezone
import secrets
import sqlite3
from typing import Any

from fastapi import HTTPException, status

class SandboxCardError(ValueError):
    pass


TEST_CARDS: tuple[dict[str, str], ...] = (
    {
        "id": "visa_success",
        "label": "Visa Success",
        "brand": "Visa",
        "cardholder_name": "Visa Success Tester",
        "card_number": "4242424242424242",
        "expiry_month": "12",
        "expiry_year": "2030",
        "cvc": "123",
        "outcome": "success",
    },
    {
        "id": "visa_failure",
        "label": "Visa Failure",
        "brand": "Visa",
        "cardholder_name": "Visa Failure Tester",
        "card_number": "4000000000000002",
        "expiry_month": "11",
        "expiry_year": "2030",
        "cvc": "123",
        "outcome": "failed",
    },
    {
        "id": "mastercard_success",
        "label": "MasterCard Success",
        "brand": "MasterCard",
        "cardholder_name": "MasterCard Success Tester",
        "card_number": "5555555555554444",
        "expiry_month": "10",
        "expiry_year": "2030",
        "cvc": "123",
        "outcome": "success",
    },
    {
        "id": "mastercard_failure",
        "label": "MasterCard Failure",
        "brand": "MasterCard",
        "cardholder_name": "MasterCard Failure Tester",
        "card_number": "5105105105105100",
        "expiry_month": "09",
        "expiry_year": "2030",
        "cvc": "123",
        "outcome": "failed",
    },
)


def normalize_card_number(card_number: str) -> str:
    return "".join(character for character in card_number if character.isdigit())


def get_test_cards() -> list[dict[str, str]]:
    return [dict(card) for card in TEST_CARDS]


def _validate_card(card_number: str, expiry_month: int, expiry_year: int, cvc: str) -> dict[str, str]:
    normalized_number = normalize_card_number(card_number)
    matched_card = next((card for card in TEST_CARDS if card["card_number"] == normalized_number), None)
    if not matched_card:
        raise SandboxCardError("Use one of the sandbox Visa or MasterCard test cards.")

    now = datetime.now(timezone.utc)
    if expiry_year < now.year or (expiry_year == now.year and expiry_month < now.month):
        raise SandboxCardError("The sandbox card is expired.")

    if not cvc.isdigit() or len(cvc) not in (3, 4):
        raise SandboxCardError("Enter a valid CVC.")

    return matched_card


def process_test_payment(
    *,
    cardholder_name: str,
    card_number: str,
    expiry_month: int,
    expiry_year: int,
    cvc: str,
) -> dict[str, Any]:
    if not cardholder_name.strip():
        raise SandboxCardError("Enter the cardholder name.")

    matched_card = _validate_card(card_number, expiry_month, expiry_year, cvc)
    provider_ref = f"pi_sandbox_{secrets.token_hex(6)}"
    status = "paid" if matched_card["outcome"] == "success" else "failed"

    return {
        "status": status,
        "provider_ref": provider_ref,
        "card_brand": matched_card["brand"],
        "last4": matched_card["card_number"][-4:],
        "scenario_id": matched_card["id"],
        "message": (
            "Sandbox payment approved. Reservation confirmed."
            if status == "paid"
            else "Sandbox payment declined. Reservation released."
        ),
    }


def _fetch_booking(conn: sqlite3.Connection, booking_id: int) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT id, user_id, showtime_id, booking_code, seats_count, total_amount, status, created_at, updated_at
        FROM bookings
        WHERE id = ?
        """,
        (booking_id,),
    ).fetchone()


def _booking_seat_labels(conn: sqlite3.Connection, booking_id: int) -> list[str]:
    rows = conn.execute(
        """
        SELECT s.seat_label
        FROM booking_seats bs
        JOIN seats s ON s.id = bs.seat_id
        WHERE bs.booking_id = ?
        ORDER BY s.row_label, s.seat_number
        """,
        (booking_id,),
    ).fetchall()
    return [row["seat_label"] for row in rows]


def _release_booking_seats(conn: sqlite3.Connection, booking_id: int) -> list[str]:
    seat_labels = _booking_seat_labels(conn, booking_id)
    conn.execute("DELETE FROM booking_seats WHERE booking_id = ?", (booking_id,))
    return seat_labels


def create_pending_booking(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    showtime_id: int,
    seat_labels: list[str],
) -> dict[str, Any]:
    unique_labels = sorted({label.strip().upper() for label in seat_labels if label and label.strip()})
    if not unique_labels:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Select at least one seat")

    try:
        conn.execute("BEGIN IMMEDIATE")

        showtime = conn.execute(
            "SELECT id, screen_id, base_price, status FROM showtimes WHERE id = ?",
            (showtime_id,),
        ).fetchone()
        if not showtime or showtime["status"] != "scheduled":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Showtime not found or unavailable")

        placeholders = ",".join(["?"] * len(unique_labels))
        seat_rows = conn.execute(
            f"""
            SELECT id, seat_label
            FROM seats
            WHERE screen_id = ? AND seat_label IN ({placeholders}) AND is_active = 1
            """,
            (showtime["screen_id"], *unique_labels),
        ).fetchall()
        if len(seat_rows) != len(unique_labels):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="One or more selected seats are invalid")

        seat_ids = [row["id"] for row in seat_rows]
        conflict_placeholders = ",".join(["?"] * len(seat_ids))
        taken = conn.execute(
            f"""
            SELECT bs.seat_id
            FROM booking_seats bs
            JOIN bookings b ON b.id = bs.booking_id
            WHERE bs.showtime_id = ? AND bs.seat_id IN ({conflict_placeholders}) AND b.status != 'canceled'
            """,
            (showtime_id, *seat_ids),
        ).fetchall()
        if taken:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="One or more seats are already reserved")

        total_amount = float(showtime["base_price"]) * len(unique_labels)
        booking_code = f"BK-{secrets.token_hex(4).upper()}"

        conn.execute(
            """
            INSERT INTO bookings (user_id, showtime_id, booking_code, seats_count, total_amount, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
            """,
            (user_id, showtime_id, booking_code, len(unique_labels), total_amount),
        )
        booking_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

        for seat_id in seat_ids:
            conn.execute(
                "INSERT INTO booking_seats (booking_id, showtime_id, seat_id, price) VALUES (?, ?, ?, ?)",
                (booking_id, showtime_id, seat_id, showtime["base_price"]),
            )

        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except sqlite3.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking conflict. Please choose different seats")

    return {
        "message": "Seats reserved. Complete payment to confirm the reservation.",
        "booking_id": booking_id,
        "booking_code": booking_code,
        "showtime_id": showtime_id,
        "seat_labels": unique_labels,
        "total_amount": total_amount,
        "status": "pending",
        "payment_provider": "stripe_sandbox",
    }


def initiate_payment_session(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    booking_id: int,
) -> dict[str, Any]:
    booking = _fetch_booking(conn, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    if booking["status"] != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking is not pending payment")

    try:
        conn.execute("BEGIN IMMEDIATE")
        existing_payment = conn.execute(
            """
            SELECT id, booking_id, provider, amount, currency, status
            FROM payments
            WHERE booking_id = ? AND status = 'initiated'
            ORDER BY id DESC
            LIMIT 1
            """,
            (booking_id,),
        ).fetchone()

        if existing_payment:
            payment_id = existing_payment["id"]
        else:
            conn.execute(
                "INSERT INTO payments (booking_id, provider, amount, currency, status) VALUES (?, ?, ?, 'USD', 'initiated')",
                (booking_id, "stripe_sandbox", booking["total_amount"]),
            )
            payment_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except sqlite3.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment session could not be created")

    return {
        "message": "Payment session ready",
        "payment_id": payment_id,
        "booking_id": booking_id,
        "status": "initiated",
        "amount": booking["total_amount"],
        "currency": "USD",
        "test_cards": get_test_cards(),
    }


def process_booking_payment(
    conn: sqlite3.Connection,
    *,
    user_id: int,
    payment_id: int,
    cardholder_name: str,
    card_number: str,
    expiry_month: int,
    expiry_year: int,
    cvc: str,
) -> dict[str, Any]:
    try:
        conn.execute("BEGIN IMMEDIATE")
        payment = conn.execute(
            """
            SELECT p.id, p.booking_id, p.provider, p.amount, p.currency, p.status, b.user_id, b.booking_code
            FROM payments p
            JOIN bookings b ON b.id = p.booking_id
            WHERE p.id = ?
            """,
            (payment_id,),
        ).fetchone()
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        if payment["user_id"] != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
        if payment["status"] != "initiated":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment is no longer editable")

        booking = _fetch_booking(conn, payment["booking_id"])
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
        if booking["status"] != "pending":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking is not pending payment")

        try:
            gateway_result = process_test_payment(
                cardholder_name=cardholder_name,
                card_number=card_number,
                expiry_month=expiry_month,
                expiry_year=expiry_year,
                cvc=cvc,
            )
        except SandboxCardError as error:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(error))

        if gateway_result["status"] == "paid":
            conn.execute(
                """
                UPDATE payments
                SET status = 'paid', provider_ref = ?, paid_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (gateway_result["provider_ref"], payment_id),
            )
            conn.execute(
                "UPDATE bookings SET status = 'confirmed', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (booking["id"],),
            )
            booking_status = "confirmed"
            released_seats: list[str] = []
        else:
            released_seats = _release_booking_seats(conn, booking["id"])
            conn.execute(
                """
                UPDATE payments
                SET status = 'failed', provider_ref = ?
                WHERE id = ?
                """,
                (gateway_result["provider_ref"], payment_id),
            )
            conn.execute(
                "UPDATE bookings SET status = 'canceled', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (booking["id"],),
            )
            booking_status = "canceled"

        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except sqlite3.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment could not be processed")

    return {
        "status": gateway_result["status"],
        "message": gateway_result["message"],
        "booking_id": booking["id"],
        "booking_code": booking["booking_code"],
        "booking_status": booking_status,
        "payment_id": payment_id,
        "provider": "stripe_sandbox",
        "provider_ref": gateway_result["provider_ref"],
        "card_brand": gateway_result["card_brand"],
        "card_last4": gateway_result["last4"],
        "scenario_id": gateway_result["scenario_id"],
        "released_seats": released_seats,
    }


def get_booking_details(
    conn: sqlite3.Connection,
    *,
    booking_id: int,
    user_id: int,
) -> dict[str, Any]:
    booking = _fetch_booking(conn, booking_id)
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    payment = conn.execute(
        """
        SELECT id, booking_id, provider, provider_ref, amount, currency, status, created_at, paid_at
        FROM payments
        WHERE booking_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (booking_id,),
    ).fetchone()

    result: dict[str, Any] = dict(booking)
    result["seat_labels"] = _booking_seat_labels(conn, booking_id)
    if payment:
        result["payment"] = dict(payment)
    return result


def cancel_pending_booking(
    conn: sqlite3.Connection,
    *,
    booking_id: int,
    user_id: int,
) -> dict[str, Any]:
    try:
        conn.execute("BEGIN IMMEDIATE")
        booking = _fetch_booking(conn, booking_id)
        if not booking:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
        if booking["user_id"] != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
        if booking["status"] == "confirmed":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Confirmed bookings cannot be canceled here")
        if booking["status"] == "canceled":
            conn.rollback()
            return {
                "status": "canceled",
                "booking_id": booking["id"],
                "booking_code": booking["booking_code"],
                "message": "Reservation already released",
                "released_seats": [],
            }

        released_seats = _release_booking_seats(conn, booking["id"])
        conn.execute(
            "UPDATE bookings SET status = 'canceled', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (booking_id,),
        )
        conn.execute(
            "UPDATE payments SET status = 'failed' WHERE booking_id = ? AND status = 'initiated'",
            (booking_id,),
        )
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except sqlite3.IntegrityError:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking could not be canceled")

    return {
        "status": "canceled",
        "booking_id": booking["id"],
        "booking_code": booking["booking_code"],
        "message": "Reservation released",
        "released_seats": released_seats,
    }
