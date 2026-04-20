from databaseConnect import DatabaseManager
from encryptionEngine import generate_hash

class CreateAccount:
    '''
    CreateAccount class is reponsible for account creation including 
    validating email and password strength, and storing the new account information into the database.
    '''
    def __init__(self):
        self.db = DatabaseManager()
    def validate_email(self, email):
        if ('@' in email and '.' in email):
            return True
        return False
    
    def validate_password(self, password):
        # Strong password criteria: at least 14 characters, has uppercase, lowercase, and digits for security
        if len(password) < 14:
            return False
        if not any(char.isdigit() for char in password):
            return False
        if not any(char.isupper() for char in password):
            return False
        if not any(char.islower() for char in password):
            return False
        return True
    
    def create_account(self, username, password):
        if not self.validate_email(username):
            return False

        if not self.validate_password(password):
            return False

        # Generate secure hash using encryptionEngine and store in database
        password_hash = generate_hash(password)
        return self.db.add_user(username, password_hash)

if __name__ == "__main__":
    account_creator = CreateAccount()
    print("=== Create Account ===")
    username_input = input("Email (Username): ")
    password_input = input("Password: ")
    
    if account_creator.create_account(username_input, password_input):
        print("Account created successfully!")
    else:
        print("Account creation failed. Ensure the email is valid, the password is at least 14 characters long with uppercase, lowercase, and digits, and the username doesn't already exist.")