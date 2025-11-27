from flask import Flask, render_template, request, jsonify
import mysql.connector
import random
from datetime import datetime
import os

app = Flask(__name__)

# ---------- DB CONNECTION ----------

def get_db():
    conn = mysql.connector.connect(
        host=os.environ["MYSQLHOST"],          # shuttle.proxy.rlwy.net
        user=os.environ["MYSQLUSER"],          # root
        password=os.environ["MYSQLPASSWORD"],  # your password
        database=os.environ["MYSQLDATABASE"],  # railway
        port=int(os.environ["MYSQLPORT"])      # 28420
    )
    return conn

# ---------- POPUP MESSAGES ----------

positive_msgs = [
    "Great job Jei! Super da, keep going.",
    "You did well today pa. All the best for the next trade.",
    "Solid trade da! Your analysis worked perfectly.",
    "Profit is profit — good discipline bruu."
]

negative_msgs = [
    "It's okay Jei, don't feel bad pa. Loss is part of the market.",
    "Loss doesn’t define you. You’ll bounce back stronger.",
    "Take a deep breath. Tomorrow will be better.",
    "Good effort. Learn and move on — you got this."
]

neutral_msgs = [
    "Break-even is also a win. Good control."
]

# ---------- PAGES ----------
@app.route("/welcome")
def welcome_page():
    return render_template("welcome.html")

@app.route("/")
def home():
    return render_template("welcome.html")

# -----------------------------------------
# Dashboard page
# -----------------------------------------
@app.route('/charts')
def dashboard():
    return render_template('charts.html')


# -----------------------------------------
# API: Performance data for charts
# -----------------------------------------
@app.route('/api/performance-data')
def performance_data():
    conn = get_db()  # ✅ correct function name
   # now it is defined
    cursor = conn.cursor(dictionary=True)

    # DAILY P/L
    cursor.execute("""
        SELECT date, SUM(pl_amount) as daily_pl
        FROM trades
        GROUP BY date
        ORDER BY date
    """)
    rows = cursor.fetchall()

    dates = []
    daily_pl = []
    equity_curve = []

    cumulative = 0
    for row in rows:
        d = row['date']
        if isinstance(d, datetime):
            d = d.date()
        dates.append(d.strftime('%Y-%m-%d'))

        pl = float(row['daily_pl'] or 0)
        daily_pl.append(pl)

        cumulative += pl
        equity_curve.append(cumulative)

    # WIN / LOSS count
    cursor.execute("""
        SELECT 
            SUM(CASE WHEN pl_amount > 0 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN pl_amount <= 0 THEN 1 ELSE 0 END) as losses
        FROM trades
    """)
    wl = cursor.fetchone()
    wins = int(wl['wins'] or 0)
    losses = int(wl['losses'] or 0)

    # STATS
    cursor.execute("SELECT AVG(pl_amount) FROM trades WHERE pl_amount > 0")
    avg_profit = cursor.fetchone()[0] or 0

    cursor.execute("SELECT AVG(pl_amount) FROM trades WHERE pl_amount < 0")
    avg_loss = cursor.fetchone()[0] or 0

    cursor.execute("SELECT MAX(pl_amount) FROM trades")
    best_trade = cursor.fetchone()[0] or 0

    cursor.execute("SELECT MIN(pl_amount) FROM trades")
    worst_trade = cursor.fetchone()[0] or 0

    conn.close()

    return jsonify({
        "dates": dates,
        "daily_pl": daily_pl,
        "equity_curve": equity_curve,
        "wins": wins,
        "losses": losses,
        "stats": {
            "avg_profit": avg_profit,
            "avg_loss": avg_loss,
            "best_trade": best_trade,
            "worst_trade": worst_trade
        }
    })



@app.route("/add_trade_page")
def add_trade_page():
    return render_template("add_trade.html")

@app.route("/history")
def history_page():
    return render_template("history.html")

@app.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")

# ---------- API: ADD TRADE ----------

