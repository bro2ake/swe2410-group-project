import tkinter as tk
from tkinter import messagebox
from loginPage import LoginPage
from createAccount import CreateAccount
from passwordManager import PasswordManager

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

        # Initialize all the pages
        for F in (LoginFrame, CreateAccountFrame, VaultFrame):
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
        
        self.title_label = tk.Label(self, text="My Password Vault", font=("Arial", 18))
        self.title_label.pack(pady=20)
        
        # A Listbox to display saved passwords
        self.listbox = tk.Listbox(self, width=60)
        self.listbox.pack(pady=10)
        
        # Placeholder buttons for vault actions
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Add/Generate Password", command=lambda: messagebox.showinfo("Info", "Show Add dialog here")).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Edit Password", command=lambda: messagebox.showinfo("Info", "Show Edit dialog here")).grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Delete Password", command=lambda: messagebox.showinfo("Info", "Delete selected entry here")).grid(row=0, column=2, padx=5)
        
        tk.Button(self, text="Logout", command=self.logout).pack(side="bottom", pady=10)

    def refresh_data(self):
        if self.controller.logged_in_user:
            self.title_label.config(text=f"Vault for {self.controller.logged_in_user}")
            self.manager = PasswordManager(self.controller.logged_in_user)
            self.listbox.delete(0, tk.END)
            for entry in self.manager.view_entries():
                self.listbox.insert(tk.END, f"Service: {entry[1]} | Username: {entry[2]}")

    def logout(self):
        self.controller.logged_in_user = None
        self.listbox.delete(0, tk.END)
        self.controller.show_frame("LoginFrame")

if __name__ == "__main__":
    app = App()
    app.mainloop()
