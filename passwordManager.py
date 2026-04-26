from databaseConnect import DatabaseManager
import passwordGenerator

# Valid entry types for the password vault
VALID_ENTRY_TYPES = ["password", "api_key"]
# Work / Personal / Social (plus Other)
VALID_GROUP_NAMES = ["work", "personal", "social", "other"]

class PasswordManager:
    '''
    Manages password vault entries for a specific logged-in user.
    Allows the user to create, read, update, and delete their saved passwords.
    '''
    def __init__(self, logged_in_username):
        self.username = logged_in_username
        self.db = DatabaseManager()

    def create_entry(self, service, username, password, entry_type="password", group_name="other"):
        if entry_type not in VALID_ENTRY_TYPES:
            print(f"Invalid entry type '{entry_type}'. Must be one of: {VALID_ENTRY_TYPES}")
            return False
        if group_name not in VALID_GROUP_NAMES:
            print(f"Invalid group '{group_name}'. Must be one of: {VALID_GROUP_NAMES}")
            return False
        if self.db.add_password_entry(self.username, service, username, password, entry_type, group_name):
            print(f"Successfully added password {entry_type} entry for {service}.")
            return True
        return False

    def view_entries(self, filter_type=None, filter_group=None):
        # Returns all entries. Optional filters: entry_type ("password", "api_key") and/or group
        entries = self.db.get_password_entries(self.username)
        if filter_type:
            entries = [e for e in entries if e[4] == filter_type]
        if filter_group:
            entries = [e for e in entries if e[5] == filter_group]
        return entries

    def _print_entries(self, entries):
        if not entries:
            print("No saved passwords found.")
            return

        print("\n--- Saved Passwords ---")
        for entry in entries:
            entry_id, service, entry_user, entry_pass, entry_type, group_name = entry
            label = "API Key" if entry_type == "api_key" else "Password"
            g = group_name or "other"
            print(f"ID: {entry_id} | [{label}] | [{g}] | Service: {service} | Username: {entry_user} | Password: {entry_pass}")
        print("-----------------------")

    def update_entry(self, entry_id, new_service, new_username, new_password, new_entry_type=None, new_group_name=None):
        # new_entry_type / new_group_name: pass None to use defaults (password / other) for non-Flask paths
        et = new_entry_type if new_entry_type is not None else "password"
        gn = new_group_name if new_group_name is not None else "other"
        if et not in VALID_ENTRY_TYPES:
            print(f"Invalid entry type ' {et}'. Must be one of: {VALID_ENTRY_TYPES}")
            return False
        if gn not in VALID_GROUP_NAMES:
            print(f"Invalid group '{gn}'. Must be one of: {VALID_GROUP_NAMES}")
            return False
        if self.db.update_password_entry(entry_id, self.username, new_service, new_username, new_password, et, gn):
            print(f"Successfully updated entry ID {entry_id}.")
            return True
        return False

    def delete_entry(self, entry_id):
        if self.db.delete_password_entry(entry_id, self.username):
            print(f"Successfully deleted entry ID {entry_id}.")
            return True
        return False
        
    def _prompt_entry_type(self):
        while True:
            print("Entry type:")
            print("    1. Password")
            print("    2. API Key")
            choice = input("Select type (1-2): ")
            if choice == '1':
                return "password"
            elif choice == '2':
                return "api_key"
            else:
                print("Invalid selection, please enter 1 or 2.")
    
    # Valut health menu 
    def vault_health(self):
        entries = self.view_entries()

        if not entries:
            return {
                "total_entries": 0,
                "weak_passwords": 0,
                "reused_passwords": 0
            }

        passwords = [entry[3] for entry in entries]
        reused_count = len(passwords) - len(set(passwords))

        weak_pass_count = 0
        for password in passwords:
            if passwordGenerator.passwordStrength(password) == "❌ Weak":
                weak_pass_count += 1

        return {
            "total_entries": len(entries),
            "weak_passwords": weak_pass_count,
            "reused_passwords": reused_count
        }

    # May need to change to allow filtering by type
    def vault_menu(self):
        while True:
            print(f"\n=== Vault for {self.username} ===")
            print("1. View Passwords")
            print("2. Add Password")
            print("3. Edit Password")
            print("4. Delete Password")
            print("5. Vault Health")
            print("6. Logout")
            choice = input("Select an option (1-6): ")
            
            if choice == '1':
                entries = self.view_entries()
                self._print_entries(entries)
            elif choice == '2':
                service = input("Service/Website: ")
                username = input("Username/Email: ")
                password = input("Password (leave blank to auto-generate): ")
                
                if not password:
                    length = input("Enter desired password length (default 16): ")
                    use_symbols = input("Include symbols? (y/n): ").lower()

                    if not length:
                        length = 16
                    else:
                        length = int(length)

                    symbols_enabled = (use_symbols == 'y')

                    password = passwordGenerator.genRandomPassword(length=length, use_symbols=symbols_enabled)
                    print(f"Generated Password: {password}")

                print("Password Strength:", passwordGenerator.passwordStrength(password))    
                self.create_entry(service, username, password)
            elif choice == '3':
                entries = self.view_entries()
                self._print_entries(entries)
                if entries:
                    entry_id_str = input("Enter the ID of the entry to edit: ").strip()
                    service = input("New Service/Website: ")
                    username = input("New Username/Email: ")
                    password = input("New Password: ")
                    match = next((e for e in entries if str(e[0]) == entry_id_str), None)
                    if match:
                        self.update_entry(
                            int(match[0]), service, username, password, match[4], match[5] if len(match) > 5 and match[5] else "other"
                        )
                    else:
                        print("No entry with that ID.")
            elif choice == '4':
                entries = self.view_entries()
                self._print_entries(entries)
                if entries:
                    entry_id = input("Enter the ID of the entry to delete: ")
                    self.delete_entry(entry_id)
            elif choice == '5':
                health = self.vault_health()
                print("\n--- Vault Health ---")
                print("Total Entries:", health["total_entries"])
                print("Weak Passwords:", health["weak_passwords"])
                print("Reused Passwords:", health["reused_passwords"])
            elif choice == '6':
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
