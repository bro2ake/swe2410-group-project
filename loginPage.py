from databaseConnect import DatabaseManager
from encryptionEngine import verify_native
from createAccount import CreateAccount
from passwordManager import PasswordManager

'''
Handles login functionality, verifies user credentials against stored hashes in the database.
'''

class LoginPage:
    def __init__(self):
        self.db = DatabaseManager()

    def login(self, username, password):
        stored_password_hash = self.db.get_hash(username)

        # Query the database for the stored hash of the provided username
        if stored_password_hash is None:
            return False

        # Verify the provided password against the stored hash

        return verify_native(password, stored_password_hash)

if __name__ == "__main__":
    while True:
        print("\n=== Welcome ===")
        print("1. Login")
        print("2. Create Account")
        print("3. Exit")
        choice = input("Select an option (1-3): ")
        
        if choice == '1':
            login_page = LoginPage()
            print("\n=== Login ===")
            username_input = input("Username: ")
            password_input = input("Password: ")
            
            if login_page.login(username_input, password_input):
                print("Login successful!")
                manager = PasswordManager(username_input)
                manager.vault_menu()
                
            else:
                print("Login failed. Invalid username or password.")
        elif choice == '2':
            account_creator = CreateAccount()
            print("\n=== Create Account ===")
            username_input = input("Email (Username): ")
            password_input = input("Password: ")
            
            if account_creator.create_account(username_input, password_input):
                print("Account created successfully!")
            else:
                print("Account creation failed. Ensure the email is valid, the password is at least 14 characters long with uppercase, lowercase, and digits, and the username doesn't already exist.")
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid selection. Please try again.")