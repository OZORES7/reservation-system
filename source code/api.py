from starlette.middleware import Middleware

original_iter = Middleware.__iter__


def patched_iter(self):
    yield self.cls
    yield {**dict(self.args), **self.kwargs}


Middleware.__iter__ = patched_iter

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hashlib
from pathlib import Path
import secrets
import sqlite3
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field

import db_setup
from payment_gateway import (
    cancel_pending_booking,
    create_pending_booking,
    get_booking_details,
    get_test_cards,
    initiate_payment_session,
    process_booking_payment,
)


DB_PATH = Path(__file__).resolve().parent / db_setup.DB_NAME
JWT_SECRET = "change-this-secret-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 12
PBKDF2_ITERATIONS = 390000

auth_scheme = HTTPBearer()

app = FastAPI(title="Cinema Home API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class BookingRequest(BaseModel):
    showtime_id: int
    seat_labels: list[str] = Field(min_length=1)


class PaymentInitRequest(BaseModel):
    booking_id: int
    provider: str = "stripe_sandbox"


class PaymentConfirmRequest(BaseModel):
    payment_id: int
    cardholder_name: str = Field(min_length=2, max_length=60)
    card_number: str = Field(min_length=12, max_length=24)
    expiry_month: int = Field(ge=1, le=12)
    expiry_year: int = Field(ge=2024, le=2100)
    cvc: str = Field(min_length=3, max_length=4)


class PaymentCheckoutRequest(BaseModel):
    payment_id: int
    provider: str = "stripe_sandbox"
    cardholder_name: str = Field(min_length=2, max_length=60)
    card_number: str = Field(min_length=12, max_length=24)
    expiry_month: int = Field(ge=1, le=12)
    expiry_year: int = Field(ge=2024, le=2100)
    cvc: str = Field(min_length=3, max_length=4)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    ).hex()
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${password_hash}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt, expected_hash = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), int(iterations)
        ).hex()
        return secrets.compare_digest(candidate_hash, expected_hash)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: int, username: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "username": username,
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> dict[str, Any]:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    with get_conn() as conn:
        user = conn.execute(
            "SELECT id, username, email FROM users WHERE id = ?", (user_id,)
        ).fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    return dict(user)


