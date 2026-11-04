from app import create_app

application = create_app()

if __name__ == "__main__":
    # Database tables are managed through Flask-Migrate/Alembic.
    # Do not call db.create_all() here; it bypasses the team's migration history.
    application.run(host="127.0.0.1", port=5000, debug=True)
