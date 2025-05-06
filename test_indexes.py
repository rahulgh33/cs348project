# test_indexes.py
import sqlite3
from pathlib import Path

DB_FILE = Path("booklog.db")          # adjust if your file lives elsewhere
assert DB_FILE.exists(), f"{DB_FILE} not found!"

def explain(sql: str, params=()):
    """Print the single‑line query plan for a statement."""
    with sqlite3.connect(DB_FILE) as conn:
        plan = conn.execute(f"EXPLAIN QUERY PLAN {sql}", params).fetchall()
        # plan is a list of tuples; the 4th column (index 3) is the detail
        print(plan[0][3])

tests = [
    # IX_book_author
    ("SELECT title FROM book WHERE author = ?", ("JK Rowling",)),
    # IX_book_genre
    ("SELECT title FROM book WHERE genre_id = ?", (1,)),
    # IX_log_date_book  (composite)
    ("""
      SELECT SUM(pages_read) 
      FROM reading_log
      WHERE log_date BETWEEN ? AND ?
      GROUP BY book_id
     """, ("2025-05-01", "2025-05-31")),
]

for sql, params in tests:
    explain(sql, params)

