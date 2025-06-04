import streamlit as st
import sqlite3
import datetime
import json
from pathlib import Path
import requests

DB_PATH = Path("data/life_os.db")

# Initialize database
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS habits(date TEXT, habit TEXT, completed INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS moods(date TEXT PRIMARY KEY, mood TEXT, notes TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS affirmations(date TEXT PRIMARY KEY, text TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS trades(timestamp TEXT, bias INTEGER, confidence INTEGER, notes TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS weekly_goals(week_start TEXT, goal TEXT, score INTEGER)")
conn.commit()
conn.close()

st.set_page_config(page_title="Life OS Dashboard", layout="wide")

st.title("Victor's Life OS Dashboard")

# Quote of the day
quote = ""
try:
    res = requests.get("https://api.quotable.io/random", timeout=5)
    if res.status_code == 200:
        data = res.json()
        quote = f"{data['content']} — {data['author']}"
except Exception:
    pass
if quote:
    st.info(quote)

# Tabs
tabs = st.tabs(["Daily Rituals", "TSLA Trades", "Devlog", "Weekly Planner"])

# Daily Rituals Tab
with tabs[0]:
    today = datetime.date.today().isoformat()
    st.header("Daily Rituals")
    habits = ["Exercise", "Meditation", "Reading"]
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for habit in habits:
        cur.execute("SELECT completed FROM habits WHERE date=? AND habit=?", (today, habit))
        row = cur.fetchone()
        completed = bool(row[0]) if row else False
        checked = st.checkbox(habit, value=completed, key=habit)
        if checked and not completed:
            cur.execute("INSERT INTO habits(date, habit, completed) VALUES(?,?,1)", (today, habit))
        elif not checked and completed:
            cur.execute("DELETE FROM habits WHERE date=? AND habit=?", (today, habit))
    mood = st.selectbox("Mood", ["😀", "🙂", "😐", "😞", "😡"])
    notes = st.text_input("Notes", "")
    if st.button("Save Mood"):
        cur.execute("REPLACE INTO moods(date, mood, notes) VALUES(?,?,?)", (today, mood, notes))
        conn.commit()
    cur.execute("SELECT mood, notes FROM moods WHERE date=?", (today,))
    mrow = cur.fetchone()
    if mrow:
        st.write(f"Mood saved: {mrow[0]} {mrow[1]}")
    aff = st.text_input("Affirmation", "", key="aff")
    if st.button("Save Affirmation"):
        cur.execute("REPLACE INTO affirmations(date, text) VALUES(?,?)", (today, aff))
        conn.commit()
    cur.execute("SELECT text FROM affirmations WHERE date=?", (today,))
    arow = cur.fetchone()
    if arow:
        st.write(f"Today's affirmation: {arow[0]}")
    conn.commit()
    conn.close()

# TSLA Trades Tab
with tabs[1]:
    st.header("TSLA Trade Log")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    with st.form("trade_form"):
        bias = st.slider("Bias (-2 short to 2 long)", -2, 2, 0)
        confidence = st.slider("Confidence", 0, 100, 50)
        notes = st.text_input("Notes")
        submitted = st.form_submit_button("Add Trade")
        if submitted:
            cur.execute(
                "INSERT INTO trades(timestamp, bias, confidence, notes) VALUES(?,?,?,?)",
                (datetime.datetime.now().isoformat(), bias, confidence, notes),
            )
            conn.commit()
    cur.execute("SELECT timestamp, bias, confidence, notes FROM trades ORDER BY timestamp DESC LIMIT 10")
    trades = cur.fetchall()
    st.table(trades)
    conn.close()

# Devlog Tab
with tabs[2]:
    st.header("Devlog Tasks")
    tasks_path = Path("runtime/tasks.json")
    if tasks_path.exists():
        with open(tasks_path) as f:
            tasks = json.load(f)
        for t in tasks:
            st.write(f"{t['name']} - {t['status']}")
    else:
        st.write("No tasks found")

# Weekly Planner Tab
with tabs[3]:
    st.header("Weekly Planner")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    week_start = (datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())).isoformat()
    goal = st.text_input("Weekly Goal")
    score = st.slider("Score", 0, 10, 0)
    if st.button("Save Goal"):
        cur.execute(
            "INSERT INTO weekly_goals(week_start, goal, score) VALUES(?,?,?)",
            (week_start, goal, score),
        )
        conn.commit()
    cur.execute("SELECT goal, score FROM weekly_goals WHERE week_start=?", (week_start,))
    rows = cur.fetchall()
    if rows:
        st.subheader("This Week's Goals")
        for g, s in rows:
            st.write(f"{g} - {s}/10")
    conn.close()
