import sqlite3

def init_db():
    conn = sqlite3.connect('metrics.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node TEXT NOT NULL,
            cpu REAL NOT NULL,
            mem REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def insert_metric(node, cpu, mem):
    conn = sqlite3.connect('metrics.db')
    c = conn.cursor()
    c.execute('INSERT INTO metrics (node, cpu, mem) VALUES (?, ?, ?)', (node, cpu, mem))
    conn.commit()
    conn.close()

def get_metrics_history(node, limit=100, since=None):
    conn = sqlite3.connect('metrics.db')
    c = conn.cursor()
    if since:
        c.execute('SELECT timestamp, cpu, mem FROM metrics WHERE node = ? AND timestamp >= ? ORDER BY timestamp ASC', (node, since))
    else:
        c.execute('SELECT timestamp, cpu, mem FROM metrics WHERE node = ? ORDER BY timestamp DESC LIMIT ?', (node, limit))
    rows = c.fetchall()
    conn.close()
    return rows[::-1] if not since else rows

