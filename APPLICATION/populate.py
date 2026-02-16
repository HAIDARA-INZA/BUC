from app import app, db
from models import Ouvrage, Exemplaire, Usager
from datetime import datetime

with app.app_context():
    print("🗑️ Nettoyage de la base de données...")
    Exemplaire.query.delete()
    Ouvrage.query.delete()
    Usager.query.delete()
    db.session.commit()
    
    print("📚 Ajout des ouvrages de test...")
    
    # Liste d'ouvrages de test
    ouvrages_test = [
        {
            'titre': 'Le Petit Prince',
            'auteur': 'Antoine de Saint-Exupéry',
            'isbn': '9782070612758',
            'annee_publication': 1943,
            'categorie': 'Jeunesse',
            'exemplaires': 3
        },
        {
            'titre': '1984',
            'auteur': 'George Orwell',
            'isbn': '9782070368228',
            'annee_publication': 1949,
            'categorie': 'Science-fiction',
            'exemplaires': 2
        },
        {
            'titre': 'Les Misérables',
            'auteur': 'Victor Hugo',
            'isbn': '9782253088698',
            'annee_publication': 1862,
            'categorie': 'Roman',
            'exemplaires': 4
        },
        {
            'titre': 'Le Seigneur des Anneaux',
            'auteur': 'J.R.R. Tolkien',
            'isbn': '9782266282363',
            'annee_publication': 1954,
            'categorie': 'Fantasy',
            'exemplaires': 2
        },
        {
            'titre': 'Da Vinci Code',
            'auteur': 'Dan Brown',
            'isbn': '9782253154898',
            'annee_publication': 2003,
            'categorie': 'Policier',
            'exemplaires': 5
        },
        {
            'titre': 'Harry Potter à l\'école des sorciers',
            'auteur': 'J.K. Rowling',
            'isbn': '9782070643028',
            'annee_publication': 1997,
            'categorie': 'Fantasy',
            'exemplaires': 3
        },
        {
            'titre': 'Le Monde de Sophie',
            'auteur': 'Jostein Gaarder',
            'isbn': '9782253040917',
            'annee_publication': 1991,
            'categorie': 'Philosophie',
            'exemplaires': 2
        }
    ]
    
    for i, data in enumerate(ouvrages_test, 1):
        ouvrage = Ouvrage(
            titre=data['titre'],
            auteur=data['auteur'],
            isbn=data['isbn'],
            annee_publication=data['annee_publication'],
            categorie=data['categorie'],
            nombre_exemplaires=data['exemplaires']
        )
        db.session.add(ouvrage)
        db.session.flush()  # Pour obtenir l'ID
        
        # Créer les exemplaires
        for j in range(data['exemplaires']):
            exemplaire = Exemplaire(
                ouvrage_id=ouvrage.id,
                numero=f"{data['isbn']}-{j+1:03d}",
                etat='bon',
                date_acquisition=datetime.now()
            )
            db.session.add(exemplaire)
        
        print(f"  ✅ {i}. {data['titre']} - {data['exemplaires']} exemplaires")
    
    # Ajouter des usagers de test
    print("\n👥 Ajout des usagers de test...")
    
    usagers_test = [
        {'nom': 'Dupont', 'prenom': 'Jean', 'email': 'jean.dupont@email.com'},
        {'nom': 'Martin', 'prenom': 'Marie', 'email': 'marie.martin@email.com'},
        {'nom': 'Bernard', 'prenom': 'Pierre', 'email': 'pierre.bernard@email.com'},
        {'nom': 'Dubois', 'prenom': 'Sophie', 'email': 'sophie.dubois@email.com'},
    ]
    
    for i, data in enumerate(usagers_test, 1):
        usager = Usager(
            nom=data['nom'],
            prenom=data['prenom'],
            email=data['email'],
            telephone=f"01 23 45 67 {80+i:02d}",
            statut='actif',
            date_inscription=datetime.now()
        )
        db.session.add(usager)
        print(f"  ✅ {i}. {data['prenom']} {data['nom']}")
    
    db.session.commit()
    print("\n✨ Base de données initialisée avec succès !")
    print(f"   Total : {len(ouvrages_test)} ouvrages")
    print(f"   Total : {len(usagers_test)} usagers")