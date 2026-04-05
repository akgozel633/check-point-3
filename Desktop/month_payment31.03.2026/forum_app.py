import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Определяем путь к файлу базы рядом с этим скриптом
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(BASE_DIR, 'forum.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Модель поста
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100))
    content = db.Column(db.Text)
    replies = db.relationship('Reply', backref='post', lazy=True)

# Модель ответа
class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    author = db.Column(db.String(100))
    content = db.Column(db.Text)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ База данных forum.db успешно создана в:", db_path)
