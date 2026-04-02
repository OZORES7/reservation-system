import sqlite3
from pathlib import Path

DB_NAME = "cinema_home.db"


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    schema_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'customer' CHECK(role IN ('customer', 'admin')),
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS password_reset_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token_hash TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        used_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        duration_minutes INTEGER NOT NULL,
        genre TEXT,
        language TEXT,
        release_date TEXT,
        poster_url TEXT,
        status TEXT NOT NULL DEFAULT 'now_showing' CHECK(status IN ('coming_soon', 'now_showing', 'archived')),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS theaters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        city TEXT,
        address TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS screens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        theater_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        total_seats INTEGER NOT NULL CHECK(total_seats > 0),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (theater_id) REFERENCES theaters(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS seats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        screen_id INTEGER NOT NULL,
        seat_label TEXT NOT NULL,
        row_label TEXT NOT NULL,
        seat_number INTEGER NOT NULL,
        seat_type TEXT NOT NULL DEFAULT 'regular' CHECK(seat_type IN ('regular', 'premium')),
        is_active INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (screen_id) REFERENCES screens(id) ON DELETE CASCADE,
        UNIQUE (screen_id, seat_label)
    );

    CREATE TABLE IF NOT EXISTS showtimes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        movie_id INTEGER NOT NULL,
        screen_id INTEGER NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        base_price REAL NOT NULL CHECK(base_price >= 0),
        status TEXT NOT NULL DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'canceled', 'completed')),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (movie_id) REFERENCES movies(id) ON DELETE CASCADE,
        FOREIGN KEY (screen_id) REFERENCES screens(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        showtime_id INTEGER NOT NULL,
        booking_code TEXT NOT NULL UNIQUE,
        seats_count INTEGER NOT NULL CHECK(seats_count > 0),
        total_amount REAL NOT NULL CHECK(total_amount >= 0),
        status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'confirmed', 'canceled')),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (showtime_id) REFERENCES showtimes(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS booking_seats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL,
        showtime_id INTEGER NOT NULL,
        seat_id INTEGER NOT NULL,
        price REAL NOT NULL CHECK(price >= 0),
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE,
        FOREIGN KEY (showtime_id) REFERENCES showtimes(id) ON DELETE CASCADE,
        FOREIGN KEY (seat_id) REFERENCES seats(id) ON DELETE CASCADE,
        UNIQUE (showtime_id, seat_id)
    );

    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id INTEGER NOT NULL,
        provider TEXT,
        provider_ref TEXT,
        amount REAL NOT NULL CHECK(amount >= 0),
        currency TEXT NOT NULL DEFAULT 'USD',
        status TEXT NOT NULL DEFAULT 'initiated' CHECK(status IN ('initiated', 'paid', 'failed', 'refunded')),
        paid_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS newsletter_subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT NOT NULL UNIQUE,
        subscribed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        is_active INTEGER NOT NULL DEFAULT 1
    );

    CREATE INDEX IF NOT EXISTS idx_showtimes_movie_id ON showtimes(movie_id);
    CREATE INDEX IF NOT EXISTS idx_showtimes_screen_id ON showtimes(screen_id);
    CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings(user_id);
    CREATE INDEX IF NOT EXISTS idx_bookings_showtime_id ON bookings(showtime_id);
    CREATE INDEX IF NOT EXISTS idx_booking_seats_booking_id ON booking_seats(booking_id);
    """
    conn.executescript(schema_sql)


def main() -> None:
    project_dir = Path(__file__).resolve().parent
    db_path = project_dir / DB_NAME

    with get_connection(db_path) as conn:
        create_tables(conn)

    print(f"Database created successfully: {db_path}")


if __name__ == "__main__":
    main()