def seed_data(conn: sqlite3.Connection) -> None:
    movie_count = conn.execute("SELECT COUNT(*) AS c FROM movies").fetchone()["c"]
    if movie_count == 0:
        movies = [
            (
                "Barbie",
                "Fantasy comedy",
                114,
                "Comedy",
                "English",
                "2023-07-21",
                "img/home1.jpg",
                "now_showing",
            ),
            (
                "Oppenheimer",
                "Biographical drama",
                180,
                "Drama",
                "English",
                "2023-07-21",
                "img/home2.jpg",
                "now_showing",
            ),
            (
                "Spider-Man: No Way Home",
                "Marvel action",
                148,
                "Action",
                "English",
                "2021-12-17",
                "img/home3.jpg",
                "now_showing",
            ),
        ]
        conn.executemany(
            """
            INSERT INTO movies (title, description, duration_minutes, genre, language, release_date, poster_url, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            movies,
        )

    theater = conn.execute("SELECT id FROM theaters LIMIT 1").fetchone()
    if not theater:
        conn.execute(
            "INSERT INTO theaters (name, city, address) VALUES (?, ?, ?)",
            ("Cinema Home", "Local", "Main Street"),
        )
        theater_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    else:
        theater_id = theater["id"]

    screen = conn.execute(
        "SELECT id FROM screens WHERE theater_id = ? LIMIT 1", (theater_id,)
    ).fetchone()
    if not screen:
        conn.execute(
            "INSERT INTO screens (theater_id, name, total_seats) VALUES (?, ?, ?)",
            (theater_id, "Screen 1", 120),
        )
        screen_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    else:
        screen_id = screen["id"]

    seat_count = conn.execute(
        "SELECT COUNT(*) AS c FROM seats WHERE screen_id = ?", (screen_id,)
    ).fetchone()["c"]
    if seat_count == 0:
        seat_rows = []
        for row_label in "ABCDEFGHIJ":
            for seat_number in range(1, 13):
                seat_rows.append(
                    (
                        screen_id,
                        f"{row_label}{seat_number}",
                        row_label,
                        seat_number,
                        "regular",
                        1,
                    )
                )
        conn.executemany(
            """
            INSERT INTO seats (screen_id, seat_label, row_label, seat_number, seat_type, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            seat_rows,
        )

    showtime_count = conn.execute("SELECT COUNT(*) AS c FROM showtimes").fetchone()["c"]
    if showtime_count == 0:
        movies = conn.execute("SELECT id FROM movies ORDER BY id LIMIT 3").fetchall()
        start = datetime.now().replace(minute=0, second=0, microsecond=0)
        showtimes = []
        for idx, movie in enumerate(movies):
            show_start = start + timedelta(hours=(idx + 1) * 3)
            show_end = show_start + timedelta(hours=2)
            showtimes.append(
                (
                    movie["id"],
                    screen_id,
                    show_start.isoformat(),
                    show_end.isoformat(),
                    10.0,
                    "scheduled",
                )
            )
        conn.executemany(
            """
            INSERT INTO showtimes (movie_id, screen_id, start_time, end_time, base_price, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            showtimes,
        )


def seed_test_user(conn: sqlite3.Connection) -> None:
    existing_user = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        ("test",),
    ).fetchone()

    password_hash = hash_password("test123")
    if existing_user:
        conn.execute(
            """
            UPDATE users
            SET email = ?, password_hash = ?, is_active = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            ("test@example.com", password_hash, existing_user["id"]),
        )
    else:
        conn.execute(
            """
            INSERT INTO users (username, email, password_hash, role, is_active)
            VALUES (?, ?, ?, 'customer', 1)
            """,
            ("test", "test@example.com", password_hash),
        )


@app.on_event("startup")
def startup_event() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with db_setup.get_connection(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        db_setup.create_tables(conn)
        seed_data(conn)
        seed_test_user(conn)


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Cinema Home API running"}


@app.post("/auth/signup")
def signup(payload: SignupRequest) -> dict[str, Any]:
    with get_conn() as conn:
        exists = conn.execute(
            "SELECT id FROM users WHERE username = ? OR email = ?",
            (payload.username, payload.email),
        ).fetchone()
        if exists:
            raise HTTPException(
                status_code=409, detail="Username or email already exists"
            )

        conn.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (payload.username, payload.email, hash_password(payload.password)),
        )
        user_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

    return {"message": "Account created", "user_id": user_id}


@app.post("/auth/login")
def login(payload: LoginRequest) -> dict[str, Any]:
    with get_conn() as conn:
        user = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (payload.username,),
        ).fetchone()

    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(user["id"], user["username"])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user["id"], "username": user["username"]},
    }


@app.post("/auth/forgot-password")
def forgot_password(payload: ForgotPasswordRequest) -> dict[str, str]:
    with get_conn() as conn:
        user = conn.execute(
            "SELECT id FROM users WHERE email = ?", (payload.email,)
        ).fetchone()
        if user:
            raw_token = secrets.token_urlsafe(24)
            token_hash = sha256(raw_token.encode("utf-8")).hexdigest()
            expires_at = (
                datetime.now(timezone.utc) + timedelta(minutes=30)
            ).isoformat()
            conn.execute(
                "INSERT INTO password_reset_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
                (user["id"], token_hash, expires_at),
            )

    return {"message": "If that email exists, a reset link has been generated"}


