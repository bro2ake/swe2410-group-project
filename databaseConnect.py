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
        query_users = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            passwordHash TEXT,
            mfa_enabled INTEGER DEFAULT 0,
            totp_secret TEXT
        )
        """
        self._execute_query(query_users)
        
        query_passwords = """
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY,
            owner_username TEXT,
            service TEXT,
            username TEXT,
            password TEXT,
            entry_type TEXT DEFAULT 'password',
            group_name TEXT DEFAULT 'other',
            FOREIGN KEY(owner_username) REFERENCES users(username)
        )
        """
        self._execute_query(query_passwords)
        
        # Migrate existing databases to add entry_type column if missing
        self._migrate_table()

    def _migrate_table(self):
        '''
        Adds the entry_type column to existing databases that were created
        before this column existed. Safe to run on new databases too —
        the exception is silently ignored if the column is already present.
        '''
        try:
            self._execute_query("ALTER TABLE passwords ADD COLUMN entry_type TEXT DEFAULT 'password'")
        except sqlite3.OperationalError:
            pass  # Column already exists, nothing to do

        try:
            self._execute_query("ALTER TABLE passwords ADD COLUMN group_name TEXT DEFAULT 'other'")
        except sqlite3.OperationalError:
            pass  # Column already exists, nothing to do

        try:
            self._execute_query("ALTER TABLE users ADD COLUMN mfa_enabled INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        try:
            self._execute_query("ALTER TABLE users ADD COLUMN totp_secret TEXT")
        except sqlite3.OperationalError:
            pass

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

    def get_mfa_state(self, username):
        """Returns (mfa_enabled: 0/1, totp_secret: str|None)."""
        query = "SELECT mfa_enabled, totp_secret FROM users WHERE username = ?"
        cursor = self._execute_query(query, (username,))
        row = cursor.fetchone()
        if not row:
            return (0, None)
        return (int(row[0] or 0), row[1])

    def set_totp_secret(self, username, totp_secret):
        query = "UPDATE users SET totp_secret = ? WHERE username = ?"
        self._execute_query(query, (totp_secret, username))
        return True

    def set_mfa_enabled(self, username, enabled):
        v = 1 if enabled else 0
        query = "UPDATE users SET mfa_enabled = ? WHERE username = ?"
        self._execute_query(query, (v, username))
        return True

    def clear_mfa(self, username):
        query = "UPDATE users SET mfa_enabled = 0, totp_secret = NULL WHERE username = ?"
        self._execute_query(query, (username,))
        return True

    def get_hash(self, username):
        query = "SELECT passwordHash FROM users WHERE username = ?"
        cursor = self._execute_query(query, (username,))
        result = cursor.fetchone()
        return result[0] if result else None

    def add_password_entry(self, owner_username, service, username, password, entry_type="password", group_name="other"):
        query = "INSERT INTO passwords (owner_username, service, username, password, entry_type, group_name) VALUES (?, ?, ?, ?, ?, ?)"
        self._execute_query(query, (owner_username, service, username, password, entry_type, group_name))
        return True

    def get_password_entries(self, owner_username):
        query = "SELECT id, service, username, password, entry_type, group_name FROM passwords WHERE owner_username = ?"
        cursor = self._execute_query(query, (owner_username,))
        return cursor.fetchall()

    def update_password_entry(self, entry_id, owner_username, service, username, password, entry_type="password", group_name="other"):
        query = "UPDATE passwords SET service = ?, username = ?, password = ?, entry_type = ?, group_name = ? WHERE id = ? AND owner_username = ?"
        self._execute_query(query, (service, username, password, entry_type, group_name, entry_id, owner_username))
        return True

    def delete_password_entry(self, entry_id, owner_username):
        query = "DELETE FROM passwords WHERE id = ? AND owner_username = ?"
        self._execute_query(query, (entry_id, owner_username))
        return True
