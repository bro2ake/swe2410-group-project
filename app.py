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
from databaseConnect import DatabaseManager
import os
import base64
import io
import pyotp
import qrcode
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Generate random secret key for sessions

# Valid entry types for password vault
VALID_ENTRY_TYPES = ["password", "api_key"]
# Work / Personal / Social organization
VALID_GROUPS = ["work", "personal", "social", "other"]

TOTP_ISSUER = "PasswordManager"


def _totp_provisioning_uri(secret, account_name):
    return pyotp.TOTP(secret).provisioning_uri(name=account_name, issuer_name=TOTP_ISSUER)


def _make_qr_data_uri(provisioning_uri):
    buf = io.BytesIO()
    img = qrcode.make(provisioning_uri)
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def _finalize_session_login(username):
    session["logged_in"] = True
    session["username"] = username
    session.pop("mfa_pending_user", None)


def _password_login_result(username, password):
    """
    After primary password check: 'success' and username, or 'mfa', or 'error' and message.
    """
    if not username or not password:
        return "error", "Username and password required."
    login_page = LoginPage()
    if not login_page.login(username, password):
        return "error", "Invalid username or password."
    db = DatabaseManager()
    mfa_en, totp_secret = db.get_mfa_state(username)
    if mfa_en and totp_secret:
        return "mfa", username
    return "success", username


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
    """Redirect to dashboard if logged in, MFA step, or login."""
    if 'logged_in' in session and session.get('logged_in'):
        return redirect(url_for('dashboard'))
    if session.get('mfa_pending_user') and not session.get('logged_in'):
        return redirect(url_for('mfa_verify'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login: password first; MFA users go to mfa_verify."""
    if request.method == 'GET' and session.get('mfa_pending_user'):
        return redirect(url_for('mfa_verify'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        result, payload = _password_login_result(username, password)
        if result == 'error':
            flash(payload, 'error')
        elif result == 'mfa':
            session['mfa_pending_user'] = payload
            return redirect(url_for('mfa_verify'))
        else:
            _finalize_session_login(payload)
            flash(f"Welcome, {payload}!", 'success')
            return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/login/mfa', methods=['GET', 'POST'])
def mfa_verify():
    """Second factor after password (TOTP via PyOTP)."""
    pending = session.get('mfa_pending_user')
    if not pending:
        flash('Log in with your password first.', 'warning')
        return redirect(url_for('login'))
    db = DatabaseManager()
    mfa_en, totp_secret = db.get_mfa_state(pending)
    if not mfa_en or not totp_secret:
        session.pop('mfa_pending_user', None)
        flash('MFA is not set up for this account. Try again.', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        raw = request.form.get('code', '') or ''
        code = raw.replace(' ', '').strip()
        if pyotp.TOTP(totp_secret).verify(code, valid_window=1):
            _finalize_session_login(pending)
            flash('Signed in with authenticator. Welcome!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid or expired code. Try again.', 'error')
    return render_template('mfa.html', username=pending)


@app.route('/login/cancel-mfa', methods=['GET', 'POST'])
def login_cancel_mfa():
    session.pop('mfa_pending_user', None)
    flash('Login cancelled. Enter your password again if you want to sign in.', 'info')
    return redirect(url_for('login'))


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
# MFA settings (TOTP / PyOTP) — after login
# ============================================================================

@app.route('/account/mfa', methods=['GET'])
@login_required
def account_mfa():
    username = session.get('username')
    db = DatabaseManager()
    mfa_en, secret = db.get_mfa_state(username)
    mfa_on = bool(mfa_en)
    enrollment_secret = None
    qr_data_uri = None
    if not mfa_on and secret:
        enrollment_secret = secret
        uri = _totp_provisioning_uri(secret, username)
        qr_data_uri = _make_qr_data_uri(uri)
    return render_template(
        'account_mfa.html',
        mfa_enabled=mfa_on,
        enrollment_secret=enrollment_secret,
        qr_data_uri=qr_data_uri,
    )


@app.route('/account/mfa/start', methods=['POST'])
@login_required
def account_mfa_start():
    username = session.get('username')
    db = DatabaseManager()
    mfa_en, sec = db.get_mfa_state(username)
    if mfa_en:
        flash('MFA is already enabled.', 'info')
        return redirect(url_for('account_mfa'))
    if sec:
        flash('You already have a setup in progress. Scan the QR or cancel below.', 'info')
        return redirect(url_for('account_mfa'))
    new_secret = pyotp.random_base32()
    db.set_totp_secret(username, new_secret)
    flash('Scan the QR with your app, then enter a code to enable MFA.', 'success')
    return redirect(url_for('account_mfa'))


@app.route('/account/mfa/confirm', methods=['POST'])
@login_required
def account_mfa_confirm():
    username = session.get('username')
    code = (request.form.get('code') or '').replace(' ', '').strip()
    db = DatabaseManager()
    mfa_en, totp_secret = db.get_mfa_state(username)
    if mfa_en:
        return redirect(url_for('account_mfa'))
    if not totp_secret:
        flash('Start setup first.', 'error')
        return redirect(url_for('account_mfa'))
    if not code or not pyotp.TOTP(totp_secret).verify(code, valid_window=1):
        flash('Invalid code. Check your app clock and try again.', 'error')
        return redirect(url_for('account_mfa'))
    db.set_mfa_enabled(username, True)
    flash('Two-factor authentication is now enabled.', 'success')
    return redirect(url_for('account_mfa'))


@app.route('/account/mfa/cancel-setup', methods=['POST'])
@login_required
def account_mfa_cancel_setup():
    username = session.get('username')
    DatabaseManager().clear_mfa(username)
    flash('Authenticator setup cancelled.', 'info')
    return redirect(url_for('account_mfa'))


@app.route('/account/mfa/disable', methods=['POST'])
@login_required
def account_mfa_disable():
    username = session.get('username')
    DatabaseManager().clear_mfa(username)
    flash('Two-factor authentication has been turned off.', 'success')
    return redirect(url_for('account_mfa'))


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
                         valid_types=VALID_ENTRY_TYPES,
                         valid_groups=VALID_GROUPS)


@app.route('/api/entries', methods=['GET'])
@login_required
def get_entries():
    """API endpoint to get filtered entries."""
    username = session.get('username')
    pm = PasswordManager(username)
    
    search_query = request.args.get('search', '').lower()
    filter_type = request.args.get('type', 'all')
    filter_group = request.args.get('group', 'all')
    
    entries = pm.view_entries()
    
    # Apply filters
    if filter_type != 'all':
        entries = [e for e in entries if e[4] == filter_type]

    if filter_group != 'all' and filter_group in VALID_GROUPS:
        entries = [e for e in entries if (e[5] or 'other') == filter_group]
    
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
            'type': e[4],
            'group': e[5] if len(e) > 5 and e[5] else 'other'
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
    group_name = request.form.get('group', 'other').strip() or 'other'
    
    if not all([service, username_cred, password]):
        flash('All fields are required.', 'error')
        return redirect(url_for('dashboard'))
    
    if entry_type not in VALID_ENTRY_TYPES:
        flash('Invalid entry type.', 'error')
        return redirect(url_for('dashboard'))

    if group_name not in VALID_GROUPS:
        flash('Invalid group.', 'error')
        return redirect(url_for('dashboard'))
    
    success = pm.create_entry(service, username_cred, password, entry_type, group_name)
    
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
    group_name = request.form.get('group', 'other').strip() or 'other'
    
    if not all([service, username_cred, password]):
        flash('All fields are required.', 'error')
        return redirect(url_for('dashboard'))
    
    if entry_type not in VALID_ENTRY_TYPES:
        flash('Invalid entry type.', 'error')
        return redirect(url_for('dashboard'))

    if group_name not in VALID_GROUPS:
        flash('Invalid group.', 'error')
        return redirect(url_for('dashboard'))
    
    success = pm.update_entry(entry_id, service, username_cred, password, entry_type, group_name)
    
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
