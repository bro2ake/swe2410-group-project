"""
Streamlit UI for Password Manager Application
Integrates with existing backend: LoginPage, CreateAccount, PasswordManager, DatabaseManager
Session-based authentication with per-entry password masking, search/filter, and vault health analytics.
"""

import streamlit as st
from loginPage import LoginPage
from createAccount import CreateAccount
from passwordManager import PasswordManager
from passwordGenerator import genRandomPassword, passwordStrength
import sqlite3

# Valid entry types for password vault
VALID_ENTRY_TYPES = ["password", "api_key"]

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize session state variables on first app load."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "password_manager" not in st.session_state:
        st.session_state.password_manager = None
    if "revealed_entries" not in st.session_state:
        st.session_state.revealed_entries = {}  # {entry_id: True/False}
    if "auth_error" not in st.session_state:
        st.session_state.auth_error = None
    if "auth_success" not in st.session_state:
        st.session_state.auth_success = None


# ============================================================================
# AUTHENTICATION FUNCTIONS (Wrapper around backend)
# ============================================================================

def handle_login(username, password):
    """
    Authenticate user by calling LoginPage.login() backend function.
    Sets session state on successful login.
    """
    if not username or not password:
        st.session_state.auth_error = "Username and password required."
        return False

    login_page = LoginPage()
    if login_page.login(username, password):
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.password_manager = PasswordManager(username)
        st.session_state.revealed_entries = {}  # Reset revealed entries on login
        st.session_state.auth_error = None
        st.session_state.auth_success = f"Welcome, {username}!"
        return True
    else:
        st.session_state.auth_error = "Invalid username or password."
        st.session_state.auth_success = None
        return False


def handle_register(email, password, confirm_password):
    """
    Create new account by calling CreateAccount.create_account() backend function.
    Validates email and password strength before calling backend.
    """
    # Validate inputs
    if not email or not password or not confirm_password:
        return False, "All fields required."

    if password != confirm_password:
        return False, "Passwords do not match."

    # Call backend CreateAccount
    account_creator = CreateAccount()
    
    # Validate email (backend check)
    if not account_creator.validate_email(email):
        return False, "Invalid email format. Must contain @ and ."

    # Validate password strength (backend check)
    if not account_creator.validate_password(password):
        strength = account_creator.password_strength(password)
        return False, f"Password strength: {strength}. Must be 'Strong'."

    # Create account
    if account_creator.create_account(email, password):
        return True, "Account created successfully! Please log in."
    else:
        return False, "Registration failed. Email may already be in use."


def handle_logout():
    """Clear session state and return to login page."""
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.password_manager = None
    st.session_state.revealed_entries = {}
    st.session_state.auth_error = None
    st.session_state.auth_success = "Logged out successfully."


# ============================================================================
# LOGIN PAGE
# ============================================================================

