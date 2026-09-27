from werkzeug.security import check_password_hash, generate_password_hash
from app.database import get_db

class User:
    """User data access layer using parameterized queries."""

    @staticmethod
    def get_by_username(username: str):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cursor.fetchone()

    @staticmethod
    def get_by_id(user_id: int):
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return cursor.fetchone()

    @staticmethod
    def verify_password(user_row, password: str) -> bool:
        if not user_row or not user_row['password_hash']:
            return False
        return check_password_hash(user_row['password_hash'], password)

    @staticmethod
    def create(username: str, password: str, role: str = "analyst"):
        db = get_db()
        cursor = db.cursor()
        password_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role)
        )
        db.commit()
        return cursor.lastrowid


class Report:
    """Report data access layer using parameterized queries."""

    @staticmethod
    def get_all(published_only: bool = True):
        db = get_db()
        cursor = db.cursor()
        if published_only:
            cursor.execute(
                """
                SELECT r.*, u.username as author_username 
                FROM reports r 
                LEFT JOIN users u ON r.author_id = u.id 
                WHERE r.is_published = 1 
                ORDER BY r.created_at DESC
                """
            )
        else:
            cursor.execute(
                """
                SELECT r.*, u.username as author_username 
                FROM reports r 
                LEFT JOIN users u ON r.author_id = u.id 
                ORDER BY r.created_at DESC
                """
            )
        return cursor.fetchall()

    @staticmethod
    def get_by_id(report_id: int):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT r.*, u.username as author_username 
            FROM reports r 
            LEFT JOIN users u ON r.author_id = u.id 
            WHERE r.id = ?
            """,
            (report_id,)
        )
        return cursor.fetchone()

    @staticmethod
    def count() -> int:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM reports WHERE is_published = 1")
        row = cursor.fetchone()
        return row['count'] if row else 0

    @staticmethod
    def create(title: str, category: str, summary: str, content: str, author_id: int, is_published: int = 1):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            INSERT INTO reports (title, category, summary, content, author_id, is_published)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, category, summary, content, author_id, is_published)
        )
        db.commit()
        return cursor.lastrowid


class AuditEvent:
    """Audit log recorder using parameterized queries."""

    @staticmethod
    def log(user_id: int | None, action: str, ip_address: str | None = None, details: str | None = None):
        try:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                """
                INSERT INTO audit_events (user_id, action, ip_address, details)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, action, ip_address, details)
            )
            db.commit()
            return cursor.lastrowid
        except Exception:
            # Audit logging failures should not crash user requests
            return None

    @staticmethod
    def get_recent(limit: int = 20):
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            """
            SELECT a.*, u.username 
            FROM audit_events a 
            LEFT JOIN users u ON a.user_id = u.id 
            ORDER BY a.timestamp DESC 
            LIMIT ?
            """,
            (limit,)
        )
        return cursor.fetchall()