@app.get("/auth/me")
def get_current_user_profile(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    with get_conn() as conn:
        user = conn.execute(
            "SELECT id, username, email, role, created_at FROM users WHERE id = ?",
            (current_user["id"],),
        ).fetchone()
    return dict(user) if user else {}


@app.get("/movies")
def get_movies() -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, description, duration_minutes, genre, language, release_date, poster_url, status FROM movies ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/showtimes")
def get_showtimes(movie_id: int | None = None) -> list[dict[str, Any]]:
    sql = """
    SELECT st.id, st.movie_id, m.title AS movie_title, st.screen_id, st.start_time, st.end_time, st.base_price, st.status
    FROM showtimes st
    JOIN movies m ON m.id = st.movie_id
    """
    params: tuple[Any, ...] = ()
    if movie_id is not None:
        sql += " WHERE st.movie_id = ?"
        params = (movie_id,)
    sql += " ORDER BY st.start_time"

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


@app.get("/showtimes/{showtime_id}/seats")
def get_showtime_seats(showtime_id: int) -> dict[str, Any]:
    with get_conn() as conn:
        showtime = conn.execute(
            """
            SELECT st.id, st.screen_id, st.movie_id, m.title AS movie_title, m.poster_url
            FROM showtimes st
            JOIN movies m ON m.id = st.movie_id
            WHERE st.id = ?
            """,
            (showtime_id,),
        ).fetchone()
        if not showtime:
            raise HTTPException(status_code=404, detail="Showtime not found")

        all_seats = conn.execute(
            "SELECT seat_label FROM seats WHERE screen_id = ? AND is_active = 1 ORDER BY row_label, seat_number",
            (showtime["screen_id"],),
        ).fetchall()

        booked = conn.execute(
            """
            SELECT s.seat_label
            FROM booking_seats bs
            JOIN seats s ON s.id = bs.seat_id
            JOIN bookings b ON b.id = bs.booking_id
            WHERE bs.showtime_id = ? AND b.status != 'canceled'
            """,
            (showtime_id,),
        ).fetchall()

    return {
        "showtime_id": showtime_id,
        "movie_id": showtime["movie_id"],
        "movie_title": showtime["movie_title"],
        "poster_url": showtime["poster_url"],
        "all_seats": [r["seat_label"] for r in all_seats],
        "booked_seats": [r["seat_label"] for r in booked],
    }


@app.post("/bookings")
def create_booking(
    payload: BookingRequest, current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    with get_conn() as conn:
        return create_pending_booking(
            conn,
            user_id=current_user["id"],
            showtime_id=payload.showtime_id,
            seat_labels=payload.seat_labels,
        )


@app.get("/bookings/{booking_id}")
def get_booking(
    booking_id: int, current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    with get_conn() as conn:
        return get_booking_details(
            conn, booking_id=booking_id, user_id=current_user["id"]
        )


@app.post("/bookings/{booking_id}/cancel")
def cancel_booking(
    booking_id: int, current_user: dict[str, Any] = Depends(get_current_user)
) -> dict[str, Any]:
    with get_conn() as conn:
        return cancel_pending_booking(
            conn, booking_id=booking_id, user_id=current_user["id"]
        )


@app.get("/payments/test-cards")
def payment_test_cards() -> dict[str, Any]:
    return {"provider": "stripe_sandbox", "cards": get_test_cards()}


@app.post("/payments/initiate")
def payment_initiate(
    payload: PaymentInitRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    with get_conn() as conn:
        return initiate_payment_session(
            conn, user_id=current_user["id"], booking_id=payload.booking_id
        )


@app.post("/payments/confirm")
def payment_confirm(
    payload: PaymentConfirmRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    with get_conn() as conn:
        return process_booking_payment(
            conn,
            user_id=current_user["id"],
            payment_id=payload.payment_id,
            cardholder_name=payload.cardholder_name,
            card_number=payload.card_number,
            expiry_month=payload.expiry_month,
            expiry_year=payload.expiry_year,
            cvc=payload.cvc,
        )


@app.post("/payments/checkout")
def payment_checkout(
    payload: PaymentCheckoutRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    with get_conn() as conn:
        return process_booking_payment(
            conn,
            user_id=current_user["id"],
            payment_id=payload.payment_id,
            cardholder_name=payload.cardholder_name,
            card_number=payload.card_number,
            expiry_month=payload.expiry_month,
            expiry_year=payload.expiry_year,
            cvc=payload.cvc,
        )
