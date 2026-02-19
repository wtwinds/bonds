from flask import Flask, render_template, request, redirect, session
from pymongo import MongoClient
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# MongoDB
client = MongoClient(config.MONGO_URI)
db = client["bondshub"]

users = db["users"]
bonds_col = db["bonds"]   # NEW collection

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("email")   # full name input
        password = request.form.get("password")

        user = users.find_one({
            "name": name,
            "password": password
        })

        if user:
            session["user"] = name
            return redirect("/bonds")
        else:
            return render_template("login.html", error="Invalid login")

    return render_template("login.html")

# ---------------- BONDS PAGE ----------------
@app.route("/bonds")
def bonds():
    if "user" not in session:
        return redirect("/")

    data = list(bonds_col.find({}, {"_id": 0}))

    total_investment = 0
    total_roi = 0
    total_returns = 0

    for b in data:
        # Clean Min Invest
        invest = b.get("Min Invest", "0")
        invest = invest.replace("₹", "").replace(",", "").strip()
        invest = float(invest)

        # Clean ROI
        roi = b.get("ROI", "0").replace("%", "").strip()
        roi = float(roi)

        total_investment += invest
        total_roi += roi

        # Calculate returns
        total_returns += invest * (roi / 100)

    active_bonds = len(data)
    avg_roi = round(total_roi / active_bonds, 2)
    total_returns = round(total_returns, 2)

    return render_template(
        "bonds.html",
        bonds=data,
        total_investment=int(total_investment),
        active_bonds=active_bonds,
        avg_roi=avg_roi,
        total_returns=int(total_returns)
    )

# ---------------- PORTFOLIO ----------------
@app.route("/portfolio")
def portfolio():
    if "user" not in session:
        return redirect("/")

    data = list(bonds_col.find({}, {"_id": 0}))

    total_investment=0
    total_roi=0
    total_returns=0

    rating_counts={}

    for b in data:
        invest=b.get("Min Invest", "0")
        invest=invest.replace("₹", "").replace(",", "").strip()
        invest=float(invest)

        roi=b.get("ROI", "0").replace("%","").strip()
        roi=float(roi)

        total_investment+=invest
        total_roi+=roi
        total_returns+=invest*(roi/100)

        rating=b.get("Rating")
        rating_counts[rating]=rating_counts.get(rating,0)+1

    total_bonds=len(data)
    avg_roi=round(total_roi/total_bonds,2)
    total_returns=round(total_returns,2)
    return render_template(
        "portfolio.html", 
        bonds=data,  
        total_investment=int(total_investment),
        avg_roi=avg_roi,
        total_returns=int(total_returns),
        pie=rating_counts)

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
