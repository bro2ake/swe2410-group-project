# Streamlit Password Manager UI - Setup Guide

## 📋 What Was Created

A complete Streamlit-based UI (`ui.py`) that integrates with your existing backend:
- ✅ Login/Register authentication
- ✅ Dashboard with vault display
- ✅ Per-entry password masking with individual toggles
- ✅ Search & filter functionality
- ✅ Full CRUD operations (Add, View, Edit, Delete)
- ✅ Vault health analytics
- ✅ Password strength indicator & generator

## ⚠️ Python Version Requirement

**IMPORTANT:** The current Python 3.15 environment cannot install Streamlit due to missing pre-built numpy wheels.

**Solution:** Use Python 3.11 or 3.12 instead.

### Option A: Install Python 3.11 or 3.12
1. Download Python 3.11 or 3.12 from https://www.python.org/downloads/
2. Make sure to add Python to PATH during installation
3. Create a virtual environment:
   ```bash
   python3.11 -m venv venv
   ```
4. Activate the virtual environment:
   - **Windows:** `venv\Scripts\activate`
   - **Mac/Linux:** `source venv/bin/activate`
5. Install dependencies:
   ```bash
   pip install streamlit
   ```

### Option B: Use uv with Python 3.11
```bash
uv venv --python 3.11 venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
uv pip install streamlit
```

## 📦 Dependencies

The `ui.py` file requires:
- **streamlit** (1.31.1 or newer) — Main UI framework
- **numpy** — Required by streamlit (pre-built wheel for Python 3.11+)
- **pandas** — May be required by streamlit
- **pillow** — Image support
- **altair** — Charting library
- **click** — CLI support

All other modules (loginPage, createAccount, passwordManager, etc.) are your existing backend and don't require installation.

## 🚀 Running the Streamlit App

Once Streamlit is installed:

```bash
streamlit run ui.py
```

This will:
1. Launch a local Streamlit server (default: http://localhost:8501)
2. Open the app in your browser automatically
3. Start with the login page

## 📝 Testing the App

### Create a Test Account
1. Click "Create Account"
2. Email: test@example.com
3. Password: TestPassword123! (must be Strong)
4. Confirm password
5. Click "Create Account"

### Log In
1. Email: test@example.com
2. Password: TestPassword123!
3. Click "Login"

### Test Vault Features
1. **Add Entry**: Expand "➕ Add New Entry", fill in fields, click "Add Entry"
2. **View Entries**: All entries shown in table below
3. **Mask/Reveal**: Click "Reveal" button next to password to toggle visibility
4. **Search**: Type service name in search box to filter
5. **Filter**: Use dropdown to filter by "password" or "api_key" type
6. **Edit**: Click "✏️" to edit an entry
7. **Delete**: Click "🗑️" to delete an entry with confirmation
8. **Logout**: Click "Logout" button in top right

## 🔧 Backend Integration Points

The UI calls these backend functions directly (no duplication):

| Function | Called From | Purpose |
|----------|------------|---------|
| `LoginPage.login()` | Login form | Authenticate user |
| `CreateAccount.create_account()` | Register form | Create new account |
| `PasswordManager.create_entry()` | Add form | Add new credential |
| `PasswordManager.view_entries()` | Dashboard | Display all entries |
| `PasswordManager.update_entry()` | Edit modal | Update credential |
| `PasswordManager.delete_entry()` | Delete button | Remove credential |
| `PasswordManager.vault_health()` | Dashboard metrics | Get vault statistics |

## 📊 Dashboard Features

### Metrics (Top of dashboard)
- **Total Entries**: Count of all stored credentials
- **Weak Passwords**: Count of passwords with weak strength
- **Reused Passwords**: Count of duplicate passwords
- **API Keys**: Count of API key entries

### Search & Filter
- **Search box**: Filter by service name or username (real-time)
- **Type dropdown**: Filter by "password" or "api_key"

### Vault Table
Each entry shows:
- Service name & type icon (🔐 Password / 🔑 API Key)
- Username/email
- Password (masked as •••••••• by default)
- **Reveal** button: Toggle to show/hide password
- **✏️** button: Edit entry
- **🗑️** button: Delete entry with confirmation

### Add New Entry
Expandable form with:
- Service name
- Entry type selector (Password/API Key)
- Username/email
- Password input
- **Generate** button: Creates random secure password
- Password strength indicator

## 🐛 Known Issues & Solutions

### Issue 1: "ModuleNotFoundError: No module named 'streamlit'"
**Solution**: Install streamlit in the correct Python version (3.11 or 3.12)

### Issue 2: "No such table: users" error on first run
**Solution**: This is expected on first run. The database creates tables automatically. Create a test account and try again.

### Issue 3: VALID_ENTRY_TYPES not defined
**Solution**: Already fixed in `passwordManager.py` (added definition at top)

### Issue 4: "Streamlit requires Python 3.7+"
**Solution**: You need Python 3.11+. Python 3.15 is too new for wheel compatibility.

## 🎯 File Structure

```
swe2410-group-project/
├── ui.py                    # ← NEW: Streamlit UI (the file you'll run)
├── loginPage.py             # Backend: Authentication
├── createAccount.py         # Backend: Registration
├── passwordManager.py       # Backend: CRUD + vault health (FIXED: added VALID_ENTRY_TYPES)
├── databaseConnect.py       # Backend: Database queries
├── encryptionEngine.py      # Backend: Hashing/encryption
├── passwordGenerator.py     # Backend: Password strength & generation
├── user_data.db            # Auto-created on first run: SQLite database
└── SETUP_STREAMLIT.md      # ← NEW: This file
```

## ⚙️ Environment Variables (Optional)

For production deployments, set:
```bash
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_ADDRESS=localhost
```

## 🔒 Security Notes

1. **Passwords masked by default** — Click "Reveal" to see (per-entry)
2. **Session-based login** — Clears when Streamlit app restarts
3. **No plaintext storage** — All passwords hashed with PBKDF2-HMAC-SHA256
4. **Secure comparison** — Uses `secrets.compare_digest()` for timing-safe checks

## 📚 Additional Resources

- Streamlit Docs: https://docs.streamlit.io/
- Streamlit Components: https://docs.streamlit.io/library/api-reference/widgets
- Session State: https://docs.streamlit.io/library/api-reference/session-state

## 💡 Next Steps

1. **Install Python 3.11 or 3.12** (required)
2. **Create virtual environment** (recommended)
3. **Install Streamlit**: `pip install streamlit`
4. **Run UI**: `streamlit run ui.py`
5. **Test all features** as described in "Testing the App" section

---

**Issues?** Check that:
- [ ] Python version is 3.11 or 3.12 (not 3.15)
- [ ] Virtual environment is activated
- [ ] Streamlit is installed: `pip list | grep streamlit`
- [ ] Database file has been created: `user_data.db` exists
- [ ] Backend files are in same directory as `ui.py`
