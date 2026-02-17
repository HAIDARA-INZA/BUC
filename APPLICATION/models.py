from database import db
from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class Usager(db.Model):
    """Modele pour les usagers de la bibliotheque"""
    __tablename__ = 'usagers'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telephone = db.Column(db.String(20))
    adresse = db.Column(db.Text)
    password_hash = db.Column(db.String(200))
    date_inscription = db.Column(db.DateTime, default=datetime.utcnow)
    statut = db.Column(db.String(20), default='actif')  # actif, suspendu, inactif

    # Relations
    emprunts = db.relationship('Emprunt', backref='usager', lazy=True)
    reservations = db.relationship('Reservation', backref='usager', lazy=True)
    demandes = db.relationship('DemandeUsager', backref='usager', lazy=True)

    def __repr__(self):
        return f'<Usager {self.prenom} {self.nom}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return bool(self.password_hash) and check_password_hash(self.password_hash, password)

    def peut_emprunter(self):
        """Verifie si l'usager peut emprunter un livre"""
        if self.statut != 'actif':
            return False, 'Compte non actif'

        emprunts_actifs = [e for e in self.emprunts if e.statut == 'en_cours']
        if len(emprunts_actifs) >= 5:  # Limite de 5 emprunts simultanes
            return False, 'Limite d emprunts atteinte'

        return True, 'OK'


class Ouvrage(db.Model):
    """Modele pour les ouvrages (livres)"""
    __tablename__ = 'ouvrages'

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    auteur = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(20), unique=True)
    annee_publication = db.Column(db.Integer)
    editeur = db.Column(db.String(100))
    categorie = db.Column(db.String(50))
    description = db.Column(db.Text)
    nombre_exemplaires = db.Column(db.Integer, default=1)
    date_ajout = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    exemplaires = db.relationship('Exemplaire', backref='ouvrage', lazy=True)
    reservations = db.relationship('Reservation', backref='ouvrage', lazy=True)
    demandes = db.relationship('DemandeUsager', backref='ouvrage', lazy=True)

    def __repr__(self):
        return f'<Ouvrage {self.titre}>'

    def exemplaires_disponibles(self):
        """Retourne le nombre d'exemplaires disponibles"""
        total = self.nombre_exemplaires
        empruntes = sum(
            1 for e in self.exemplaires if any(emp.statut == 'en_cours' for emp in e.emprunts)
        )
        return total - empruntes

    def est_disponible(self):
        """Verifie si au moins un exemplaire est disponible"""
        return self.exemplaires_disponibles() > 0


class Exemplaire(db.Model):
    """Modele pour les exemplaires individuels d'un ouvrage"""
    __tablename__ = 'exemplaires'

    id = db.Column(db.Integer, primary_key=True)
    ouvrage_id = db.Column(db.Integer, db.ForeignKey('ouvrages.id'), nullable=False)
    numero = db.Column(db.String(50), nullable=False)  # Numero d'inventaire
    etat = db.Column(db.String(20), default='bon')  # bon, abime, perdu
    date_acquisition = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    emprunts = db.relationship('Emprunt', backref='exemplaire', lazy=True)

    def __repr__(self):
        return f'<Exemplaire {self.numero} de {self.ouvrage.titre}>'

    def est_disponible(self):
        """Verifie si cet exemplaire est disponible"""
        emprunts_actifs = [e for e in self.emprunts if e.statut == 'en_cours']
        return len(emprunts_actifs) == 0


class Emprunt(db.Model):
    """Modele pour les emprunts"""
    __tablename__ = 'emprunts'

    id = db.Column(db.Integer, primary_key=True)
    usager_id = db.Column(db.Integer, db.ForeignKey('usagers.id'), nullable=False)
    exemplaire_id = db.Column(db.Integer, db.ForeignKey('exemplaires.id'), nullable=False)
    date_emprunt = db.Column(db.DateTime, default=datetime.utcnow)
    date_retour_prevue = db.Column(db.DateTime)
    date_retour_reelle = db.Column(db.DateTime)
    statut = db.Column(db.String(20), default='en_cours')  # en_cours, retourne, en_retard
    prolongations = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<Emprunt {self.id}>'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.date_retour_prevue:
            self.date_retour_prevue = datetime.utcnow() + timedelta(days=21)  # 3 semaines

    def est_en_retard(self):
        """Verifie si l'emprunt est en retard"""
        if self.statut in ('retourne', 'retourn\u00e9'):
            return False
        return datetime.utcnow() > self.date_retour_prevue

    def peut_prolonger(self):
        """Verifie si l'emprunt peut etre prolonge"""
        if self.prolongations >= 2:  # Maximum 2 prolongations
            return False, 'Nombre maximum de prolongations atteint'
        if self.est_en_retard():
            return False, 'Emprunt en retard'
        return True, 'OK'

    def prolonger(self):
        """Prolonge l'emprunt de 7 jours"""
        can_prolong, message = self.peut_prolonger()
        if can_prolong:
            self.date_retour_prevue += timedelta(days=7)
            self.prolongations += 1
            return True, 'Emprunt prolonge'
        return False, message


class Reservation(db.Model):
    """Modele pour les reservations"""
    __tablename__ = 'reservations'

    id = db.Column(db.Integer, primary_key=True)
    usager_id = db.Column(db.Integer, db.ForeignKey('usagers.id'), nullable=False)
    ouvrage_id = db.Column(db.Integer, db.ForeignKey('ouvrages.id'), nullable=False)
    date_reservation = db.Column(db.DateTime, default=datetime.utcnow)
    date_expiration = db.Column(db.DateTime)
    statut = db.Column(db.String(20), default='active')  # active, annulee, honoree
    priorite = db.Column(db.Integer)

    def __repr__(self):
        return f'<Reservation {self.id}>'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.date_expiration:
            self.date_expiration = datetime.utcnow() + timedelta(days=7)  # 1 semaine


class DemandeUsager(db.Model):
    """Demandes envoyees par l'usager et traitees par l'admin"""
    __tablename__ = 'demandes_usager'

    id = db.Column(db.Integer, primary_key=True)
    usager_id = db.Column(db.Integer, db.ForeignKey('usagers.id'), nullable=False)
    ouvrage_id = db.Column(db.Integer, db.ForeignKey('ouvrages.id'), nullable=False)
    type_demande = db.Column(db.String(20), nullable=False)  # emprunt, reservation
    statut = db.Column(db.String(20), default='en_attente')  # en_attente, acceptee, refusee
    commentaire = db.Column(db.Text)
    commentaire_admin = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_traitement = db.Column(db.DateTime)
    bibliothecaire_id = db.Column(db.Integer, db.ForeignKey('bibliothecaires.id'))

    bibliothecaire = db.relationship('Bibliothecaire', backref='demandes_traitees', lazy=True)

    def __repr__(self):
        return f'<DemandeUsager {self.id} {self.type_demande}>'


class Bibliothecaire(db.Model, UserMixin):
    """Modele pour les bibliothecaires (administrateurs)"""
    __tablename__ = 'bibliothecaires'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    login = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        """Hash le mot de passe"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifie le mot de passe"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<Bibliothecaire {self.login}>'

