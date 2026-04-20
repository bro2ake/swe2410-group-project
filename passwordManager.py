from databaseConnect import DatabaseManager
import passwordGenerator

class PasswordManager:
    '''
    Manages password vault entries for a specific logged-in user.
    Allows the user to create, read, update, and delete their saved passwords.
    '''
    def __init__(self, logged_in_username):
        self.username = logged_in_username
        self.db = DatabaseManager()

    def create_entry(self, service, username, password):
        if self.db.add_password_entry(self.username, service, username, password):
            print(f"Successfully added password entry for {service}.")
            return True
        return False

    def view_entries(self):
        entries = self.db.get_password_entries(self.username)
        if not entries:
            print("No saved passwords found.")
            return []
        
        print("\n--- Saved Passwords ---")
        for entry in entries:
            entry_id, service, entry_user, entry_pass = entry
            print(f"ID: {entry_id} | Service: {service} | Username: {entry_user} | Password: {entry_pass}")
        print("-----------------------")
        return entries

    def update_entry(self, entry_id, new_service, new_username, new_password):
        if self.db.update_password_entry(entry_id, self.username, new_service, new_username, new_password):
            print(f"Successfully updated entry ID {entry_id}.")
            return True
        return False

    def delete_entry(self, entry_id):
        if self.db.delete_password_entry(entry_id, self.username):
            print(f"Successfully deleted entry ID {entry_id}.")
            return True
        return False

    def vault_menu(self):
        while True:
            print(f"\n=== Vault for {self.username} ===")
            print("1. View Passwords")
            print("2. Add Password")
            print("3. Edit Password")
            print("4. Delete Password")
            print("5. Logout")
            choice = input("Select an option (1-5): ")
            
            if choice == '1':
                self.view_entries()
            elif choice == '2':
                service = input("Service/Website: ")
                username = input("Username/Email: ")
                password = input("Password (leave blank to auto-generate): ")
                
                if not password:
                    password = passwordGenerator.genRandomPassword()
                    print(f"Generated Password: {password}")
                    
                self.create_entry(service, username, password)
            elif choice == '3':
                self.view_entries()
                entry_id = input("Enter the ID of the entry to edit: ")
                service = input("New Service/Website: ")
                username = input("New Username/Email: ")
                password = input("New Password: ")
                self.update_entry(entry_id, service, username, password)
            elif choice == '4':
                self.view_entries()
                entry_id = input("Enter the ID of the entry to delete: ")
                self.delete_entry(entry_id)
            elif choice == '5':
                print("Logging out...")
                break
            else:
                print("Invalid selection.")

if __name__ == "__main__":
    # Interactive menu for testing the vault standalone
    print("=== Password Manager Vault ===")
    test_user = input("Enter your account username to access vault: ")
    manager = PasswordManager(test_user)
    manager.vault_menu()