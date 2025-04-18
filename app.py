from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import inspect

import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
database_url = os.environ.get('DATABASE_URL', 'sqlite:///todo.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    todos = db.relationship('Todo', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    complete = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.DateTime)
    category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    todos = Todo.query.filter_by(user_id=current_user.id).order_by(Todo.created_at.desc()).all()
    return render_template('dashboard.html', todos=todos)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.check_password(request.form.get('password')):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        user = User(username=username)
        user.set_password(request.form.get('password'))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/add_todo', methods=['POST'])
@login_required
def add_todo():
    title = request.form.get('title')
    description = request.form.get('description')
    category = request.form.get('category')
    due_date_str = request.form.get('due_date')
    due_date = datetime.strptime(due_date_str, '%Y-%m-%d') if due_date_str else None
    
    todo = Todo(
        title=title,
        description=description,
        category=category,
        due_date=due_date,
        user_id=current_user.id
    )
    db.session.add(todo)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/toggle_todo/<int:id>')
@login_required
def toggle_todo(id):
    todo = Todo.query.get_or_404(id)
    if todo.user_id != current_user.id:
        return redirect(url_for('dashboard'))
    todo.complete = not todo.complete
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/delete_todo/<int:id>')
@login_required
def delete_todo(id):
    todo = Todo.query.get_or_404(id)
    if todo.user_id != current_user.id:
        return redirect(url_for('dashboard'))
    db.session.delete(todo)
    db.session.commit()
    return redirect(url_for('dashboard'))

with app.app_context():
    if not inspect(db.engine).has_table('user'):
        db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)