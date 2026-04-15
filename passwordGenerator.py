import string
import secrets
'''
When generating a password, users will have the option to generate a random one,
This is where that would come from.
'''

alphabet = string.ascii_letters + string.digits + string.punctuation

def genRandomPassword():
    password = ''.join(secrets.choice(alphabet) for i in range(16))
    return password
    
