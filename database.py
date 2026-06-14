import sqlite3
from pathlib import Path

DB_PATH = Path("data/web_mvp.db")

def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        league TEXT,
        bookmaker TEXT,
        home_team TEXT,
        away_team TEXT,
        outcome TEXT,
        price REAL,
        model_probability REAL,
        market_probability REAL,
        edge REAL,
        value_label TEXT,
        classification TEXT,
        risk TEXT,
        confidence TEXT,
        igc INTEGER,
        consensus TEXT,
        reason TEXT
    )
    ''')

    conn.commit()
    conn.close()

def save_analysis(data, result):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for a in result["analyses"]:
        cur.execute('''
        INSERT INTO analyses (
            league, bookmaker, home_team, away_team, outcome, price,
            model_probability, market_probability, edge, value_label,
            classification, risk, confidence, igc, consensus, reason
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data["league"],
            data["bookmaker"],
            data["home_team"],
            data["away_team"],
            a["outcome_label"],
            a["price"],
            a["model_probability"],
            a["market_probability"],
            a["edge"],
            a["value_label"],
            a["classification"],
            a["risk"],
            a["confidence"],
            a["igc"],
            a["consensus"],
            a["reason"]
        ))

    conn.commit()
    conn.close()

def get_history(limit=100):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute('''
    SELECT * FROM analyses
    ORDER BY id DESC
    LIMIT ?
    ''', (limit,))

    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows
