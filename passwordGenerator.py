import string
import secrets
'''
When generating a password, users will have the option to generate a random one,
This is where that would come from.
'''

def genRandomPassword(length=16, use_symbols=True, use_digits=True):
    alphabet = string.ascii_letters

    if use_digits:
        alphabet += string.digits
    if use_symbols:
        alphabet += string.punctuation

    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password

def passwordStrength(password):
    score = 0

    if len(password) >= 8:
        score += 1
    if len(password) >= 14:
        score += 1
    if any(char.isdigit() for char in password):
        score += 1
    if any(char.isupper() for char in password):
        score += 1
    if any(char.islower() for char in password):
        score += 1
    if any(not char.isalnum() for char in password):
        score += 1

    if score <= 2:
        return "❌ Weak"
    elif score <= 4:
        return "⚠️ Medium"
    return "✅ Strong"