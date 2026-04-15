import sqlite3
'''
databaseConnect is used as an access point for the SQLite database we have chosen to use
The functionality of this will be adding users, adding passwords, and retrieving hashes
'''
class DatabaseManager:
    def __init__(self, db_name="user_data.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(db_name)
        self.create_table()
    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            passwordHash TEXT
        )
        """
        self._execute_query(query)
        
    def _execute_query(self, query, params=()):
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor
    
    def add_user(self, username, passwordHash):
        query = "INSERT INTO users (username, passwordHash) VALUES (?, ?)"
        try:
            self._execute_query(query, (username, passwordHash))
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_hash(self, username):
        query = "SELECT passwordHash FROM users WHERE username = ?"
        cursor = self._execute_query(query, (username,))
        result = cursor.fetchone()
        return result[0] if result else None