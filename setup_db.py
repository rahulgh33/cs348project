# Run this once to initialize the database and insert sample genres
from booklog_app import db, Genre, app

with app.app_context():
    db.create_all()

    genres = ["Fiction", "Non-Fiction", "Fantasy", "Sci-Fi", "Biography"]
    for name in genres:
        db.session.add(Genre(name=name))
    db.session.commit()

    print("✅ Database initialized and genres added.")
