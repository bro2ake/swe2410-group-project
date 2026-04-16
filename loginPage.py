from databaseConnect import DatabaseManager
from encryptionEngine import verify_native

'''
Handles login functionality, verifies user credentials against stored hashes in the database.
'''

class LoginPage:
    def __init__(self):
        self.db = DatabaseManager()

    def login(self, username, password):
        stored_password_hash = self.db.get_hash(username)

        if stored_password_hash is None:
            return False

        return verify_native(password, stored_password_hash)