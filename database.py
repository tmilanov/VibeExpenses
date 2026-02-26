"""SQLite database layer for Vibe Expenses."""
import sys
import sqlite3
from pathlib import Path

# When frozen by PyInstaller (--onefile), __file__ is inside a temp extraction
# dir.  Use sys.executable so the database always lives next to the .exe / .py.
if getattr(sys, "frozen", False):
    _BASE = Path(sys.executable).parent
else:
    _BASE = Path(__file__).parent

DB_PATH = _BASE / "expenses.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                date        TEXT    NOT NULL,
                description TEXT    NOT NULL,
                amount      REAL    NOT NULL CHECK(amount > 0),
                type        TEXT    NOT NULL CHECK(type IN ('income','expense')),
                tags        TEXT    NOT NULL DEFAULT '',
                notes       TEXT    NOT NULL DEFAULT '',
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


# ── CRUD ──────────────────────────────────────────────────────────────────────

def add_transaction(date: str, description: str, amount: float,
                    type_: str, tags: str = "", notes: str = "") -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO transactions (date,description,amount,type,tags,notes) VALUES (?,?,?,?,?,?)",
            (date, description, amount, type_, tags.strip(), notes.strip()),
        )
        conn.commit()
        return cur.lastrowid


def update_transaction(id_: int, date: str, description: str, amount: float,
                        type_: str, tags: str = "", notes: str = "") -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE transactions SET date=?,description=?,amount=?,type=?,tags=?,notes=? WHERE id=?",
            (date, description, amount, type_, tags.strip(), notes.strip(), id_),
        )
        conn.commit()


def delete_transaction(id_: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM transactions WHERE id=?", (id_,))
        conn.commit()


# ── Queries ───────────────────────────────────────────────────────────────────

def get_transactions(search: str = "", type_filter: str = "", tag_filter: str = "") -> list[dict]:
    q = "SELECT * FROM transactions WHERE 1=1"
    p: list = []
    if search:
        q += " AND (description LIKE ? OR tags LIKE ? OR notes LIKE ?)"
        p += [f"%{search}%"] * 3
    if type_filter:
        q += " AND type=?"
        p.append(type_filter)
    if tag_filter:
        q += " AND tags LIKE ?"
        p.append(f"%{tag_filter}%")
    q += " ORDER BY date DESC, created_at DESC"
    with _connect() as conn:
        return [dict(r) for r in conn.execute(q, p).fetchall()]


def get_recent_transactions(limit: int = 8) -> list[dict]:
    with _connect() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM transactions ORDER BY date DESC, created_at DESC LIMIT ?", (limit,)
        ).fetchall()]


def get_total_balance() -> float:
    with _connect() as conn:
        r = conn.execute(
            "SELECT COALESCE(SUM(CASE WHEN type='income' THEN amount ELSE -amount END),0) FROM transactions"
        ).fetchone()
        return r[0]


def get_monthly_summary(year: int, month: int) -> dict:
    with _connect() as conn:
        r = conn.execute("""
            SELECT
                COALESCE(SUM(CASE WHEN type='income'  THEN amount ELSE 0 END),0) AS income,
                COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END),0) AS expenses
            FROM transactions
            WHERE strftime('%Y-%m', date) = ?
        """, (f"{year}-{month:02d}",)).fetchone()
        return {"income": r[0], "expenses": r[1]}


def get_grouped_totals(date_from: str = None, date_to: str = None,
                        group_by: str = "month") -> list[dict]:
    """
    Returns [{period, income, expenses}, ...] in chronological order.
    group_by: 'month' (YYYY-MM) or 'day' (YYYY-MM-DD).
    date_from / date_to: 'YYYY-MM-DD' strings, or None for all time.
    """
    fmt = "%Y-%m-%d" if group_by == "day" else "%Y-%m"
    q = f"""
        SELECT
            strftime('{fmt}', date)                                           AS period,
            COALESCE(SUM(CASE WHEN type='income'  THEN amount ELSE 0 END),0) AS income,
            COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END),0) AS expenses
        FROM transactions
        WHERE 1=1
    """
    p: list = []
    if date_from:
        q += " AND date >= ?"
        p.append(date_from)
    if date_to:
        q += " AND date <= ?"
        p.append(date_to)
    q += " GROUP BY 1 ORDER BY 1"
    with _connect() as conn:
        return [dict(r) for r in conn.execute(q, p).fetchall()]


# Keep old name as alias so nothing else breaks
def get_monthly_totals(n_months: int = 12) -> list[dict]:
    return get_grouped_totals()[-n_months:]


def get_spending_by_tag(date_from: str = None, date_to: str = None) -> list[tuple]:
    """Returns [(tag, total), ...] sorted by total desc. Splits amounts across multiple tags."""
    q = "SELECT tags, amount FROM transactions WHERE type='expense' AND tags != ''"
    p: list = []
    if date_from:
        q += " AND date >= ?"
        p.append(date_from)
    if date_to:
        q += " AND date <= ?"
        p.append(date_to)
    with _connect() as conn:
        rows = conn.execute(q, p).fetchall()
    totals: dict[str, float] = {}
    for row in rows:
        raw_tags = [t.strip() for t in row["tags"].split(",") if t.strip()]
        if not raw_tags:
            continue
        share = row["amount"] / len(raw_tags)
        for tag in raw_tags:
            totals[tag] = totals.get(tag, 0.0) + share
    return sorted(totals.items(), key=lambda x: x[1], reverse=True)


def get_balance_over_time(date_from: str = None, date_to: str = None) -> list[dict]:
    """Running cumulative balance. When a date range is given, returns the
    actual balance values (all-time cumulative) but only for transactions
    within [date_from, date_to]."""
    if date_from or date_to:
        q = """
            WITH running AS (
                SELECT date, created_at,
                       SUM(CASE WHEN type='income' THEN amount ELSE -amount END)
                           OVER (ORDER BY date, created_at ROWS UNBOUNDED PRECEDING) AS balance
                FROM transactions
            )
            SELECT date, balance FROM running WHERE 1=1
        """
        p: list = []
        if date_from:
            q += " AND date >= ?"
            p.append(date_from)
        if date_to:
            q += " AND date <= ?"
            p.append(date_to)
        q += " ORDER BY date, created_at"
        with _connect() as conn:
            return [dict(r) for r in conn.execute(q, p).fetchall()]
    with _connect() as conn:
        return [dict(r) for r in conn.execute("""
            SELECT date,
                   SUM(CASE WHEN type='income' THEN amount ELSE -amount END)
                       OVER (ORDER BY date, created_at ROWS UNBOUNDED PRECEDING) AS balance
            FROM transactions ORDER BY date, created_at
        """).fetchall()]


def get_period_summary(date_from: str = None, date_to: str = None) -> dict:
    """Income + expenses for any date range (None = all time)."""
    q = """
        SELECT
            COALESCE(SUM(CASE WHEN type='income'  THEN amount ELSE 0 END),0) AS income,
            COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END),0) AS expenses
        FROM transactions WHERE 1=1
    """
    p: list = []
    if date_from:
        q += " AND date >= ?"
        p.append(date_from)
    if date_to:
        q += " AND date <= ?"
        p.append(date_to)
    with _connect() as conn:
        r = conn.execute(q, p).fetchone()
        return {"income": r[0], "expenses": r[1]}


def get_all_tags() -> list[str]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT tags FROM transactions WHERE tags != ''"
        ).fetchall()
    tags: set[str] = set()
    for row in rows:
        for t in row[0].split(","):
            t = t.strip()
            if t:
                tags.add(t)
    return sorted(tags)
