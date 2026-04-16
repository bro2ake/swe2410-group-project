from databaseConnect import DatabaseManager
from encryptionEngine import generate_hash

class CreateAccount:
    def __init__(self):
        self.db = DatabaseManager()
    def validate_email(self, email):
        if ('@' in email and '.' in email):
            return True
        return False