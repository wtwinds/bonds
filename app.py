from flask import Flask, render_template, request, redirect, session, flash
from pymongo import MongoClient
from datetime import datetime
import requests
import config
import time

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# MongoDB
client = MongoClient(config.MONGO_URI)
db = client["bondshub"]

users = db["users"]
bonds_col = db["bonds"]
investments = db["investments"]


# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("email")
        password = request.form.get("password")

        user = users.find_one({"name": name, "password": password})
        if user:
            session["user"] = name
            return redirect("/bonds")

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
        invest = float(b["Min Invest"].replace("₹", "").replace(",", ""))
        roi = float(b["ROI"].replace("%", ""))

        total_investment += invest
        total_roi += roi
        total_returns += invest * (roi / 100)

    active_bonds = len(data)
    avg_roi = round(total_roi / active_bonds, 2)

    return render_template(
        "bonds.html",
        bonds=data,
        total_investment=int(total_investment),
        active_bonds=active_bonds,
        avg_roi=avg_roi,
        total_returns=int(total_returns),
    )

# ---------------- BUY BOND ----------------
@app.route("/buy/<company>")
def buy_bond(company):
    if "user" not in session:
        return redirect("/")

    user = session["user"]
    bond = bonds_col.find_one({"Category": company})

    if not bond:
        flash("Bond not found", "danger")
        return redirect("/bonds")

    amount = float(bond["Min Invest"].replace("₹", "").replace(",", ""))
    roi = float(bond["ROI"].replace("%", ""))

    # BANK CALL (MULTI-MERCHANT)
    try:
        res = requests.post(
            "https://bank-stock-web.onrender.com/bank/api/pay",
            json={
                "username": user,
                "amount": amount,
                "merchant": "Bonds"
            },
            timeout=40,
        ).json()
    except:
        time.sleep(5)  # retry once (Render wakeup)
        try:
            res = requests.post(
                "https://bank-stock-web.onrender.com/bank/api/pay",
                json={
                    "username": user,
                    "amount": amount,
                    "merchant": "Bonds"
                },
                timeout=40,
            ).json()
        except:
            flash("Bank server waking up, try again", "danger")
            return redirect("/bonds")

    if res.get("status") != "success":
        flash(res.get("msg", "Payment failed"), "danger")
        return redirect("/bonds")

    # ✅ SAVE FULL SNAPSHOT (FIXED)
    investments.insert_one({
        "user": user,
        "bond": company,
        "amount": amount,
        "roi": roi,

        # SNAPSHOT DATA
        "Rating": bond.get("Rating"),
        "Tenure": bond.get("Tenure"),
        "Risk": bond.get("Risk"),

        "created_at": datetime.utcnow()
    })

    flash("Bond Purchased Successfully 🎉", "success")
    return redirect("/portfolio")

# ---------------- PORTFOLIO ----------------
@app.route("/portfolio")
def portfolio():
    if "user" not in session:
        return redirect("/")

    user = session["user"]
    data = list(investments.find({"user": user}, {"_id": 0}))

    total_investment = 0
    total_roi = 0
    total_returns = 0
    rating_counts = {}

    for b in data:
        invest = b["amount"]
        roi = b["roi"]

        total_investment += invest
        total_roi += roi
        total_returns += invest * (roi / 100)

        rating_counts["BONDS"] = rating_counts.get("BONDS", 0) + 1

    total_bonds = len(data) or 1
    avg_roi = round(total_roi / total_bonds, 2) if total_bonds else 0

    return render_template(
        "portfolio.html",
        bonds=data,
        total_investment=int(total_investment),
        avg_roi=avg_roi,
        total_returns=int(total_returns),
        pie=rating_counts
    )


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)