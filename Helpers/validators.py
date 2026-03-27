class ValidationError(ValueError):
    pass


def validate_email(raw: str) -> str:
    email = raw.strip().lower()
    if not email:
        raise ValidationError("Email is required.")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValidationError("Please enter a valid email address.")
    return email


def validate_password(password: str) -> str:
    if len(password) < 8:
        raise ValidationError("Password must be at least 8 characters.")
    return password