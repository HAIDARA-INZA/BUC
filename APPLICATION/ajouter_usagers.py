#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour ajouter des usagers de test à la bibliothèque
Exécutez: python ajouter_usagers.py
"""

from app import app, db
from models import Usager
from datetime import datetime

def ajouter_usagers_test():
    """Ajoute des usagers de test dans la base de données"""
    
    with app.app_context():
        print("=" * 60)
        print("👥 AJOUT D'USAGERS DE TEST")
        print("=" * 60)
        
        # Liste des usagers à ajouter
        usagers_test = [
            {
                'nom': 'Dupont',
                'prenom': 'Jean',
                'email': 'jean.dupont@email.com',
                'telephone': '0123456789',
                'adresse': '12 rue de Paris, 75001 Paris',
                'statut': 'actif'
            },
            {
                'nom': 'Martin',
                'prenom': 'Marie',
                'email': 'marie.martin@email.com',
                'telephone': '0234567890',
                'adresse': '25 avenue des Fleurs, 69001 Lyon',
                'statut': 'actif'
            },
            {
                'nom': 'Bernard',
                'prenom': 'Pierre',
                'email': 'pierre.bernard@email.com',
                'telephone': '0345678901',
                'adresse': '8 rue de la Gare, 33000 Bordeaux',
                'statut': 'actif'
            },
            {
                'nom': 'Dubois',
                'prenom': 'Sophie',
                'email': 'sophie.dubois@email.com',
                'telephone': '0456789012',
                'adresse': '15 boulevard Victor Hugo, 13001 Marseille',
                'statut': 'actif'
            },
            {
                'nom': 'Petit',
                'prenom': 'Thomas',
                'email': 'thomas.petit@email.com',
                'telephone': '0567890123',
                'adresse': '3 place de la Mairie, 44000 Nantes',
                'statut': 'actif'
            },
            {
                'nom': 'Robert',
                'prenom': 'Julie',
                'email': 'julie.robert@email.com',
                'telephone': '0678901234',
                'adresse': '42 rue Nationale, 59000 Lille',
                'statut': 'actif'
            },
            {
                'nom': 'Richard',
                'prenom': 'Nicolas',
                'email': 'nicolas.richard@email.com',
                'telephone': '0789012345',
                'adresse': '7 avenue Jean Jaurès, 31000 Toulouse',
                'statut': 'suspendu'  # Usager suspendu pour test
            },
            {
                'nom': 'Durand',
                'prenom': 'Isabelle',
                'email': 'isabelle.durand@email.com',
                'telephone': '0890123456',
                'adresse': '19 rue de la République, 67000 Strasbourg',
                'statut': 'actif'
            }
        ]
        
        compteur = 0
        deja_existants = 0
        
        for usager_data in usagers_test:
            # Vérifier si l'usager existe déjà
            existant = Usager.query.filter_by(email=usager_data['email']).first()
            
            if not existant:
                usager = Usager(
                    nom=usager_data['nom'],
                    prenom=usager_data['prenom'],
                    email=usager_data['email'],
                    telephone=usager_data['telephone'],
                    adresse=usager_data['adresse'],
                    statut=usager_data['statut'],
                    date_inscription=datetime.now()
                )
                
                db.session.add(usager)
                compteur += 1
                print(f"  ✅ [{compteur}] Ajouté : {usager_data['prenom']} {usager_data['nom']} ({usager_data['statut']})")
            else:
                deja_existants += 1
                print(f"  ⏭️  Déjà existant : {usager_data['prenom']} {usager_data['nom']}")
        
        # Sauvegarder
        db.session.commit()
        
        # Afficher le résumé
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ")
        print("=" * 60)
        print(f"  👤 Nouveaux usagers ajoutés : {compteur}")
        print(f"  👥 Usagers déjà existants   : {deja_existants}")
        print(f"  📊 Total dans la base       : {Usager.query.count()}")
        print(f"  ✅ Usagers actifs           : {Usager.query.filter_by(statut='actif').count()}")
        print(f"  ⚠️  Usagers suspendus        : {Usager.query.filter_by(statut='suspendu').count()}")
        print("\n✨ Terminé avec succès !")
        print("=" * 60)

if __name__ == '__main__':
    ajouter_usagers_test()