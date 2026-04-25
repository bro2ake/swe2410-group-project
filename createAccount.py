import passwordGenerator
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
    
    def password_strength(self, password):
        score = 0

        if len(password) >= 8:
            score += 1
        if len(password) >= 14:
            score += 1
        if any(char.isdigit() for char in password):
            score += 1
        if any(char.isupper() for char in password):
            score += 1
        if any(char.islower() for char in password):
            score += 1
        if any(not char.isalnum() for char in password):
            score += 1

        if score <= 2:
            return "Weak"
        elif score <= 4:
            return "Medium"
        return "Strong"

    def validate_password(self, password):
        return passwordGenerator.passwordStrength(password) == "✅ Strong"
    
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

    print("Password strength:", passwordGenerator.passwordStrength(password_input))
    
    if account_creator.create_account(username_input, password_input):
        print("Account created successfully!")
    else:
        print("Account creation failed. Ensure the email is valid, the password is at least 14 characters long with uppercase, lowercase, and digits, and the username doesn't already exist.")