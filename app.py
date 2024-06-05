from flask import Flask, request, render_template, redirect, url_for, session
import sqlite3
import pickle
import numpy as np
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'supersecretkey'
model = pickle.load(open('model.pkl', 'rb'))

def init_sqlite_db():
    conn = sqlite3.connect('users.db')
    print("Opened database successfully")

    conn.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT)')
    print("Table created successfully")
    conn.close()

init_sqlite_db()

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        con = sqlite3.connect('users.db')
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cur.fetchone()
        con.close()

        if user and check_password_hash(user[1], password):
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return "Login Failed. Check your username and password."
    return render_template("login.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')

        con = sqlite3.connect('users.db')
        cur = con.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        con.commit()
        con.close()

        return redirect(url_for('login'))
    return render_template("signup.html")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        gender = request.form['gender']
        married = request.form['married']
        dependents = request.form['dependents']
        education = request.form['education']
        employed = request.form['employed']
        credit = float(request.form['credit'])
        area = request.form['area']
        ApplicantIncome = float(request.form['ApplicantIncome'])
        CoapplicantIncome = float(request.form['CoapplicantIncome'])
        LoanAmount = float(request.form['LoanAmount'])
        Loan_Amount_Term = float(request.form['Loan_Amount_Term'])

        # gender
        male = 1 if gender == "Male" else 0

        # married
        married_yes = 1 if married == "Yes" else 0

        # dependents
        dependents_1 = dependents_2 = dependents_3 = 0
        if dependents == '1':
            dependents_1 = 1
        elif dependents == '2':
            dependents_2 = 1
        elif dependents == '3+':
            dependents_3 = 1

        # education
        not_graduate = 1 if education == "Not Graduate" else 0

        # employed
        employed_yes = 1 if employed == "Yes" else 0

        # property area
        semiurban = urban = 0
        if area == "Semiurban":
            semiurban = 1
        elif area == "Urban":
            urban = 1

        ApplicantIncomelog = np.log(ApplicantIncome)
        totalincomelog = np.log(ApplicantIncome + CoapplicantIncome)
        LoanAmountlog = np.log(LoanAmount)
        Loan_Amount_Termlog = np.log(Loan_Amount_Term)

        prediction = model.predict([[credit, ApplicantIncomelog, LoanAmountlog, Loan_Amount_Termlog, totalincomelog, male, married_yes, dependents_1, dependents_2, dependents_3, not_graduate, employed_yes, semiurban, urban]])

        prediction_text = "Approved" if prediction == "Y" else "Not Approved"

        return render_template("predict.html", prediction_text="Loan is {}".format(prediction_text))
    return render_template("predict.html")

@app.route('/emi_calculator')
def emi_calculator():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template("EMI_Calculator.html")

if __name__ == "__main__":
    app.run(debug=True)
