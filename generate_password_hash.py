"""
Generate password hash for admin login
Usage: python generate_password_hash.py
"""
import hashlib
import getpass

def hash_password(password: str) -> str:
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

if __name__ == "__main__":
    print("="*70)
    print("ADMIN PASSWORD HASH GENERATOR")
    print("="*70)
    print()
    print("This will generate a password hash for your admin account:")
    print("Email: josephllemieux@gmail.com")
    print()

    # Get password securely (won't show on screen)
    password = getpass.getpass("Enter your desired password: ")
    password_confirm = getpass.getpass("Confirm password: ")

    if password != password_confirm:
        print("\n❌ Passwords don't match! Please try again.")
        exit(1)

    if len(password) < 8:
        print("\n⚠️  Warning: Password is less than 8 characters. Consider using a stronger password.")

    # Generate hash
    password_hash = hash_password(password)

    print("\n" + "="*70)
    print("✅ PASSWORD HASH GENERATED")
    print("="*70)
    print()
    print(f"Hash: {password_hash}")
    print()
    print("Set this in your Railway environment variables:")
    print()
    print(f"ADMIN_PASSWORD_HASH={password_hash}")
    print()
    print("Steps to deploy:")
    print("1. Go to Railway dashboard")
    print("2. Select your backend service")
    print("3. Go to Variables tab")
    print("4. Add: ADMIN_PASSWORD_HASH = <hash above>")
    print("5. Also add: JWT_SECRET_KEY = <random secret key>")
    print("6. Save and redeploy")
    print()
    print("="*70)
