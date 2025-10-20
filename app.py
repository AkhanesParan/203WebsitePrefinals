from flask import Flask, render_template, redirect, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dearYou.db'
db = SQLAlchemy(app)

# Database model
class Letter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipient = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    hearts = db.Column(db.Integer, default=0)  #  new column

    def __repr__(self):
        return f"Letter {self.id}"

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
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
    return render_template('index.html', letters=letters, search=search)

# ❤️ Heart react route (no JavaScript)
@app.route('/react/<int:id>', methods=['POST'])
def react(id):
    letter = Letter.query.get_or_404(id)
    letter.hearts += 1
    db.session.commit()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
