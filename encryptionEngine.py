import hashlib
import secrets

def generate_hash(password):
    
    data = password.encode('utf-8')
    salt = secrets.token_bytes(16)
    
    hash = hashlib.pbkdf2_hmac('sha256', data, salt, 100000)
    
    return (salt + hash).hex()
    
def verify_native(entered_password, stored_record):
    record_bytes = bytes.fromhex(stored_record)
    salt = record_bytes[:16]
    original_hash = record_bytes[16:]
    
    # Re-hash the entered password using the EXACT same salt and iterations
    new_hash = hashlib.pbkdf2_hmac(
        'sha256', 
        entered_password.encode('utf-8'), 
        salt, 
        100000
    )
    
    # Use secrets.compare_digest to securely compare the two hashes
    return secrets.compare_digest(new_hash, original_hash)