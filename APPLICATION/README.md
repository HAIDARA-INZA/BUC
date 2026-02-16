# 📚 Système de Gestion de Bibliothèque

Un système complet de gestion de bibliothèque développé avec Flask et SQLAlchemy.

## 🔧 Installation et Configuration

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. **Clonez ou accédez au répertoire du projet**
   ```bash
   cd APPLICATION
   ```

2. **Créez un environnement virtuel (recommandé)**
   ```bash
   python -m venv venv
   ```

3. **Activez l'environnement virtuel**
   - Sous Windows :
     ```bash
     venv\Scripts\activate
     ```
   - Sous macOS/Linux :
     ```bash
     source venv/bin/activate
     ```

4. **Installez les dépendances**
   ```bash
   pip install -r requirements.txt
   ```

5. **Initialisez la base de données**
   ```bash
   python populate.py
   ```
   ou
   ```bash
   python ajouter_livres.py
   python ajouter_usagers.py
   ```

6. **Lancez l'application**
   ```bash
   python app.py
   ```

   L'application sera disponible à `http://localhost:5000`

## 🔐 Identifiants par défaut

- **Identifiant :** `admin`
- **Mot de passe :** `admin123`

⚠️ **Important** : Changez le mot de passe après la première connexion !

## 📋 Fonctionnalités

### Pour les bibliothécaires (Admin)
- ✅ Gestion des ouvrages (ajout, modification, suppression)
- ✅ Gestion des usagers (création, modification, statut)
- ✅ Gestion des emprunts et retours
- ✅ Gestion des réservations
- ✅ Tableau de bord avec statistiques
- ✅ Recherche et filtrage avancés

### Pour les usagers
- ✅ Consultation du catalogue
- ✅ Recherche dans les ouvrages
- ✅ Affichage de la disponibilité

## 🗂️ Structure du projet

```
APPLICATION/
├── app.py                 # Application Flask principale
├── models.py              # Modèles de données (Usager, Ouvrage, Emprunt, etc.)
├── database.py            # Configuration de la base de données
├── controllers.py         # Contrôleurs/Services métier
├── requirements.txt       # Dépendances Python
├── populate.py            # Script pour initialiser la base de données
├── ajouter_livres.py      # Script pour ajouter des livres de test
├── ajouter_usagers.py     # Script pour ajouter des usagers de test
├── templates/             # Templates HTML
│   ├── base.html         # Template de base
│   ├── index.html        # Page d'accueil
│   ├── dashboard.html    # Tableau de bord
│   ├── login.html        # Page de connexion
│   ├── ouvrages.html     # Liste des ouvrages
│   ├── usagers.html      # Liste des usagers
│   ├── emprunts.html     # Liste des emprunts
│   ├── reservations.html # Liste des réservations
│   └── ...
└── static/               # Fichiers statiques (CSS, JS)
    ├── css/
    └── js/
```

## 📊 Modèles de données

### Usager
- id, nom, prénom, email, téléphone, adresse
- statut (actif, suspendu, inactif)
- date_inscription

### Ouvrage
- id, titre, auteur, isbn, année_publication
- éditeur, catégorie, description
- nombre_exemplaires

### Exemplaire
- id, ouvrage_id, numéro d'inventaire
- état (bon, abîmé, perdu)
- date_acquisition

### Emprunt
- id, usager_id, exemplaire_id
- date_emprunt, date_retour_prévue, date_retour_réelle
- statut (en_cours, retourné, en_retard)
- prolongations

### Réservation
- id, usager_id, ouvrage_id
- date_réservation, date_expiration
- statut (active, annulée, honorée)
- priorité

### Bibliothécaire
- id, nom, prénom, login
- password_hash

## 🐛 Problèmes corrigés

1. ✅ **Imports manquants** : Ajout de `db` dans `controllers.py`
2. ✅ **Erreurs SQLAlchemy** : Correction de `order_by()` avec des chaînes impropiées
3. ✅ **Sécurité** : Génération automatique de `SECRET_KEY` sécurisée
4. ✅ **Templates manquants** : Création de `catalogue.html` et `detail_ouvrage.html`
5. ✅ **Routes manquantes** : Ajout des routes pour modifier/supprimer les usagers
6. ✅ **Imports dupliqués** : Nettoyage des imports redondants de `datetime`
7. ✅ **Validation** : Vérification des emails uniques pour les usagers
8. ✅ **Données** : Fichier `requirements.txt` créé
9. ✅ **Incohérences** : Correction du template `usagers.html` et suppression des modales inutiles

## 🚀 Commandes utiles

### Ajouter des données de test
```bash
# Via populate.py (nettoie et réinitialise)
python populate.py

# Via les scripts individuels (ajoute seulement si pas présent)
python ajouter_livres.py
python ajouter_usagers.py
```

### Réinitialiser la base de données
```bash
# Supprimer la base de données
rm instance/bibliotheque.db

# Relancer l'application pour recréer
python app.py
```

## 📝 Notes

- La base de données SQLite (`bibliotheque.db`) est créée automatiquement dans le dossier `instance/`
- Les mots de passe sont hashés avec `werkzeug.security`
- L'authentification utilise Flask-Login
- Bootstrap 5 est utilisé pour le styling

## 📞 Support

En cas de problème :
1. Vérifiez que tous les dépendances sont installées : `pip install -r requirements.txt`
2. Assurez-vous que le port 5000 est disponible
3. Vérifiez les logs dans la console d'exécution pour les messages d'erreur
4. Réinitialisez la base de données si nécessaire

---

**Dernière mise à jour :** Février 2026
