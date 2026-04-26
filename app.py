"""
Flask-based Password Manager UI
Replaces Streamlit with Flask for better Python version compatibility.
Integrates with existing backend: LoginPage, CreateAccount, PasswordManager
"""

from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from loginPage import LoginPage
from createAccount import CreateAccount
from passwordManager import PasswordManager
from passwordGenerator import genRandomPassword, passwordStrength
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate random secret key for sessions

# Valid entry types for password vault
VALID_ENTRY_TYPES = ["password", "api_key"]


# ============================================================================
# AUTHENTICATION DECORATORS & HELPERS
# ============================================================================

def login_required(f):
    """Decorator to require login for routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session or not session['logged_in']:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def handle_login(username, password):
    """Authenticate user by calling LoginPage.login() backend function."""
    if not username or not password:
        return False, "Username and password required."

    login_page = LoginPage()
    if login_page.login(username, password):
        session['logged_in'] = True
        session['username'] = username
        return True, f"Welcome, {username}!"
    else:
        return False, "Invalid username or password."


def handle_register(email, password, confirm_password):
    """Create new account by calling CreateAccount.create_account() backend function."""
    if not email or not password or not confirm_password:
        return False, "All fields required."

    if password != confirm_password:
        return False, "Passwords do not match."

    account_creator = CreateAccount()
    
    if not account_creator.validate_email(email):
        return False, "Invalid email format. Must contain @ and ."

    if not account_creator.validate_password(password):
        strength = account_creator.password_strength(password)
        return False, f"Password strength: {strength}. Must be 'Strong'."

    if account_creator.create_account(email, password):
        return True, "Account created successfully! Please log in."
    else:
        return False, "Registration failed. Email may already be in use."


# ============================================================================
# ROUTES - AUTHENTICATION
# ============================================================================

@app.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login."""
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        success, message = handle_login(username, password)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(message, 'error')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page and handler."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        success, message = handle_register(email, password, confirm_password)
        
        if success:
            flash(message, 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    """Logout user and clear session."""
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))


# ============================================================================
# ROUTES - DASHBOARD & VAULT
# ============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard showing user's vault."""
    username = session.get('username')
    pm = PasswordManager(username)
    
    # Fetch all entries
    entries = pm.view_entries()
    
    # Get vault health metrics
    health = pm.vault_health()
    
    # Extract metrics
    total_entries = health.get('total_entries', 0)
    weak_passwords = health.get('weak_passwords', 0)
    reused_passwords = health.get('reused_passwords', 0)
    api_count = len([e for e in entries if e[4] == "api_key"])
    
    return render_template('dashboard.html',
                         username=username,
                         entries=entries,
                         total_entries=total_entries,
                         weak_passwords=weak_passwords,
                         reused_passwords=reused_passwords,
                         api_count=api_count,
                         valid_types=VALID_ENTRY_TYPES)


@app.route('/api/entries', methods=['GET'])
@login_required
def get_entries():
    """API endpoint to get filtered entries."""
    username = session.get('username')
    pm = PasswordManager(username)
    
    search_query = request.args.get('search', '').lower()
    filter_type = request.args.get('type', 'all')
    
    entries = pm.view_entries()
    
    # Apply filters
    if filter_type != 'all':
        entries = [e for e in entries if e[4] == filter_type]
    
    if search_query:
        entries = [
            e for e in entries
            if search_query in e[1].lower() or search_query in e[2].lower()
        ]
    
    # Format for JSON response
    entries_data = [
        {
            'id': e[0],
            'service': e[1],
            'username': e[2],
            'password': e[3],
            'type': e[4]
        }
        for e in entries
    ]
    
    return jsonify(entries_data)


@app.route('/add-entry', methods=['POST'])
@login_required
def add_entry():
    """Add new credential entry."""
    username = session.get('username')
    pm = PasswordManager(username)
    
    service = request.form.get('service', '').strip()
    username_cred = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    entry_type = request.form.get('type', 'password')
    
    if not all([service, username_cred, password]):
        flash('All fields are required.', 'error')
        return redirect(url_for('dashboard'))
    
    if entry_type not in VALID_ENTRY_TYPES:
        flash('Invalid entry type.', 'error')
        return redirect(url_for('dashboard'))
    
    success = pm.create_entry(service, username_cred, password, entry_type)
    
    if success:
        flash(f'✅ Entry added for {service}!', 'success')
    else:
        flash('Failed to add entry.', 'error')
    
    return redirect(url_for('dashboard'))


@app.route('/edit-entry/<int:entry_id>', methods=['POST'])
@login_required
def edit_entry(entry_id):
    """Edit an existing entry."""
    username = session.get('username')
    pm = PasswordManager(username)
    
    service = request.form.get('service', '').strip()
    username_cred = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    entry_type = request.form.get('type', 'password')
    
    if not all([service, username_cred, password]):
        flash('All fields are required.', 'error')
        return redirect(url_for('dashboard'))
    
    if entry_type not in VALID_ENTRY_TYPES:
        flash('Invalid entry type.', 'error')
        return redirect(url_for('dashboard'))
    
    success = pm.update_entry(entry_id, service, username_cred, password, entry_type)
    
    if success:
        flash(f'✅ Entry updated for {service}!', 'success')
    else:
        flash('Failed to update entry.', 'error')
    
    return redirect(url_for('dashboard'))


@app.route('/delete-entry/<int:entry_id>', methods=['POST'])
@login_required
def delete_entry(entry_id):
    """Delete an entry."""
    username = session.get('username')
    pm = PasswordManager(username)
    
    success = pm.delete_entry(entry_id)
    
    if success:
        flash('✅ Entry deleted!', 'success')
    else:
        flash('Failed to delete entry.', 'error')
    
    return redirect(url_for('dashboard'))


@app.route('/api/password-strength/<password>')
@login_required
def get_password_strength(password):
    """API endpoint to get password strength."""
    strength = passwordStrength(password)
    return jsonify({'strength': strength})


@app.route('/api/generate-password')
@login_required
def generate_password():
    """API endpoint to generate a random password."""
    generated = genRandomPassword(length=16, use_symbols=True, use_digits=True)
    return jsonify({'password': generated})


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return redirect(url_for('index'))


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    flash('An error occurred. Please try again.', 'error')
    return redirect(url_for('dashboard') if 'logged_in' in session else url_for('login'))


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("🔐 Password Manager Flask App")
    print("Starting on http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    app.run(debug=True, port=5000)
