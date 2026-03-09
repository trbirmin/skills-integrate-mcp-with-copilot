"""Persistence layer for the school activities API.

This module introduces a small SQLite-backed repository with validated models.
It preserves existing activity behaviors while creating foundational tables for
future features (users, clubs, memberships, events, notifications).
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from typing import Dict, Iterator, List

from pydantic import BaseModel, ConfigDict, Field


class UserModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str
    role: str = Field(pattern="^(STUDENT|CLUB_LEAD|ADMIN)$")
    full_name: str | None = None


class ClubModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    category: str
    description: str
    status: str = Field(pattern="^(PENDING|APPROVED)$")
    lead_email: str | None = None


class MembershipModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_email: str
    club_name: str
    status: str = Field(pattern="^(PENDING|APPROVED|REJECTED)$")


class EventModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    schedule: str
    max_participants: int = Field(gt=0)
    club_name: str | None = None


class NotificationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    body: str
    audience: str = "ALL"


class ActivityView(BaseModel):
    model_config = ConfigDict(extra="forbid")

    description: str
    schedule: str
    max_participants: int
    participants: List[str]


SEED_ACTIVITIES: Dict[str, Dict[str, object]] = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"],
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"],
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"],
    },
}


class Storage:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    role TEXT NOT NULL CHECK (role IN ('STUDENT', 'CLUB_LEAD', 'ADMIN')),
                    full_name TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS clubs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('PENDING', 'APPROVED')),
                    lead_user_id INTEGER,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lead_user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS memberships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    club_id INTEGER NOT NULL,
                    status TEXT NOT NULL CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (user_id, club_id),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (club_id) REFERENCES clubs(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT NOT NULL,
                    schedule TEXT NOT NULL,
                    max_participants INTEGER NOT NULL CHECK (max_participants > 0),
                    club_id INTEGER,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (club_id) REFERENCES clubs(id)
                );

                CREATE TABLE IF NOT EXISTS event_registrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (event_id, user_id),
                    FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    audience TEXT NOT NULL DEFAULT 'ALL',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

            seeded = conn.execute("SELECT COUNT(1) AS count FROM events").fetchone()["count"]
            if seeded == 0:
                self._seed_initial_data(conn)

    def _seed_initial_data(self, conn: sqlite3.Connection) -> None:
        default_club = ClubModel(
            name="General Activities",
            category="School",
            description="School-wide extracurricular activities",
            status="APPROVED",
        )
        conn.execute(
            """
            INSERT INTO clubs (name, category, description, status)
            VALUES (?, ?, ?, ?)
            """,
            (
                default_club.name,
                default_club.category,
                default_club.description,
                default_club.status,
            ),
        )
        club_id = conn.execute(
            "SELECT id FROM clubs WHERE name = ?", (default_club.name,)
        ).fetchone()["id"]

        for name, details in SEED_ACTIVITIES.items():
            event_model = EventModel(
                name=name,
                description=str(details["description"]),
                schedule=str(details["schedule"]),
                max_participants=int(details["max_participants"]),
                club_name=default_club.name,
            )

            conn.execute(
                """
                INSERT INTO events (name, description, schedule, max_participants, club_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event_model.name,
                    event_model.description,
                    event_model.schedule,
                    event_model.max_participants,
                    club_id,
                ),
            )
            event_id = conn.execute(
                "SELECT id FROM events WHERE name = ?", (event_model.name,)
            ).fetchone()["id"]

            for participant in details["participants"]:
                user_model = UserModel(email=str(participant), role="STUDENT")
                conn.execute(
                    """
                    INSERT INTO users (email, role)
                    VALUES (?, ?)
                    ON CONFLICT(email) DO NOTHING
                    """,
                    (user_model.email, user_model.role),
                )
                user_id = conn.execute(
                    "SELECT id FROM users WHERE email = ?", (user_model.email,)
                ).fetchone()["id"]
                conn.execute(
                    """
                    INSERT INTO event_registrations (event_id, user_id)
                    VALUES (?, ?)
                    ON CONFLICT(event_id, user_id) DO NOTHING
                    """,
                    (event_id, user_id),
                )

    def get_activities(self) -> Dict[str, Dict[str, object]]:
        with self.connection() as conn:
            events = conn.execute(
                """
                SELECT id, name, description, schedule, max_participants
                FROM events
                ORDER BY name ASC
                """
            ).fetchall()

            payload: Dict[str, Dict[str, object]] = {}
            for event in events:
                participants = conn.execute(
                    """
                    SELECT u.email
                    FROM event_registrations er
                    JOIN users u ON u.id = er.user_id
                    WHERE er.event_id = ?
                    ORDER BY er.id ASC
                    """,
                    (event["id"],),
                ).fetchall()

                view = ActivityView(
                    description=event["description"],
                    schedule=event["schedule"],
                    max_participants=event["max_participants"],
                    participants=[row["email"] for row in participants],
                )
                payload[event["name"]] = view.model_dump()

            return payload

    def signup_for_activity(self, activity_name: str, email: str) -> bool:
        with self._lock:
            with self.connection() as conn:
                event = conn.execute(
                    "SELECT id FROM events WHERE name = ?", (activity_name,)
                ).fetchone()
                if event is None:
                    return False

                user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
                if user is None:
                    user_model = UserModel(email=email, role="STUDENT")
                    conn.execute(
                        "INSERT INTO users (email, role) VALUES (?, ?)",
                        (user_model.email, user_model.role),
                    )
                    user = conn.execute(
                        "SELECT id FROM users WHERE email = ?", (email,)
                    ).fetchone()

                already_registered = conn.execute(
                    """
                    SELECT 1
                    FROM event_registrations
                    WHERE event_id = ? AND user_id = ?
                    """,
                    (event["id"], user["id"]),
                ).fetchone()
                if already_registered:
                    raise ValueError("Student is already signed up")

                conn.execute(
                    "INSERT INTO event_registrations (event_id, user_id) VALUES (?, ?)",
                    (event["id"], user["id"]),
                )
                return True

    def unregister_from_activity(self, activity_name: str, email: str) -> bool:
        with self._lock:
            with self.connection() as conn:
                event = conn.execute(
                    "SELECT id FROM events WHERE name = ?", (activity_name,)
                ).fetchone()
                if event is None:
                    return False

                user = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
                if user is None:
                    raise ValueError("Student is not signed up for this activity")

                registration = conn.execute(
                    """
                    SELECT id
                    FROM event_registrations
                    WHERE event_id = ? AND user_id = ?
                    """,
                    (event["id"], user["id"]),
                ).fetchone()
                if registration is None:
                    raise ValueError("Student is not signed up for this activity")

                conn.execute(
                    "DELETE FROM event_registrations WHERE id = ?", (registration["id"],)
                )
                return True