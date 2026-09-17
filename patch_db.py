import sqlite3

conn = sqlite3.connect('backend/navcare.db')
c = conn.cursor()

c.execute('''
CREATE TABLE IF NOT EXISTS analytics_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    session_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

conn.commit()
print("Analytics table added to database!")
