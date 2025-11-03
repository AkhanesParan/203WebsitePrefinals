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
    created = db.Column(db.DateTime, default=datetime.utcnow)
    hearts = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Reaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    letter_id = db.Column(db.Integer, db.ForeignKey('letter.id'))

with app.app_context():
    db.create_all()

# ---------------------------
# ROUTES
# ---------------------------

@app.route('/', methods=['GET'])
def index():
    search = request.args.get('search', '').strip().lower()
    if search:
        letters = Letter.query.filter(Letter.recipient.ilike(f'%{search}%')).order_by(Letter.created.desc()).all()
    else:
        letters = Letter.query.order_by(Letter.created.desc()).all()
    return render_template('index.html', letters=letters, search=search)

@app.route('/logged', methods=['GET', 'POST'])
def logged():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    # Posting a new letter
    if request.method == 'POST':
        recipient = request.form['recipient']
        message = request.form['message']
        new_letter = Letter(recipient=recipient, message=message, user_id=session['user_id'])
        db.session.add(new_letter)
        db.session.commit()
        return redirect(url_for('logged'))

    search = request.args.get('search', '').strip().lower()
    if search:
        letters = Letter.query.filter(Letter.recipient.ilike(f'%{search}%')).order_by(Letter.created.desc()).all()
    else:
        letters = Letter.query.order_by(Letter.created.desc()).all()

    # Get all reactions by this user
    user_reactions = {r.letter_id for r in Reaction.query.filter_by(user_id=session['user_id']).all()}

    return render_template(
        'logged.html',
        letters=letters,
        search=search,
        email=session['email'],
        user_reactions=user_reactions
    )

# ---------------------------
# AUTHENTICATION
# ---------------------------
@app.route('/login', methods=['POST'])
def login():
    email = request.form['email'].strip().lower()
    password = request.form['password']
    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password, password):
        # Fetch letters so the background still renders
        letters = Letter.query.order_by(Letter.created.desc()).all()
        return render_template(
            'index.html',
            letters=letters,
            search='',
            error='Account does not exist or wrong password.',
            show_modal=True,
            form_mode='login',
            form_action='/login',
            submit_text='Continue'
        )

    session['user_id'] = user.id
    session['email'] = user.email
    return redirect(url_for('logged'))

@app.route('/signup', methods=['POST'])
def signup():
    email = request.form['email'].strip().lower()
    password = request.form['password']

    if User.query.filter_by(email=email).first():
        letters = Letter.query.order_by(Letter.created.desc()).all()
        return render_template(
            'index.html',
            letters=letters,
            search='',
            error='Email already exists.',
            show_modal=True,
            form_mode='signup',
            form_action='/signup',
            submit_text='Create Account'
        )

    hashed_pw = generate_password_hash(password)
    new_user = User(email=email, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('index', success='Account created! Please log in.'))

# ---------------------------
# LOGOUT
# ---------------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ---------------------------
# HEART REACTIONS
# ---------------------------
@app.route('/react/<int:letter_id>', methods=['POST'])
def react(letter_id):
    if 'user_id' not in session:
        return redirect(url_for('index', error='Please log in to react.'))

    user_id = session['user_id']
    # Check if this user already reacted
    existing = Reaction.query.filter_by(user_id=user_id, letter_id=letter_id).first()
    if existing:
        return redirect(url_for('logged'))

    new_reaction = Reaction(user_id=user_id, letter_id=letter_id)
    db.session.add(new_reaction)

    letter = Letter.query.get_or_404(letter_id)
    letter.hearts += 1

    db.session.commit()
    return redirect(url_for('logged'))

@app.route('/reactarchive/<int:letter_id>', methods=['POST'])
def react_archive(letter_id):
    if 'user_id' not in session:
        return redirect(url_for('index', error='Please log in to react.'))

    user_id = session['user_id']
    # Check if this user already reacted
    existing = Reaction.query.filter_by(user_id=user_id, letter_id=letter_id).first()
    if existing:
        return redirect(url_for('archive'))

    new_reaction = Reaction(user_id=user_id, letter_id=letter_id)
    db.session.add(new_reaction)

    letter = Letter.query.get_or_404(letter_id)
    letter.hearts += 1

    db.session.commit()
    return redirect(url_for('archive'))
# ---------------------------
# VIEW LETTER 
# ---------------------------
@app.route('/letter/<int:letter_id>')
def display_letter(letter_id):
    letter = Letter.query.get_or_404(letter_id)
    return render_template('display.html', letter=letter)

@app.route('/letterout/<int:letter_id>')
def display_letter_out(letter_id):
    letter = Letter.query.get_or_404(letter_id)
    return render_template('displayout.html', letter=letter)

@app.route('/letterarchive/<int:letter_id>')
def display_letter_archive(letter_id):
    letter = Letter.query.get_or_404(letter_id)
    return render_template('display_archive.html', letter=letter)

@app.route('/letteroutarcive/<int:letter_id>')
def display_letter_out_archive(letter_id):
    letter = Letter.query.get_or_404(letter_id)
    return render_template('displayout_archive.html', letter=letter)

@app.route('/letterprofile/<int:letter_id>')
def display_letter_profile(letter_id):
    letter = Letter.query.get_or_404(letter_id)
    return render_template('display_profile.html', letter=letter)
# ---------------------------
# GO TO ARCHIVE 
# ---------------------------

@app.route('/archive')
def archive():
    letters = Letter.query.order_by(Letter.created.desc()).all()
    search = request.args.get('search', '').strip().lower()
    user_reactions = {r.letter_id for r in Reaction.query.filter_by(user_id=session['user_id']).all()}
    return render_template('archive.html', letters=letters, search=search, user_reactions=user_reactions)

@app.route('/archiveout')
def archive_out():
    letters = Letter.query.order_by(Letter.created.desc()).all()
    search = request.args.get('search', '').strip().lower()
    return render_template('archiveout.html', letters=letters, search=search)

# ---------------------------
# PROFILE
# ---------------------------

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('index'))

    user_id = session['user_id']

    # Letters the user posted
    posted_letters = Letter.query.filter_by(user_id=user_id).order_by(Letter.created.desc()).all()

    # Letters the user liked
    liked_letter_ids = [r.letter_id for r in Reaction.query.filter_by(user_id=user_id).all()]
    liked_letters = Letter.query.filter(Letter.id.in_(liked_letter_ids)).order_by(Letter.created.desc()).all()

    return render_template('profile.html',
                           posted_letters=posted_letters,
                           liked_letters=liked_letters,
                           email=session['email'])

@app.route('/edit/<int:letter_id>', methods=['GET', 'POST'])
def edit_letter(letter_id):
    letter = Letter.query.get_or_404(letter_id)
    if request.method == 'POST':
        letter.recipient = request.form['recipient']
        letter.message = request.form['message']
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('edit_letter.html', letter=letter)

@app.route('/delete/<int:letter_id>')
def delete_letter(letter_id):
    letter = Letter.query.get_or_404(letter_id)
    db.session.delete(letter)
    db.session.commit()
    return redirect(url_for('profile'))

# ---------------------------
# ABOUT
# ---------------------------
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/aboutout')
def about_out():
    return render_template('aboutout.html')

if __name__ == '__main__':
    app.run(debug=True)
