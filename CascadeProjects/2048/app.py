from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
db = SQLAlchemy(app)

# データベースモデル
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    destination = db.Column(db.String(200), nullable=False)
    purpose = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ルート設定
@app.route('/')
def index():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    return render_template('index.html', expenses=expenses)

@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        expense = Expense(
            user_name=request.form['user_name'],
            date=datetime.strptime(request.form['date'], '%Y-%m-%d'),
            destination=request.form['destination'],
            purpose=request.form['purpose'],
            amount=int(request.form['amount'])
        )
        db.session.add(expense)
        db.session.commit()
        flash('経費が登録されました')
        return redirect(url_for('index'))
    return render_template('add.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
