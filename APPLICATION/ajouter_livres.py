#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script pour ajouter des livres de test à la bibliothèque

"""

from app import app, db
from models import Ouvrage, Exemplaire
from datetime import datetime

def ajouter_livres_test():
    """Ajoute des livres dans la base de données"""
    
    with app.app_context():
        print("=" * 60)
        print("📚 AJOUT DE LIVRES DE TEST")
        print("=" * 60)
        
        # Liste des livres à ajouter
        livres_test = [
            {
                'titre': 'Le Petit Prince',
                'auteur': 'Antoine de Saint-Exupéry',
                'isbn': '9782070612758',
                'annee_publication': 1943,
                'categorie': 'Jeunesse',
                'editeur': 'Gallimard',
                'description': 'Le célèbre conte philosophique sur l\'amitié et le sens de la vie.',
                'exemplaires': 3
            },
            {
                'titre': '1984',
                'auteur': 'George Orwell',
                'isbn': '9782070368228',
                'annee_publication': 1949,
                'categorie': 'Science-fiction',
                'editeur': 'Gallimard',
                'description': 'Dans une société totalitaire, Winston tente de résister au Parti unique.',
                'exemplaires': 2
            },
            {
                'titre': 'Les Misérables',
                'auteur': 'Victor Hugo',
                'isbn': '9782253088698',
                'annee_publication': 1862,
                'categorie': 'Roman',
                'editeur': 'Pocket',
                'description': 'L\'histoire de Jean Valjean, ancien bagnard qui tente de se racheter.',
                'exemplaires': 4
            },
            {
                'titre': 'Harry Potter à l\'école des sorciers',
                'auteur': 'J.K. Rowling',
                'isbn': '9782070643028',
                'annee_publication': 1997,
                'categorie': 'Fantasy',
                'editeur': 'Gallimard Jeunesse',
                'description': 'Premier tome des aventures du jeune sorcier Harry Potter.',
                'exemplaires': 3
            },
            {
                'titre': 'Da Vinci Code',
                'auteur': 'Dan Brown',
                'isbn': '9782253154898',
                'annee_publication': 2003,
                'categorie': 'Policier',
                'editeur': 'Pocket',
                'description': 'Un thriller mystérieux mêlant art, religion et histoire.',
                'exemplaires': 2
            },
            {
                'titre': 'Le Seigneur des Anneaux - La Communauté de l\'Anneau',
                'auteur': 'J.R.R. Tolkien',
                'isbn': '9782266282363',
                'annee_publication': 1954,
                'categorie': 'Fantasy',
                'editeur': 'Pocket',
                'description': 'Premier tome de la célèbre trilogie fantastique.',
                'exemplaires': 2
            },
            {
                'titre': 'L\'Étranger',
                'auteur': 'Albert Camus',
                'isbn': '9782070360024',
                'annee_publication': 1942,
                'categorie': 'Roman',
                'editeur': 'Gallimard',
                'description': 'Meursault, un homme indifférent, commet un meurtre sans raison.',
                'exemplaires': 2
            },
            {
                'titre': 'Le Rouge et le Noir',
                'auteur': 'Stendhal',
                'isbn': '9782253006654',
                'annee_publication': 1830,
                'categorie': 'Roman',
                'editeur': 'Pocket',
                'description': 'L\'ascension et la chute de Julien Sorel, jeune ambitieux.',
                'exemplaires': 1
            },
            {
                'titre': 'Vingt mille lieues sous les mers',
                'auteur': 'Jules Verne',
                'isbn': '9782013221830',
                'annee_publication': 1870,
                'categorie': 'Aventure',
                'editeur': 'Hachette',
                'description': 'Les aventures du Capitaine Nemo à bord du Nautilus.',
                'exemplaires': 2
            },
            {
                'titre': 'Madame Bovary',
                'auteur': 'Gustave Flaubert',
                'isbn': '9782070413119',
                'annee_publication': 1857,
                'categorie': 'Roman',
                'editeur': 'Gallimard',
                'description': 'Emma Bovary, femme romantique, rêve d\'une autre vie.',
                'exemplaires': 2
            }
        ]
        
        compteur = 0
        deja_existants = 0
        
        for livre in livres_test:
            # Vérifier si le livre existe déjà par ISBN ou titre
            existant = None
            if livre['isbn']:
                existant = Ouvrage.query.filter_by(isbn=livre['isbn']).first()
            
            if not existant:
                existant = Ouvrage.query.filter_by(
                    titre=livre['titre'], 
                    auteur=livre['auteur']
                ).first()
            
            if not existant:
                # Créer le nouvel ouvrage
                ouvrage = Ouvrage(
                    titre=livre['titre'],
                    auteur=livre['auteur'],
                    isbn=livre['isbn'],
                    annee_publication=livre['annee_publication'],
                    categorie=livre['categorie'],
                    editeur=livre['editeur'],
                    description=livre['description'],
                    nombre_exemplaires=livre['exemplaires']
                )
                
                db.session.add(ouvrage)
                db.session.flush()  # Pour obtenir l'ID
                
                # Créer les exemplaires
                for i in range(livre['exemplaires']):
                    numero = f"{livre['isbn']}-{i+1:03d}" if livre['isbn'] else f"{ouvrage.id}-{i+1:03d}"
                    
                    exemplaire = Exemplaire(
                        ouvrage_id=ouvrage.id,
                        numero=numero,
                        etat='bon',
                        date_acquisition=datetime.now()
                    )
                    db.session.add(exemplaire)
                
                compteur += 1
                print(f"  ✅ [{compteur}] Ajouté : {livre['titre']} ({livre['exemplaires']} ex.)")
            else:
                deja_existants += 1
                print(f"  ⏭️  Déjà existant : {livre['titre']}")
        
        # Sauvegarder
        db.session.commit()
        
        # Afficher le résumé
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ")
        print("=" * 60)
        print(f"  📚 Nouveaux livres ajoutés : {compteur}")
        print(f"  📖 Livres déjà existants   : {deja_existants}")
        print(f"  📈 Total dans la base      : {Ouvrage.query.count()}")
        print(f"  📋 Total exemplaires       : {Exemplaire.query.count()}")
        print("\n✨ Terminé avec succès !")
        print("=" * 60)

if __name__ == '__main__':
    ajouter_livres_test()