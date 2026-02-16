from models import *
from database import db
from datetime import datetime, timedelta
from sqlalchemy import and_, or_

class GestionBibliotheque:
    """Contrôleur principal pour la gestion de la bibliothèque"""
    
    @staticmethod
    def ajouter_ouvrage(titre, auteur, isbn=None, annee=None, editeur=None, 
                       categorie=None, description=None, nb_exemplaires=1):
        """Ajoute un nouvel ouvrage à la bibliothèque"""
        ouvrage = Ouvrage(
            titre=titre,
            auteur=auteur,
            isbn=isbn,
            annee_publication=annee,
            editeur=editeur,
            categorie=categorie,
            description=description,
            nombre_exemplaires=nb_exemplaires
        )
        
        db.session.add(ouvrage)
        db.session.commit()
        
        # Créer les exemplaires
        for i in range(nb_exemplaires):
            exemplaire = Exemplaire(
                ouvrage_id=ouvrage.id,
                numero=f"{isbn or ouvrage.id}-{i+1:03d}",
                etat='bon'
            )
            db.session.add(exemplaire)
        
        db.session.commit()
        return ouvrage
    
    @staticmethod
    def inscrire_usager(nom, prenom, email, telephone=None, adresse=None):
        """Inscrit un nouvel usager"""
        usager = Usager(
            nom=nom,
            prenom=prenom,
            email=email,
            telephone=telephone,
            adresse=adresse,
            statut='actif'
        )
        
        db.session.add(usager)
        db.session.commit()
        return usager
    
    @staticmethod
    def emprunter_ouvrage(usager_id, ouvrage_id):
        """Enregistre un nouvel emprunt"""
        # Vérifier si l'usager peut emprunter
        usager = db.session.get(Usager, usager_id)
        peut_emprunter, message = usager.peut_emprunter()
        if not peut_emprunter:
            return False, message
        
        # Trouver un exemplaire disponible
        ouvrage = db.session.get(Ouvrage, ouvrage_id)
        if not ouvrage.est_disponible():
            return False, "Aucun exemplaire disponible"
        
        exemplaire_dispo = None
        for exemplaire in ouvrage.exemplaires:
            if exemplaire.est_disponible():
                exemplaire_dispo = exemplaire
                break
        
        if not exemplaire_dispo:
            return False, "Erreur: aucun exemplaire disponible trouvé"
        
        # Créer l'emprunt
        emprunt = Emprunt(
            usager_id=usager_id,
            exemplaire_id=exemplaire_dispo.id
        )
        
        db.session.add(emprunt)
        db.session.commit()
        return True, "Emprunt enregistré avec succès"
    
    @staticmethod
    def retourner_emprunt(emprunt_id):
        """Enregistre le retour d'un ouvrage"""
        emprunt = db.session.get(Emprunt, emprunt_id)
        if not emprunt:
            return False, "Emprunt non trouvé"
        
        emprunt.date_retour_reelle = datetime.utcnow()
        emprunt.statut = 'retourné'
        
        # Vérifier s'il y a des réservations pour cet ouvrage
        reservations = Reservation.query.filter_by(
            ouvrage_id=emprunt.exemplaire.ouvrage_id,
            statut='active'
        ).order_by(Reservation.priorite, Reservation.date_reservation).all()
        
        if reservations:
            # Notifier le premier usager en liste d'attente
            reservation = reservations[0]
            reservation.statut = 'honorée'
            # Ici, on pourrait envoyer un email de notification
        
        db.session.commit()
        return True, "Retour enregistré avec succès"
    
    @staticmethod
    def reserver_ouvrage(usager_id, ouvrage_id):
        """Crée une réservation pour un ouvrage"""
        usager = db.session.get(Usager, usager_id)
        ouvrage = db.session.get(Ouvrage, ouvrage_id)
        
        if not usager or not ouvrage:
            return False, "Usager ou ouvrage non trouvé"
        
        # Vérifier si l'usager a déjà une réservation active pour cet ouvrage
        reservation_existante = Reservation.query.filter_by(
            usager_id=usager_id,
            ouvrage_id=ouvrage_id,
            statut='active'
        ).first()
        
        if reservation_existante:
            return False, "Vous avez déjà une réservation active pour cet ouvrage"
        
        # Calculer la priorité
        reservations_actives = Reservation.query.filter_by(
            ouvrage_id=ouvrage_id,
            statut='active'
        ).count()
        
        reservation = Reservation(
            usager_id=usager_id,
            ouvrage_id=ouvrage_id,
            priorite=reservations_actives + 1
        )
        
        db.session.add(reservation)
        db.session.commit()
        return True, "Réservation créée avec succès"
    
    @staticmethod
    def get_statistiques():
        """Retourne des statistiques sur la bibliothèque"""
        stats = {
            'total_ouvrages': Ouvrage.query.count(),
            'total_exemplaires': Exemplaire.query.count(),
            'total_usagers': Usager.query.count(),
            'emprunts_en_cours': Emprunt.query.filter_by(statut='en_cours').count(),
            'emprunts_en_retard': len([e for e in Emprunt.query.filter_by(statut='en_cours').all() 
                                      if e.est_en_retard()]),
            'reservations_actives': Reservation.query.filter_by(statut='active').count()
        }
        return stats