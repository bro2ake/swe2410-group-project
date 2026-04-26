import tkinter as tk
from tkinter import messagebox
from loginPage import LoginPage
from createAccount import CreateAccount
from passwordManager import PasswordManager
import passwordGenerator

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Password Manager")
        self.geometry("600x400")

        # The container is where we'll stack our frames on top of each other.
        self.container = tk.Frame(self)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        self.logged_in_user = None
        self.entry_to_action = None

        # Initialize all the pages
        for F in (LoginFrame, CreateAccountFrame, VaultFrame, AddPasswordFrame, DeletePasswordFrame, EditPasswordFrame):
            page_name = F.__name__
            # Pass the container as parent, and the App instance as controller
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            
            # Put all pages in the same location; the one on top will be visible
            frame.grid(row=0, column=0, sticky="nsew")

        # Start by showing the login screen
        self.show_frame("LoginFrame")

    def show_frame(self, page_name):
        """Brings the specified frame to the front."""
        frame = self.frames[page_name]
        frame.tkraise()
        
        # If navigating to the vault, refresh the data for the logged-in user
        if page_name == "VaultFrame":
            frame.refresh_data()
        if page_name in ("DeletePasswordFrame", "EditPasswordFrame"):
            frame.on_show()

class LoginFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.login_backend = LoginPage() # Using your existing backend logic

        tk.Label(self, text="Login", font=("Arial", 18)).pack(pady=20)
        
        tk.Label(self, text="Username:").pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack()

        tk.Label(self, text="Password:").pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()

        tk.Button(self, text="Login", command=self.attempt_login).pack(pady=10)
        tk.Button(self, text="Create Account", command=lambda: controller.show_frame("CreateAccountFrame")).pack()

    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if self.login_backend.login(username, password):
            self.controller.logged_in_user = username
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.controller.show_frame("VaultFrame")
        else:
            messagebox.showerror("Error", "Invalid username or password")

class CreateAccountFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.create_account_backend = CreateAccount()

        tk.Label(self, text="Create Account", font=("Arial", 18)).pack(pady=20)
        
        tk.Label(self, text="Email (Username):").pack()
        self.username_entry = tk.Entry(self)
        self.username_entry.pack()

        tk.Label(self, text="Password:").pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack()

        tk.Button(self, text="Create Account", command=self.attempt_create_account).pack(pady=10)
        tk.Button(self, text="Back to Login", command=lambda: controller.show_frame("LoginFrame")).pack()

    def attempt_create_account(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if self.create_account_backend.create_account(username, password):
            messagebox.showinfo("Success", "Account created successfully!")
            self.username_entry.delete(0, tk.END)
            self.password_entry.delete(0, tk.END)
            self.controller.show_frame("LoginFrame")
        else:
            messagebox.showerror("Error", "Account creation failed. Check requirements.")

class VaultFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.manager = None
        self.entries = []
        
        self.title_label = tk.Label(self, text="My Password Vault", font=("Arial", 18))
        self.title_label.pack(pady=20)
        
        # A Listbox to display saved passwords
        self.listbox = tk.Listbox(self, width=60)
        self.listbox.pack(pady=10)
        self.listbox.bind("<Double-1>", self.show_password)
        
        # Placeholder buttons for vault actions
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="View Password", command=self.show_password).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Add/Generate Password", command=lambda: controller.show_frame("AddPasswordFrame")).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Edit Password", command=self.prompt_edit).grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="Delete Password", command=self.prompt_delete).grid(row=0, column=3, padx=5)
        
        tk.Button(self, text="Logout", command=self.logout).pack(side="bottom", pady=10)

    def refresh_data(self):
        if self.controller.logged_in_user:
            self.title_label.config(text=f"Vault for {self.controller.logged_in_user}")
            self.manager = PasswordManager(self.controller.logged_in_user)
            self.listbox.delete(0, tk.END)
            self.entries = self.manager.view_entries()
            for entry in self.entries:
                self.listbox.insert(tk.END, f"Service: {entry[1]} | Username: {entry[2]}")

    def show_password(self, event=None):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select an entry to view.")
            return

        selected_index = selected_indices[0]
        entry = self.entries[selected_index]
        
        service = entry[1]
        password = entry[3]
        
        messagebox.showinfo("Password", f"Password for '{service}':\n\n{password}")

    def prompt_edit(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select an entry to edit.")
            return

        selected_index = selected_indices[0]
        entry_to_edit = self.entries[selected_index]
        self.controller.entry_to_action = entry_to_edit
        self.controller.show_frame("EditPasswordFrame")

    def prompt_delete(self):
        selected_indices = self.listbox.curselection()
        if not selected_indices:
            messagebox.showwarning("No Selection", "Please select an entry to delete.")
            return

        selected_index = selected_indices[0]
        entry_to_delete = self.entries[selected_index]
        self.controller.entry_to_action = entry_to_delete
        self.controller.show_frame("DeletePasswordFrame")

    def logout(self):
        self.controller.logged_in_user = None
        self.listbox.delete(0, tk.END)
        self.entries = []
        self.controller.show_frame("LoginFrame")

class AddPasswordFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Add New Password", font=("Arial", 18)).pack(pady=20)

        # Using a frame for better layout
        form_frame = tk.Frame(self)
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="Service/Website:", width=15, anchor='w').grid(row=0, column=0, padx=5, pady=5)
        self.service_entry = tk.Entry(form_frame, width=40)
        self.service_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Username/Email:", width=15, anchor='w').grid(row=1, column=0, padx=5, pady=5)
        self.username_entry = tk.Entry(form_frame, width=40)
        self.username_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Password:", width=15, anchor='w').grid(row=2, column=0, padx=5, pady=5)
        
        password_inner_frame = tk.Frame(form_frame)
        password_inner_frame.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        self.password_entry = tk.Entry(password_inner_frame, width=30)
        self.password_entry.pack(side="left")
        tk.Button(password_inner_frame, text="Generate", command=self.generate_password).pack(side="left", padx=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Save", command=self.save_entry).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="Back to Vault", command=lambda: controller.show_frame("VaultFrame")).grid(row=0, column=1, padx=10)

    def generate_password(self):
        new_password = passwordGenerator.genRandomPassword()
        self.password_entry.delete(0, tk.END)
        self.password_entry.insert(0, new_password)

    def save_entry(self):
        service = self.service_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not service or not username or not password:
            messagebox.showwarning("Input Error", "All fields are required.")
            return

        if self.controller.logged_in_user:
            manager = PasswordManager(self.controller.logged_in_user)
            if manager.create_entry(service, username, password):
                messagebox.showinfo("Success", "Password entry saved successfully!")
                self.service_entry.delete(0, tk.END)
                self.username_entry.delete(0, tk.END)
                self.password_entry.delete(0, tk.END)
                self.controller.show_frame("VaultFrame")
            else:
                messagebox.showerror("Database Error", "Failed to save the entry.")
        else:
            messagebox.showerror("Error", "No active user session found. Please log out and log in again.")


class DeletePasswordFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.login_backend = LoginPage()

        tk.Label(self, text="Confirm Deletion", font=("Arial", 18)).pack(pady=20)
        
        self.confirm_label = tk.Label(self, text="", font=("Arial", 12))
        self.confirm_label.pack(pady=10)

        tk.Label(self, text="Enter your account password to confirm:").pack()
        self.password_entry = tk.Entry(self, show="*")
        self.password_entry.pack(pady=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Confirm Delete", command=self.confirm_delete).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="Cancel", command=self.cancel).grid(row=0, column=1, padx=10)

    def on_show(self):
        if self.controller.entry_to_action:
            service_name = self.controller.entry_to_action[1]
            self.confirm_label.config(text=f"Are you sure you want to delete the password for '{service_name}'?")
        self.password_entry.delete(0, tk.END)

    def confirm_delete(self):
        entry_to_delete = self.controller.entry_to_action
        if not entry_to_delete:
            self.cancel()
            return

        password = self.password_entry.get()
        username = self.controller.logged_in_user

        if not password:
            messagebox.showwarning("Input Error", "Password is required to confirm deletion.")
            return

        if self.login_backend.login(username, password):
            manager = PasswordManager(username)
            entry_id = entry_to_delete[0]  # The ID is the first element
            if manager.delete_entry(entry_id):
                messagebox.showinfo("Success", "Password entry deleted successfully!")
                self.cancel()
            else:
                messagebox.showerror("Database Error", "Failed to delete the entry.")
        else:
            messagebox.showerror("Authentication Failed", "Incorrect password. Deletion cancelled.")

    def cancel(self):
        self.password_entry.delete(0, tk.END)
        self.controller.entry_to_action = None
        self.controller.show_frame("VaultFrame")

class EditPasswordFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Edit Password", font=("Arial", 18)).pack(pady=20)
        
        self.service_label = tk.Label(self, text="", font=("Arial", 12))
        self.service_label.pack(pady=10)

        form_frame = tk.Frame(self)
        form_frame.pack(pady=10)

        tk.Label(form_frame, text="Old Password:", width=15, anchor='w').grid(row=0, column=0, padx=5, pady=5)
        self.old_password_entry = tk.Entry(form_frame, width=30, show="*")
        self.old_password_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="New Password:", width=15, anchor='w').grid(row=1, column=0, padx=5, pady=5)
        
        password_inner_frame = tk.Frame(form_frame)
        password_inner_frame.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        self.new_password_entry = tk.Entry(password_inner_frame, width=20)
        self.new_password_entry.pack(side="left")
        tk.Button(password_inner_frame, text="Generate", command=self.generate_password).pack(side="left", padx=5)

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="Save Changes", command=self.save_changes).grid(row=0, column=0, padx=10)
        tk.Button(btn_frame, text="Cancel", command=self.cancel).grid(row=0, column=1, padx=10)

    def on_show(self):
        if self.controller.entry_to_action:
            service_name = self.controller.entry_to_action[1]
            self.service_label.config(text=f"Editing password for: {service_name}")
        self.old_password_entry.delete(0, tk.END)
        self.new_password_entry.delete(0, tk.END)

    def generate_password(self):
        new_password = passwordGenerator.genRandomPassword()
        self.new_password_entry.delete(0, tk.END)
        self.new_password_entry.insert(0, new_password)

    def save_changes(self):
        entry_to_edit = self.controller.entry_to_action
        if not entry_to_edit:
            self.cancel()
            return

        old_password = self.old_password_entry.get()
        new_password = self.new_password_entry.get()
        actual_old_password = entry_to_edit[3]

        if not old_password or not new_password:
            messagebox.showwarning("Input Error", "Both old and new passwords are required.")
            return

        if old_password != actual_old_password:
            messagebox.showerror("Authentication Failed", "Incorrect old service password.")
            return

        manager = PasswordManager(self.controller.logged_in_user)
        entry_id = entry_to_edit[0]
        service = entry_to_edit[1]
        username = entry_to_edit[2]
        entry_type = entry_to_edit[4] if len(entry_to_edit) > 4 else "password"
        group_name = entry_to_edit[5] if len(entry_to_edit) > 5 else "other"

        if manager.update_entry(entry_id, service, username, new_password, entry_type, group_name):
            messagebox.showinfo("Success", "Password updated successfully!")
            self.cancel()
        else:
            messagebox.showerror("Database Error", "Failed to update the entry.")

    def cancel(self):
        self.old_password_entry.delete(0, tk.END)
        self.new_password_entry.delete(0, tk.END)
        self.controller.entry_to_action = None
        self.controller.show_frame("VaultFrame")

if __name__ == "__main__":
    app = App()
    app.mainloop()
