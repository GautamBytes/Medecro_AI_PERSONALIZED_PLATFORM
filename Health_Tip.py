import sqlite3

def create_health_tips_table():
    conn = sqlite3.connect('health_tips.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS health_tips
                 (id INTEGER PRIMARY KEY,
                  doctor_id INTEGER,
                  specialization TEXT,
                  content TEXT,
                  image_path TEXT,
                  created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_health_tip(doctor_id, specialization, content, image_path):
    conn = sqlite3.connect('health_tips.db')
    c = conn.cursor()

    # Check if the table exists, create it if not
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='health_tips'")
    if not c.fetchone():
        create_health_tips_table()

    c.execute('''INSERT INTO health_tips (doctor_id, specialization, content, image_path)
                 VALUES (?, ?, ?, ?)''',
              (doctor_id, specialization, content, image_path))
    conn.commit()
    conn.close()

def delete_health_tip(post_id):
    conn = sqlite3.connect('health_tips.db')
    c = conn.cursor()
    c.execute('DELETE FROM health_tips WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()

def get_all_health_tips():
    conn = sqlite3.connect('health_tips.db')
    c = conn.cursor()
    c.execute('SELECT * FROM health_tips')
    health_tips = c.fetchall()
    conn.close()
    return health_tips

