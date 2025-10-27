from flask import Flask, render_template, redirect, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dearYou.db'
app.config['SECRET_KEY'] = 'supersecretkey'
db = SQLAlchemy(app)

# ---------------------------
# DATABASE MODELS
# ---------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Letter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    hearts = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"Letter {self.id}"

with app.app_context():
    db.create_all()

# ---------------------------
# ROUTES
# ---------------------------
@app.route('/', methods=['GET', 'POST'])
def index():
    # message handling for modal
    error = request.args.get('error')
    success = request.args.get('success')
    show_modal = request.args.get('show_modal', 'false')

    if request.method == 'POST' and 'recipient' in request.form:
        recipient = request.form['recipient']
        message = request.form['message']
        new_letter = Letter(recipient=recipient, message=message)
        db.session.add(new_letter)
        db.session.commit()
        return redirect('/')

    search = request.args.get('search', '').strip().lower()
    if search:
        letters = Letter.query.filter(Letter.recipient.ilike(f'%{search}%')).order_by(Letter.created.desc()).all()
    else:
        letters = Letter.query.order_by(Letter.created.desc()).all()

    return render_template(
        'index.html',
        letters=letters,
        search=search,
        error=error,
        success=success,
        show_modal=show_modal
    )

# ❤️ React route
@app.route('/react/<int:id>', methods=['POST'])
def react(id):
    letter = Letter.query.get_or_404(id)
    letter.hearts += 1
    db.session.commit()
    return redirect('/')

# ---------------------------
# AUTHENTICATION
# ---------------------------
@app.route('/signup', methods=['POST'])
def signup():
    email = request.form['email'].strip().lower()
    password = request.form['password']

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return redirect(url_for('index', error='Email already exists. Please log in.', show_modal='true'))

    hashed_pw = generate_password_hash(password)
    new_user = User(email=email, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('index', success='Account created! Please log in.', show_modal='true'))

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email'].strip().lower()
    password = request.form['password']

    user = User.query.filter_by(email=email).first()

    # If no user or wrong password, show error without closing modal
    if not user or not check_password_hash(user.password, password):
        return redirect(url_for('index', error='Account does not exist or wrong password.', show_modal='true'))

    # Login successful
    session['user_id'] = user.id
    session['email'] = user.email
    return redirect(url_for('logged'))  # 👈 redirect to logged.html route


@app.route('/logged')
def logged():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    search = request.args.get('search', '').strip().lower()
    if search:
        letters = Letter.query.filter(Letter.recipient.ilike(f'%{search}%')).order_by(Letter.created.desc()).all()
    else:
        letters = Letter.query.order_by(Letter.created.desc()).all()

    return render_template('logged.html', email=session['email'], letters=letters, search=search)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)
