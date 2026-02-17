from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
import os
import secrets


db = SQLAlchemy()


def _ensure_legacy_compatibility(app):
    """Ajoute les colonnes manquantes sur une base SQLite deja existante."""
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        if 'usagers' in tables:
            columns = {col['name'] for col in inspector.get_columns('usagers')}
            if 'password_hash' not in columns:
                db.session.execute(text('ALTER TABLE usagers ADD COLUMN password_hash VARCHAR(200)'))
                db.session.commit()


def init_app(app):
    """Initialise l'application avec la base de donnees"""
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bibliotheque.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    db.init_app(app)


def ensure_schema(app):
    """Cree les tables manquantes et applique les ajustements legacy."""
    with app.app_context():
        db.create_all()

    _ensure_legacy_compatibility(app)
