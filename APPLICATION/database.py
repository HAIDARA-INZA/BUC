from flask_sqlalchemy import SQLAlchemy
import os
import secrets

db = SQLAlchemy()

def init_app(app):
    """Initialise l'application avec la base de données"""
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bibliotheque.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    db.init_app(app)
    
    with app.app_context():
        # Créer toutes les tables
        db.create_all()