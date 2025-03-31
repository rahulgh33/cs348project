# Flask + SQLite book log app using ORM (SQLAlchemy) and prepared statements for reports

from flask import Flask, render_template, request, redirect, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///booklog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Models
class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    pages = db.Column(db.Integer)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'))
    genre = db.relationship('Genre')
    logs = db.relationship('ReadingLog', backref='book', cascade="all, delete-orphan")

class ReadingLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'))
    log_date = db.Column(db.Date)
    pages_read = db.Column(db.Integer)
    book = db.relationship('Book')

# Routes
@app.route('/')
def index():
    books = Book.query.all()
    genres = Genre.query.all()
    return render_template('index.html', books=books, genres=genres)

@app.route('/add_book', methods=['POST'])
def add_book():
    title = request.form['title']
    author = request.form['author']
    pages = int(request.form['pages'])
    genre_id = int(request.form['genre'])
    new_book = Book(title=title, author=author, pages=pages, genre_id=genre_id)
    db.session.add(new_book)
    db.session.commit()
    return redirect('/')

@app.route('/edit_book', methods=['POST'])
def edit_book():
    book_id = int(request.form['book_id'])
    book = Book.query.get_or_404(book_id)
    book.title = request.form['title']
    book.author = request.form['author']
    book.pages = int(request.form['pages'])
    book.genre_id = int(request.form['genre'])
    db.session.commit()
    return redirect('/')

@app.route('/delete_book', methods=['POST'])
def delete_book():
    book_id = int(request.form['book_id'])
    book = Book.query.get_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
    return redirect('/')

@app.route('/add_log', methods=['POST'])
def add_log():
    book_id = int(request.form['book_id'])
    log_date = datetime.datetime.strptime(request.form['log_date'], '%Y-%m-%d').date()
    pages_read = int(request.form['pages_read'])
    new_log = ReadingLog(book_id=book_id, log_date=log_date, pages_read=pages_read)
    db.session.add(new_log)
    db.session.commit()
    return redirect('/')

@app.route('/report')
def report():
    start = request.args.get('start')
    end = request.args.get('end')
    stmt = text("""
        SELECT b.title, SUM(r.pages_read) as total_pages, COUNT(r.id) as log_count,
               ROUND(SUM(r.pages_read) * 1.0 / COUNT(DISTINCT r.log_date), 2) as avg_per_day
        FROM reading_log r
        JOIN book b ON r.book_id = b.id
        WHERE r.log_date BETWEEN :start AND :end
        GROUP BY r.book_id
    """)
    result = db.session.execute(stmt, {'start': start, 'end': end}).fetchall()
    return render_template('report.html', result=result)

@app.route('/books_by_genre')
def books_by_genre():
    genre = request.args.get('genre')
    stmt = text("""
        SELECT b.title FROM book b
        JOIN genre g ON b.genre_id = g.id
        WHERE g.name = :genre
    """)
    result = db.session.execute(stmt, {'genre': genre}).fetchall()
    return jsonify([row.title for row in result])

@app.route('/books_by_author')
def books_by_author():
    author = request.args.get('author')
    stmt = text("""
        SELECT title FROM book WHERE author = :author
    """)
    result = db.session.execute(stmt, {'author': author}).fetchall()
    return jsonify([row.title for row in result])

if __name__ == '__main__':
    app.run(debug=True)