@app.route("/api/add_trade", methods=["POST"])
def api_add_trade():
    data = request.json

    symbol = data.get("symbol", "").upper()
    buy_price = float(data.get("buy_price", 0))
    sell_price = float(data.get("sell_price", 0))
    quantity = int(data.get("quantity", 0))
    trade_datetime_str = data.get("trade_datetime")
    notes = data.get("notes", "")
    reason = data.get("reason", "")
    emotion = data.get("emotion", "")
    strategy = data.get("strategy", "")

    # parse datetime (YYYY-MM-DDTHH:MM from input type="datetime-local")
    if trade_datetime_str:
        trade_datetime = datetime.strptime(trade_datetime_str, "%Y-%m-%dT%H:%M")
    else:
        trade_datetime = datetime.now()

    profit = round((sell_price - buy_price) * quantity, 2)

    # choose popup msg
    if profit > 0:
        msg = random.choice(positive_msgs)
    elif profit < 0:
        msg = random.choice(negative_msgs)
    else:
        msg = random.choice(neutral_msgs)

    conn = get_db()
    cur = conn.cursor()
    sql = """
        INSERT INTO trades
        (symbol, buy_price, sell_price, quantity, trade_datetime, notes, reason, emotion, strategy, profit)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    cur.execute(sql, (
        symbol, buy_price, sell_price, quantity,
        trade_datetime, notes, reason, emotion, strategy, profit
    ))
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": msg, "profit": float(profit)})

# ---------- API: GET TRADES (WITH FILTERS) ----------

@app.route("/api/trades", methods=["GET"])
def api_trades():
    symbol = request.args.get("symbol", "").strip().upper()
    strategy = request.args.get("strategy", "").strip()
    emotion = request.args.get("emotion", "").strip()
    outcome = request.args.get("outcome", "").strip()  # "profit", "loss", "all"
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")

    query = "SELECT id, symbol, buy_price, sell_price, quantity, trade_datetime, notes, reason, emotion, strategy, profit FROM trades WHERE 1=1"
    params = []

    if symbol:
        query += " AND symbol = %s"
        params.append(symbol)

    if strategy:
        query += " AND strategy = %s"
        params.append(strategy)

    if emotion:
        query += " AND emotion = %s"
        params.append(emotion)

    if outcome == "profit":
        query += " AND profit > 0"
    elif outcome == "loss":
        query += " AND profit < 0"

    if date_from:
        query += " AND trade_datetime >= %s"
        params.append(date_from + " 00:00:00")

    if date_to:
        query += " AND trade_datetime <= %s"
        params.append(date_to + " 23:59:59")

    query += " ORDER BY trade_datetime DESC"

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(rows)

# ---------- API: DASHBOARD STATS ----------

@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    # total profit and counts
    cur.execute("SELECT COUNT(*) as total_trades, COALESCE(SUM(profit),0) as total_profit FROM trades")
    base = cur.fetchone()
    total_trades = base["total_trades"]
    total_profit = float(base["total_profit"])

    cur.execute("SELECT COUNT(*) as wins FROM trades WHERE profit > 0")
    wins = cur.fetchone()["wins"]

    cur.execute("SELECT COUNT(*) as losses FROM trades WHERE profit < 0")
    losses = cur.fetchone()["losses"]

    # avg win
    cur.execute("SELECT COALESCE(AVG(profit),0) as avg_win FROM trades WHERE profit > 0")
    avg_win = float(cur.fetchone()["avg_win"])

    # avg loss
    cur.execute("SELECT COALESCE(AVG(profit),0) as avg_loss FROM trades WHERE profit < 0")
    avg_loss = float(cur.fetchone()["avg_loss"])

    win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0

    # profit by symbol
    cur.execute("""
        SELECT symbol, COALESCE(SUM(profit),0) as profit_sum
        FROM trades
        GROUP BY symbol
        ORDER BY profit_sum DESC
    """)
    profit_by_symbol = [
        {"symbol": r["symbol"], "profit": float(r["profit_sum"])} for r in cur.fetchall()
    ]

    # profit by strategy
    cur.execute("""
        SELECT strategy, COALESCE(SUM(profit),0) as profit_sum
        FROM trades
        GROUP BY strategy
        ORDER BY profit_sum DESC
    """)
    profit_by_strategy = [
        {"strategy": r["strategy"], "profit": float(r["profit_sum"])} for r in cur.fetchall()
    ]

    # profit by emotion
    cur.execute("""
        SELECT emotion, COALESCE(SUM(profit),0) as profit_sum
        FROM trades
        GROUP BY emotion
        ORDER BY profit_sum DESC
    """)
    profit_by_emotion = [
        {"emotion": r["emotion"], "profit": float(r["profit_sum"])} for r in cur.fetchall()
    ]

    cur.close()
    conn.close()

    data = {
        "total_trades": total_trades,
        "total_profit": total_profit,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_by_symbol": profit_by_symbol,
        "profit_by_strategy": profit_by_strategy,
        "profit_by_emotion": profit_by_emotion
    }

    return jsonify(data)

@app.route("/feedback")
def feedback_page():
    return render_template("feedback.html")


def analyze_trades(trades):
    if not trades:
        return {
            "summary": {
                "total_trades": 0,
                "win_rate": 0,
                "net_pl": 0
            },
            "good": [],
            "bad": [],
            "improve": []
        }

    total = len(trades)
    profits = [t["profit"] for t in trades]
    wins = len([p for p in profits if p > 0])
    losses = len([p for p in profits if p < 0])
    win_rate = round((wins / total) * 100, 2)
    net_pl = round(sum(profits), 2)

    good, bad, improve = [], [], []

    if wins > losses:
        good.append("More winning trades than losing trades.")
    if not any(profits[i] < 0 and profits[i+1] < 0 for i in range(len(profits)-1)):
        good.append("No revenge trading detected.")
    if any(p > 300 for p in profits):
        good.append("Strong winning trade captured.")

    if total > 6:
        bad.append("Overtrading detected — too many trades.")
    if any(p < -500 for p in profits):
        bad.append("Heavy loss due to no stop-loss.")
    if any(p > 0 and p < 100 for p in profits):
        bad.append("Cutting winners too early.")
    if any(p < -200 for p in profits):
        bad.append("Risky position sizing detected.")

    if any(p > 0 and p < 100 for p in profits):
        improve.append("Hold winners longer for strong R:R.")
    if any(p < -300 for p in profits):
        improve.append("Reduce lot size on volatile days.")
    if total > 6:
        improve.append("Focus on quality setups only.")
    if losses > wins:
        improve.append("Avoid weak setups to improve accuracy.")

    return {
        "summary": {
            "total_trades": total,
            "win_rate": win_rate,
            "net_pl": net_pl
        },
        "good": good,
        "bad": bad,
        "improve": improve
    }
@app.route("/api/feedback")
def api_feedback_all():
    conn = get_db()
    cur = conn.cursor(dictionary=True)

    # 2-Day Trades
    cur.execute("""
        SELECT * FROM trades
        WHERE trade_datetime >= NOW() - INTERVAL 2 DAY
    """)
    two_day = analyze_trades(cur.fetchall())

    # Weekly (last 7 days)
    cur.execute("""
        SELECT * FROM trades
        WHERE trade_datetime >= NOW() - INTERVAL 7 DAY
    """)
    week = analyze_trades(cur.fetchall())

    # Monthly (last 30 days)
    cur.execute("""
        SELECT * FROM trades
        WHERE trade_datetime >= NOW() - INTERVAL 30 DAY
    """)
    month = analyze_trades(cur.fetchall())

    cur.close()
    conn.close()

    return jsonify({
        "two_day": two_day,
        "weekly": week,
        "monthly": month
    })

if __name__ == "__main__":
    app.run(debug=True)
