import re


def validate_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email)


def validate_phone(phone):
    pattern = r"^[0-9]{10}$"
    return re.match(pattern, phone)


def validate_experience(exp):
    try:
        return float(exp) >= 0
    except:
        return False