def login_page():
    """
    Login page with form for authentication.
    Calls handle_login() which wraps LoginPage.login() backend function.
    """
    st.title("🔐 Password Manager Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.write("---")
        
        # Login form
        with st.form("login_form"):
            username = st.text_input("Email/Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                handle_login(username, password)
        
        st.write("---")
        
        # Display auth messages
        if st.session_state.auth_error:
            st.error(st.session_state.auth_error)
        if st.session_state.auth_success:
            st.success(st.session_state.auth_success)
        
        st.write("---")
        
        # Navigate to registration
        st.write("Don't have an account?")
        if st.button("Create Account", use_container_width=True):
            st.session_state.page = "register"
            st.rerun()


# ============================================================================
# REGISTRATION PAGE
# ============================================================================

def register_page():
    """
    Registration page with form for creating new accounts.
    Calls handle_register() which wraps CreateAccount.create_account() backend function.
    """
    st.title("📝 Create Account")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.write("---")
        
        # Registration form
        with st.form("register_form"):
            email = st.text_input("Email", key="register_email")
            password = st.text_input("Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm")
            
            # Display password strength
            if password:
                strength = passwordStrength(password)
                col_a, col_b = st.columns([1, 3])
                with col_a:
                    st.write("Strength:")
                with col_b:
                    st.write(strength)
            
            submit = st.form_submit_button("Create Account", use_container_width=True)
            
            if submit:
                success, message = handle_register(email, password, confirm_password)
                if success:
                    st.success(message)
                    st.write("Redirecting to login...")
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error(message)
        
        st.write("---")
        
        # Navigate back to login
        if st.button("Back to Login", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()


# ============================================================================
# DASHBOARD - MAIN VAULT VIEW
# ============================================================================

def dashboard_page():
    """
    Main dashboard showing user's vault with all stored credentials.
    Features: display entries, per-entry password masking, search/filter, CRUD operations.
    """
    st.title(f"🔒 Vault Dashboard - {st.session_state.username}")
    
    # Header with logout button
    col1, col2, col3 = st.columns([3, 1, 1])
    with col3:
        if st.button("Logout", use_container_width=True):
            handle_logout()
            st.rerun()
    
    st.write("---")
    
    # Fetch entries from backend
    pm = st.session_state.password_manager
    all_entries = pm.view_entries()
    
    # ========================================================================
    # VAULT HEALTH METRICS
    # ========================================================================
    
    health = pm.vault_health()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Entries", health["total_entries"])
    
    with col2:
        weak_count = health["weak_passwords"]
        st.metric("Weak Passwords", weak_count, delta=None if weak_count == 0 else "⚠️")
    
    with col3:
        reused_count = health["reused_passwords"]
        st.metric("Reused Passwords", reused_count, delta=None if reused_count == 0 else "⚠️")
    
    with col4:
        api_count = len([e for e in all_entries if e[4] == "api_key"])
        st.metric("API Keys", api_count)
    
    st.write("---")
    
    # ========================================================================
    # SEARCH & FILTER
    # ========================================================================
    
    st.subheader("🔍 Search & Filter")
    
    col1, col2 = st.columns(2)
    
    with col1:
        search_query = st.text_input("Search by service or username", key="search_input")
    
    with col2:
        filter_type = st.selectbox("Filter by type", ["All", "password", "api_key"], key="filter_type")
    
    # Apply filters
    filtered_entries = all_entries
    
    if filter_type != "All":
        filtered_entries = [e for e in filtered_entries if e[4] == filter_type]
    
    if search_query:
        search_lower = search_query.lower()
        filtered_entries = [
            e for e in filtered_entries
            if search_lower in e[1].lower() or search_lower in e[2].lower()
        ]
    
    st.write(f"Showing {len(filtered_entries)} of {len(all_entries)} entries")
    
    st.write("---")
    
    # ========================================================================
    # ADD NEW ENTRY FORM (Expandable)
    # ========================================================================
    
    with st.expander("➕ Add New Entry", expanded=False):
        st.subheader("Add New Credential")
        
        with st.form("add_entry_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                service = st.text_input("Service Name", key="add_service", placeholder="e.g., Gmail, GitHub")
            
            with col2:
                entry_type = st.selectbox("Entry Type", VALID_ENTRY_TYPES, key="add_type")
            
            username = st.text_input("Username/Email", key="add_username")
            
            col_pass, col_gen = st.columns([3, 1])
            with col_pass:
                password = st.text_input("Password", type="password", key="add_password")
            
            with col_gen:
                if st.form_submit_button("Generate", use_container_width=True):
                    generated = genRandomPassword(length=16, use_symbols=True, use_digits=True)
                    st.session_state.add_password = generated
                    st.rerun()
            
            # Display password strength
            if password:
                strength = passwordStrength(password)
                st.write(f"Password Strength: {strength}")
            
            if st.form_submit_button("Add Entry", use_container_width=True):
                if not service or not username or not password:
                    st.error("All fields required.")
                else:
                    success = pm.create_entry(service, username, password, entry_type)
                    if success:
                        st.success(f"✅ Entry added for {service}!")
                        st.rerun()
                    else:
                        st.error("Failed to add entry.")
    
    st.write("---")
    
    # ========================================================================
    # VAULT TABLE WITH CRUD OPERATIONS
    # ========================================================================
    
    st.subheader("📋 Your Credentials")
    
    if not filtered_entries:
        st.info("No credentials found.")
    else:
        # Create table display with expandable rows for each entry
        for idx, entry in enumerate(filtered_entries):
            entry_id, service, username, password, entry_type = entry
            
            # Toggle reveal state for this entry
            reveal_key = f"reveal_{entry_id}"
            if reveal_key not in st.session_state.revealed_entries:
                st.session_state.revealed_entries[reveal_key] = False
            
            # Display entry row
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 1, 1])
            
            with col1:
                type_label = "🔑 API Key" if entry_type == "api_key" else "🔐 Password"
                st.write(f"**{service}**")
                st.caption(type_label)
            
            with col2:
                st.write(f"**User:** {username}")
            
            with col3:
                # Conditionally display password or mask
                if st.session_state.revealed_entries[reveal_key]:
                    st.write(f"**Pass:** `{password}`")
                else:
                    st.write(f"**Pass:** `{'•' * 8}`")
            
            with col4:
                # Reveal/Hide toggle button
                reveal_text = "Hide" if st.session_state.revealed_entries[reveal_key] else "Reveal"
                if st.button(reveal_text, key=f"btn_reveal_{entry_id}", use_container_width=True):
                    st.session_state.revealed_entries[reveal_key] = not st.session_state.revealed_entries[reveal_key]
                    st.rerun()
            
            with col5:
                # Edit button
                if st.button("✏️", key=f"btn_edit_{entry_id}", use_container_width=True):
                    st.session_state.edit_entry_id = entry_id
                    st.rerun()
            
            with col6:
                # Delete button
                if st.button("🗑️", key=f"btn_delete_{entry_id}", use_container_width=True):
                    st.session_state.delete_entry_id = entry_id
                    st.rerun()
            
            st.write("---")
        
        # ====================================================================
        # EDIT MODAL (if edit_entry_id is set)
        # ====================================================================
        
        if "edit_entry_id" in st.session_state:
            entry_id = st.session_state.edit_entry_id
            # Find the entry to edit
            entry = next((e for e in all_entries if e[0] == entry_id), None)
            
            if entry:
                _, service, username, password, entry_type = entry
                
                st.subheader(f"Edit Entry #{entry_id}")
                
                with st.form("edit_entry_form"):
                    new_service = st.text_input("Service Name", value=service, key="edit_service")
                    new_username = st.text_input("Username/Email", value=username, key="edit_username")
                    new_password = st.text_input("Password", value=password, type="password", key="edit_password")
                    new_entry_type = st.selectbox("Entry Type", VALID_ENTRY_TYPES, 
                                                   index=VALID_ENTRY_TYPES.index(entry_type), 
                                                   key="edit_type")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.form_submit_button("Save Changes", use_container_width=True):
                            success = pm.update_entry(entry_id, new_service, new_username, new_password, new_entry_type)
                            if success:
                                st.success("✅ Entry updated!")
                                del st.session_state.edit_entry_id
                                st.rerun()
                            else:
                                st.error("Failed to update entry.")
                    
                    with col2:
                        if st.form_submit_button("Cancel", use_container_width=True):
                            del st.session_state.edit_entry_id
                            st.rerun()
        
        # ====================================================================
        # DELETE CONFIRMATION (if delete_entry_id is set)
        # ====================================================================
        
        if "delete_entry_id" in st.session_state:
            entry_id = st.session_state.delete_entry_id
            entry = next((e for e in all_entries if e[0] == entry_id), None)
            
            if entry:
                _, service, _, _, _ = entry
                
                st.warning(f"⚠️ Delete entry for **{service}**? This cannot be undone.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("Confirm Delete", use_container_width=True, key="btn_confirm_delete"):
                        success = pm.delete_entry(entry_id)
                        if success:
                            st.success("✅ Entry deleted!")
                            del st.session_state.delete_entry_id
                            st.rerun()
                        else:
                            st.error("Failed to delete entry.")
                
                with col2:
                    if st.button("Cancel", use_container_width=True, key="btn_cancel_delete"):
                        del st.session_state.delete_entry_id
                        st.rerun()


# ============================================================================
# PAGE ROUTER
# ============================================================================

def main():
    """Main entry point - router between pages based on login state."""
    st.set_page_config(
        page_title="Password Manager",
        page_icon="🔐",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session state
    init_session_state()
    
    # Page routing
    if st.session_state.logged_in:
        dashboard_page()
    else:
        # Determine which auth page to show
        if "page" not in st.session_state:
            st.session_state.page = "login"
        
        if st.session_state.page == "login":
            login_page()
        elif st.session_state.page == "register":
            register_page()


if __name__ == "__main__":
    main()
