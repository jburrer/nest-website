from flask import Flask, render_template

app = Flask(__name__)

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

@app.route('/calc')
def calc():
    return render_template('calc.html')

@app.route('/statement')
def statement():
    return render_template('statement.html')

if __name__ == '__main__':
    app.run()
