# booklog_app.py — CS348 Project (Stage 3‑ready)
# --------------------------------------------------
# • Adds B‑tree indexes for every performance‑critical column
# • Wraps all data‑changing routes in explicit transactions so you can
#   discuss isolation levels in your demo
# --------------------------------------------------

from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, Index
import datetime

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///booklog.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -------------------------
# Models with explicit indexes
# -------------------------
class Genre(db.Model):
    __tablename__ = "genre"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)


class Book(db.Model):
    __tablename__ = "book"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))  # IX_book_author
    pages = db.Column(db.Integer)
    genre_id = db.Column(db.Integer, db.ForeignKey("genre.id"), index=True)  # IX_book_genre

    genre = db.relationship("Genre")
    logs = db.relationship(
        "ReadingLog",
        backref="parent_book",
        cascade="all, delete-orphan",
    )

    # Extra single‑column index on title for fast LIKE 'abc%' searches (optional)
    __table_args__ = (
        Index("ix_book_author", "author"),
        Index("ix_book_genre", "genre_id"),
    )


class ReadingLog(db.Model):
    __tablename__ = "reading_log"
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), index=True)  # IX_log_bookid
    log_date = db.Column(db.Date, index=True)
    pages_read = db.Column(db.Integer)

    book = db.relationship("Book")

    __table_args__ = (
        # Composite index used by the date‑range report
        Index("ix_log_date_book", "log_date", "book_id"),
        Index("ix_log_bookid", "book_id"),
    )


# -------------------------
# Helper: create DB + sample genres (run once)
# -------------------------

#@app.cli.command("init-db")
#def init_db():
#    db.create_all()
#    for name in ["Fiction", "Non-Fiction", "Fantasy", "Sci-Fi", "Biography"]:
#        db.session.merge(Genre(name=name))
#    db.session.commit()
#    print("✅ Database & indexes created.")
@app.cli.command("init-db")
#def init_db():
 #   """Drop all tables & indexes, then recreate and reseed."""
  #  db.drop_all()       # ← drops every table (and their indexes) if they exist
   # db.create_all()     # ← now creates tables + indexes cleanly
    ## seed genres
    #for name in ["Fiction","Non-Fiction","Fantasy","Sci-Fi","Biography"]:
    #    db.session.add(Genre(name=name))
    #db.session.commit()
    #print("✅ Database & indexes created.")
@app.cli.command("init-db")
def init_db():
    """Drop all tables & indexes, then recreate and reseed."""
    # 1) Drop everything this metadata knows about (tables → cascades indexes)
    db.drop_all()

    # 2) Recreate tables + indexes from your model definitions
    db.create_all()

    # 3) Seed the Genre table
    genres = ["Fiction", "Non-Fiction", "Fantasy", "Sci-Fi", "Biography"]
    for name in genres:
        db.session.add(Genre(name=name))
    db.session.commit()

    print("✅ Database & indexes created.")
# -------------------------
# Routes
# -------------------------
@app.route("/")
def index():
    books = Book.query.all()
    genres = Genre.query.all()
    return render_template("index.html", books=books, genres=genres)


@app.route("/add_book", methods=["POST"])
def add_book():
    with db.session.begin():  # → SERIALIZABLE by default in SQLite
        new_book = Book(
            title=request.form["title"],
            author=request.form["author"],
            pages=int(request.form["pages"]),
            genre_id=int(request.form["genre"]),
        )
        db.session.add(new_book)
    return redirect("/")


@app.route("/edit_book", methods=["POST"])
def edit_book():
    with db.session.begin():
        book = Book.query.get_or_404(int(request.form["book_id"]))
        book.title = request.form["title"]
        book.author = request.form["author"]
        book.pages = int(request.form["pages"])
        book.genre_id = int(request.form["genre"])
    return redirect("/")


@app.route("/delete_book", methods=["POST"])
def delete_book():
    with db.session.begin():
        book = Book.query.get_or_404(int(request.form["book_id"]))
        db.session.delete(book)
    return redirect("/")


@app.route("/add_log", methods=["POST"])
def add_log():
    with db.session.begin():
        new_log = ReadingLog(
            book_id=int(request.form["book_id"]),
            log_date=datetime.datetime.strptime(request.form["log_date"], "%Y-%m-%d").date(),
            pages_read=int(request.form["pages_read"]),
        )
        db.session.add(new_log)
    return redirect("/")


@app.route("/report")
def report():
    start = request.args.get("start")
    end = request.args.get("end")
    stmt = text(
        """
        SELECT b.title,
               SUM(r.pages_read)                        AS total_pages,
               COUNT(r.id)                              AS log_count,
               ROUND(SUM(r.pages_read) * 1.0 / COUNT(DISTINCT r.log_date), 2) AS avg_per_day
        FROM reading_log r
        JOIN book b ON r.book_id = b.id
        WHERE r.log_date BETWEEN :start AND :end
        GROUP BY r.book_id
        """
    )
    result = db.session.execute(stmt, {"start": start, "end": end}).fetchall()
    return render_template("report.html", result=result)


@app.route("/books_by_genre")
def books_by_genre():
    genre = request.args.get("genre")
    stmt = text(
        """
        SELECT b.title
        FROM book b
        JOIN genre g ON b.genre_id = g.id
        WHERE g.name = :genre
        """
    )
    rows = db.session.execute(stmt, {"genre": genre}).fetchall()
    return jsonify([r.title for r in rows])


@app.route("/books_by_author")
def books_by_author():
    author = request.args.get("author")
    stmt = text("SELECT title FROM book WHERE author = :author")
    rows = db.session.execute(stmt, {"author": author}).fetchall()
    return jsonify([r.title for r in rows])


if __name__ == "__main__":
    app.run(debug=True)

