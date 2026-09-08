import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DB_DIR = Path("data")
DB_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DB_DIR / "chatbot.db"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():
    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            summary TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,

            FOREIGN KEY (conversation_id)
            REFERENCES conversations(id)
        )
    """)

    connection.commit()
    connection.close()


# =========================================================
# CONVERSATION
# =========================================================

def create_conversation(
    title: str = "New Conversation",
) -> int:

    now = datetime.now(timezone.utc).isoformat()

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO conversations
        (title, summary, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            title,
            "",
            now,
            now,
        ),
    )

    conversation_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return conversation_id


def get_conversation(conversation_id: int):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM conversations
        WHERE id = ?
        """,
        (conversation_id,),
    )

    conversation = cursor.fetchone()

    connection.close()

    return conversation


def update_conversation_summary(
    conversation_id: int,
    summary: str,
):
    now = datetime.now(timezone.utc).isoformat()

    connection = get_connection()

    connection.execute(
        """
        UPDATE conversations
        SET summary = ?,
            updated_at = ?
        WHERE id = ?
        """,
        (
            summary,
            now,
            conversation_id,
        ),
    )

    connection.commit()
    connection.close()


# =========================================================
# MESSAGES
# =========================================================

def add_message(
    conversation_id: int,
    role: str,
    content: str,
):
    now = datetime.now(timezone.utc).isoformat()

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO messages
        (conversation_id, role, content, created_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            conversation_id,
            role,
            content,
            now,
        ),
    )

    connection.execute(
        """
        UPDATE conversations
        SET updated_at = ?
        WHERE id = ?
        """,
        (
            now,
            conversation_id,
        ),
    )

    connection.commit()
    connection.close()


def get_messages(
    conversation_id: int,
    limit: Optional[int] = None,
):
    """
    Get messages in chronological order.

    If limit is provided, returns the latest `limit`
    messages while keeping them in ASC order.
    """

    connection = get_connection()

    cursor = connection.cursor()

    if limit is None:

        cursor.execute(
            """
            SELECT *
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,),
        )

    else:

        cursor.execute(
            """
            SELECT *
            FROM (
                SELECT *
                FROM messages
                WHERE conversation_id = ?
                ORDER BY id DESC
                LIMIT ?
            )
            ORDER BY id ASC
            """,
            (
                conversation_id,
                limit,
            ),
        )

    messages = cursor.fetchall()

    connection.close()

    return messages


# =========================================================
# RECENT MESSAGES
# =========================================================

def get_recent_messages(
    conversation_id: int,
    limit: int = 10,
):
    """
    Return recent conversation messages in the format
    expected by the chat/generation layer.

    Example:

    [
        {
            "role": "user",
            "content": "What is machine learning?"
        },
        {
            "role": "assistant",
            "content": "Machine learning is..."
        }
    ]
    """

    rows = get_messages(
        conversation_id=conversation_id,
        limit=limit,
    )

    return [
        {
            "role": row["role"],
            "content": row["content"],
        }
        for row in rows
    ]


# =========================================================
# COUNT MESSAGES
# =========================================================

def count_messages(
    conversation_id: int,
) -> int:

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM messages
        WHERE conversation_id = ?
        """,
        (conversation_id,),
    )

    count = cursor.fetchone()[0]

    connection.close()

    return count


# =========================================================
# INITIALIZE DATABASE ON IMPORT
# =========================================================

init_db()