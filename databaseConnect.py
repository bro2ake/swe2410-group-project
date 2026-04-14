import sqlite3

# 1. Connect to the database (it creates the file if it doesn't exist)
conn = sqlite3.connect('project_data.db')
cursor = conn.cursor()

# 2. Create a table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )
''')

# 3. Function to save a user (Construction Phase)
def save_user(username, hashed_password):
    try:
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', 
                       (username, hashed_password))
        conn.commit()
    except sqlite3.IntegrityError:
        print("Username already exists!")

# Always close the connection when done
# conn.close()