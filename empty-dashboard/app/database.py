import sqlite3
import os
from pathlib import Path
from flask import g, current_app
from werkzeug.security import generate_password_hash

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'analyst',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    summary TEXT,
    content TEXT,
    author_id INTEGER,
    is_published INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL,
    ip_address TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    details TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
"""

def get_db():
    """Retrieve or create SQLite database connection for current request context."""
    if 'db' not in g:
        db_path = current_app.config['DATABASE_PATH']
        if db_path != ':memory:':
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(db_path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON;")
    return g.db

def close_db(e=None):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db(app=None):
    """Initialize database schema and seed the initial analyst user."""
    if app is None:
        app = current_app

    with app.app_context():
        db_path = app.config['DATABASE_PATH']
        if db_path != ':memory:':
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()
        
        # Execute schema
        cursor.executescript(SCHEMA_SQL)

        # Seed initial test account if not exists
        cursor.execute("SELECT id FROM users WHERE username = ?", ("analyst",))
        existing_user = cursor.fetchone()
        if not existing_user:
            password_hash = generate_password_hash("analyst2026")
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("analyst", password_hash, "analyst")
            )
            # Log initial setup audit event
            user_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO audit_events (user_id, action, ip_address, details) VALUES (?, ?, ?, ?)",
                (user_id, "SYSTEM_INIT", "127.0.0.1", "Initial analyst account provisioned")
            )
            conn.commit()

        # Seed realistic reports if table is empty
        cursor.execute("SELECT COUNT(*) as count FROM reports")
        report_count = cursor.fetchone()["count"]
        if report_count == 0:
            # Retrieve analyst user ID to associate as author
            cursor.execute("SELECT id FROM users WHERE username = ?", ("analyst",))
            analyst_user = cursor.fetchone()
            author_id = analyst_user["id"] if analyst_user else 1

            seed_reports = [
                (
                    "Q2 Telemetry Ingestion Pipeline Verification",
                    "Infrastructure",
                    "Audit of telemetry message brokers and stream partitions across regional data centers.",
                    "All 16 stream brokers passed throughput verification. Average ingress latency remained under 12ms. Standby pipeline 04 is currently idle pending upstream queue dispatch. Diagnostic listeners on local interfaces remain isolated.",
                    author_id,
                    1
                ),
                (
                    "Quarterly Access Control & Privilege Boundary Review",
                    "Compliance",
                    "Assessment of analyst tier permissions and session isolation policies.",
                    "Analyst permissions conform to standard telemetry consumption guidelines. Analysts have read-only visibility into departmental archives and export capabilities. Management and operational debug controls are segregated onto the internal management plane. Refer to internal security audit record #5 for cross-tier boundary validations.",
                    author_id,
                    1
                ),
                (
                    "Diagnostic Subsystem Network Segregation Notice",
                    "Security",
                    "Formal notice on the decommissioning and segregation of legacy telemetry diagnostic services on web nodes.",
                    "Engineering notice: The legacy diagnostic probe endpoint (/internal/debug) has been decoupled from application web nodes. Direct access now terminates with restricted status codes. Diagnostics may only be queried via authorized orchestration controllers.",
                    author_id,
                    1
                ),
                (
                    "Annual Data Retention & Cryptographic Sanitization Audit",
                    "Audit",
                    "Review of database retention routines and secret material handling procedures.",
                    "Audit confirmed zero secret leakage across indexed reporting tables. High-entropy tokens, environment configuration variables, and corporate secrets are strictly excluded from report digests and client-accessible schemas.",
                    author_id,
                    1
                ),
                (
                    "Internal Security & Audit Ledger Telemetry",
                    "Security Audit",
                    "Privileged telemetry observation ledger and export authorization verification.",
                    "Audit ledger record verified under internal diagnostic reference DB-17.\nIngress pipeline reconciler confirms valid session binding context.\nCross-tier observation note: Analyst tier accounts operate under default telemetry partition DB-19. Diagnostic parameter chaining routes session context into restricted telemetry scope.\nAuthorization validation: Ingestion ledger confirmed operational for current session.",
                    author_id,
                    1
                )
            ]

            cursor.executemany(
                """
                INSERT INTO reports (title, category, summary, content, author_id, is_published)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                seed_reports
            )
            conn.commit()

        conn.close()
