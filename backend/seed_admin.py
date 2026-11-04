from app import create_app
from app.extensions import db
from app.models.user import User

app = create_app()

with app.app_context():
    name = input("Enter admin name: ").strip()
    email = input("Enter admin email: ").strip().lower()
    password = input("Enter admin password: ")

    if not name or not email or not password:
        raise SystemExit("Name, email and password are required.")
    if len(password) < 8:
        raise SystemExit("Password must contain at least 8 characters.")

    existing_admin = User.query.filter_by(email=email).first()
    if existing_admin:
        print("A user with this email already exists. No changes made.")
    else:
        admin = User(name=name, email=email, role="admin")
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print("Admin account created successfully.")
