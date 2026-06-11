import json, os, datetime
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from sqlalchemy.sql import func

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir,
                                                                    'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Income(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    cash = db.Column(db.Integer)
    venmo = db.Column(db.Integer)
    date = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.Boolean)

    def __repr__(self):
        return f'<Income id={self.id} cash={self.cash} venmo={self.venmo} date={self.date} status={self.status}>'

    def serialize(self):
        return {
            'cash': self.cash,
            'venmo': self.venmo,
            'date': self.date,
        }

class Payout(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    venmo = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    payout = db.Column(db.Integer)
    date = db.Column(db.DateTime(timezone=True))
    status = db.Column(db.Boolean)

    def __repr__(self):
        return f'<Payout id={self.id} name={self.name} venmo={self.venmo} role={self.role} payout={self.payout} date={self.date} status={self.status}>'

    def serialize(self):
        return {
            'name': self.name,
            'venmo': self.venmo,
            'role': self.role,
            'payout': self.payout,
            'date': self.date,
        }

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/donate')
def donate():
    return render_template('donate.html')

@app.route('/merch')
def merch():
    return render_template('merch.html')

@app.route('/guidelines')
def guidelines():
    return render_template('guidelines.html')

@app.route('/finances')
def finances():
    return render_template('finances.html')

@app.route('/finances_get')
def finances_get():

    shows = []

    saved_income_records = Income.query.filter_by(status=False).order_by(desc(Income.date)).all()
    for income_record in saved_income_records:

        performers = []
        performer_payout_records = Payout.query.filter_by(status=False,
                                                          date=income_record.date,
                                                          role='performer').all()
        for performer_record in performer_payout_records:
            performers.append({
                'name': performer_record.name,
                'payout': performer_record.payout
            })
            
        staff_payout_records = Payout.query.filter_by(status=False,
                                                      date=income_record.date,
                                                      role='staff').all()

        nest_payout_record = Payout.query.filter_by(status=False,
                                                    date=income_record.date,
                                                    role='nest').first()

        shows.append({
            'date': income_record.date,
            'income': income_record.cash + income_record.venmo,
            'performers': performers,
            'numStaff': len(staff_payout_records),
            'staffPayout': staff_payout_records[0].payout,
            'nestCut': nest_payout_record.payout
        })

    return shows

@app.route('/statement')
def statement():
    return render_template('statement.html')

@app.route('/payout')
def payout():
    return render_template('payout.html')

@app.route('/payout_get')
def payout_get():

    date = None
    cash = 0
    venmo = 0
    saved_income_record = Income.query.filter_by(status=True).first()
    if saved_income_record is not None:
        date = saved_income_record.date
        cash = saved_income_record.cash
        venmo = saved_income_record.venmo

    saved_performer_records = Payout.query.filter_by(status=True,
                                                     role='performer').all()

    saved_staff_records = Payout.query.filter_by(status=True,
                                                 role='staff').all()

    nest_payout = 0
    saved_nest_record = Payout.query.filter_by(status=True,
                                               role='nest').first()
    if saved_nest_record is not None:
        nest_payout = saved_nest_record.payout

    return {
        'date': date,
        'cash': cash,
        'venmo': venmo,
        'performers': [i.serialize() for i in saved_performer_records],
        'staff': [i.serialize() for i in saved_staff_records],
        'nestCut': nest_payout
    }


@app.route('/payout_save', methods=['POST'])
def payout_save():

    if request.method == 'POST':

        # get date for new records
        date_time = datetime.datetime.strptime(request.form['date'], '%Y-%m-%d')

        # check if record has already been published for that date
        existing_dates = Income.query.with_entities(Income.date).filter_by(status=False).all()
        for date in existing_dates:
            if date[0] == date_time:
                return "Error: A show for this date has already been published." 

        # delete previously saved records to replace with new ones
        saved_income_record = Income.query.filter_by(status=True).first()
        if saved_income_record is not None:
            db.session.delete(saved_income_record)
        saved_payout_records = Payout.query.filter_by(status=True).all()
        for record in saved_payout_records:
            db.session.delete(record)
        db.session.commit()

        # create new income record
        income_record = Income(cash=int(request.form['cashIncome']),
                               venmo=int(request.form['venmoIncome']),
                               date=date_time,
                               status=True)
        db.session.add(income_record)
        print(income_record)

        # create new records for performer payouts
        performers = json.loads(request.form['performers'])
        for performer in performers:
            performer_record = Payout(name=performer['name'],
                                      venmo=performer['venmo'],
                                      role='performer',
                                      payout=performer['payout'],
                                      date=date_time,
                                      status=True)
            db.session.add(performer_record)

        # create new records for staff payouts
        staff = json.loads(request.form['staff'])
        for staffer in staff:
            staff_record = Payout(name=staffer['name'],
                                  venmo=staffer['venmo'],
                                  role='staff',
                                  payout=staffer['payout'],
                                  date=date_time,
                                  status=True)
            db.session.add(staff_record)

        # create new record for nest payout
        nest_record = Payout(name='Nest',
                             venmo='N/A',
                             role='nest',
                             payout=int(request.form['nestCut']),
                             date=date_time,
                             status=True)
        db.session.add(nest_record)

        # commit new records to db
        db.session.commit()

        return "success" 

    return "Error: Save failed (check logs)." 

@app.route('/payout_publish', methods=['GET'])
def payout_publish():

    if request.method == 'GET':

        saved_income_record = Income.query.filter_by(status=True).first()
        saved_income_record.status = False
        db.session.add(saved_income_record)

        saved_payout_records = Payout.query.filter_by(status=True).all()
        for record in saved_payout_records:
            record.status=False
            db.session.add(record)

        db.session.commit()

        return "success" 

    return "Error: Publish failed (check logs)." 

if __name__ == '__main__':
    app.run()
