from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///solar.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class DesignData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    power_output = db.Column(db.Float, nullable=False)

def create_tables():
    with app.app_context():
        db.create_all()

@app.route('/')
def index():
    data = DesignData.query.all()
    return render_template('index.html', data=data)

@app.route('/add', methods=['POST'])
def add_data():
    panel_id = request.form['panel_id']
    location = request.form['location']
    power_output = request.form['power_output']
    new_data = DesignData(panel_id=panel_id, location=location, power_output=power_output)
    db.session.add(new_data)
    db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    create_tables()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
