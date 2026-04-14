import hashlib
import secrets

def generate_hash(password):
    
    data = password.encode('utf-8')
    salt = secrets.token_bytes(16)
    
    hash = hashlib.pbkdf2_hmac('sha256', data, salt, 100000)
    
    print(hash.hex())
    
def verify_native(entered_password, stored_record):
    # Assume the first 32 characters are the salt, the rest is the hash
    salt = stored_record[:32]
    original_hash = stored_record[32:]
    
    # Re-hash the entered password using the EXACT same salt and iterations
    new_hash = hashlib.pbkdf2_hmac(
        'sha256', 
        entered_password.encode('utf-8'), 
        salt, 
        100000
    )
    
    # Use secrets.compare_digest to securely compare the two hashes
    return secrets.compare_digest(new_hash, original_hash)
password = input("Enter Password: ")

generate_hash(password)