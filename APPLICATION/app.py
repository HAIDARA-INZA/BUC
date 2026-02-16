from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import json

# Créer l'application d'abord
app = Flask(__name__)

# Importer et initialiser la base de données
from database import db, init_app
init_app(app)

# Importer les modèles APRÈS l'initialisation de l'application
from models import *

# Configuration de Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Bibliothecaire, int(user_id))

# ==================== ROUTES PUBLIQUES ====================

@app.route('/')
def index():
    """Page d'accueil publique"""
    return render_template('index.html')

@app.route('/catalogue')
def catalogue():
    """Catalogue public des livres"""
    search = request.args.get('search', '')
    if search:
        ouvrages = Ouvrage.query.filter(
            Ouvrage.titre.contains(search) | 
            Ouvrage.auteur.contains(search)
        ).all()
    else:
        ouvrages = Ouvrage.query.all()
    
    return render_template('catalogue.html', ouvrages=ouvrages)

@app.route('/catalogue/<int:id>')
def detail_ouvrage_public(id):
    """Détail public d'un ouvrage"""
    ouvrage = Ouvrage.query.get_or_404(id)
    exemplaires = Exemplaire.query.filter_by(ouvrage_id=id).all()
    return render_template('detail_ouvrage_public.html', 
                          ouvrage=ouvrage, 
                          exemplaires=exemplaires)

# ==================== ROUTES AUTHENTIFICATION ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        login_input = request.form['login']
        password = request.form['password']
        
        bibliothecaire = Bibliothecaire.query.filter_by(login=login_input).first()
        
        if bibliothecaire and bibliothecaire.check_password(password):
            login_user(bibliothecaire)
            flash('Connexion réussie!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Identifiants incorrects', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Déconnexion"""
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('index'))

# ==================== TABLEAU DE BORD ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord administrateur"""
    stats = {
        'total_ouvrages': Ouvrage.query.count(),
        'total_usagers': Usager.query.count(),
        'emprunts_en_cours': Emprunt.query.filter_by(statut='en_cours').count(),
        'emprunts_en_retard': 0,  # À calculer
        'reservations_actives': Reservation.query.filter_by(statut='active').count()
    }
    return render_template('dashboard.html', stats=stats, now=datetime.now())

# ==================== GESTION DES OUVRAGES ====================

@app.route('/admin/ouvrages')
@login_required
def liste_ouvrages():
    """Liste tous les ouvrages (admin)"""
    search = request.args.get('search', '')
    if search:
        ouvrages = Ouvrage.query.filter(
            Ouvrage.titre.contains(search) | 
            Ouvrage.auteur.contains(search) |
            Ouvrage.isbn.contains(search)
        ).all()
    else:
        ouvrages = Ouvrage.query.all()
    
    return render_template('ouvrages.html', ouvrages=ouvrages)

@app.route('/admin/ouvrage/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter_ouvrage():
    """Ajoute un nouvel ouvrage"""
    if request.method == 'POST':
        titre = request.form['titre']
        auteur = request.form['auteur']
        isbn = request.form.get('isbn')
        nb_exemplaires = int(request.form['nb_exemplaires'])
        
        ouvrage = Ouvrage(
            titre=titre,
            auteur=auteur,
            isbn=isbn,
            nombre_exemplaires=nb_exemplaires
        )
        
        db.session.add(ouvrage)
        db.session.flush()  # Pour obtenir l'ID
        
        # Créer les exemplaires
        for i in range(nb_exemplaires):
            exemplaire = Exemplaire(
                ouvrage_id=ouvrage.id,
                numero=f"{isbn or ouvrage.id}-{i+1:03d}",
                etat='bon'
            )
            db.session.add(exemplaire)
        
        db.session.commit()
        
        flash(f'Ouvrage "{titre}" ajouté avec succès!', 'success')
        return redirect(url_for('liste_ouvrages'))
    
    return render_template('ajouter_ouvrage.html')

@app.route('/admin/ouvrage/<int:id>')
@login_required
def detail_ouvrage(id):
    """Détail d'un ouvrage"""
    ouvrage = Ouvrage.query.get_or_404(id)
    exemplaires = Exemplaire.query.filter_by(ouvrage_id=id).all()
    return render_template('detail_ouvrage.html', 
                          ouvrage=ouvrage, 
                          exemplaires=exemplaires)

# ==================== GESTION DES USAGERS ====================

@app.route('/admin/usagers')
@login_required
def liste_usagers():
    """Liste tous les usagers"""
    search = request.args.get('search', '')
    if search:
        usagers = Usager.query.filter(
            (Usager.nom.contains(search)) | 
            (Usager.prenom.contains(search)) |
            (Usager.email.contains(search))
        ).all()
    else:
        usagers = Usager.query.all()
    
    return render_template('usagers.html', usagers=usagers)

@app.route('/admin/usager/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter_usager():
    """Ajouter un nouvel usager"""
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        telephone = request.form.get('telephone', '')
        adresse = request.form.get('adresse', '')
        
        # Vérifier si l'email existe déjà
        existant = Usager.query.filter_by(email=email).first()
        if existant:
            flash('❌ Un usager avec cet email existe déjà', 'danger')
            return redirect(url_for('ajouter_usager'))
        
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
        
        flash(f'✅ Usager "{prenom} {nom}" ajouté avec succès!', 'success')
        return redirect(url_for('liste_usagers'))
    
    return render_template('ajouter_usager.html')

@app.route('/admin/usager/<int:id>/modifier', methods=['GET', 'POST'])
@login_required
def modifier_usager(id):
    """Modifier un usager"""
    usager = Usager.query.get_or_404(id)
    
    if request.method == 'POST':
        usager.nom = request.form['nom']
        usager.prenom = request.form['prenom']
        usager.telephone = request.form.get('telephone', '')
        usager.adresse = request.form.get('adresse', '')
        usager.statut = request.form['statut']
        
        db.session.commit()
        flash(f'✅ Usager "{usager.prenom} {usager.nom}" modifié avec succès!', 'success')
        return redirect(url_for('liste_usagers'))
    
    return render_template('modifier_usager.html', usager=usager)

@app.route('/admin/usager/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer_usager(id):
    """Supprimer un usager"""
    usager = Usager.query.get_or_404(id)
    prenom, nom = usager.prenom, usager.nom
    
    # Vérifier s'il a des emprunts actifs
    emprunts_actifs = Emprunt.query.filter_by(usager_id=id, statut='en_cours').count()
    if emprunts_actifs > 0:
        flash('❌ Impossible de supprimer un usager avec des emprunts actifs', 'danger')
        return redirect(url_for('liste_usagers'))
    
    db.session.delete(usager)
    db.session.commit()
    
    flash(f'✅ Usager "{prenom} {nom}" supprimé avec succès!', 'success')
    return redirect(url_for('liste_usagers'))


# ==================== GESTION DES EMPRUNTS ====================

@app.route('/admin/emprunts')
@login_required
def liste_emprunts():
    """Liste tous les emprunts"""
    emprunts = Emprunt.query.order_by(Emprunt.date_emprunt.desc()).all()
    return render_template('emprunts.html', emprunts=emprunts)

@app.route('/admin/emprunt/nouveau', methods=['GET', 'POST'])
@login_required
def nouvel_emprunt():
    """Nouvel emprunt"""
    
    if request.method == 'POST':
        usager_id = request.form['usager_id']
        ouvrage_id = request.form['ouvrage_id']
        
        # Vérifier si l'usager peut emprunter
        usager = db.session.get(Usager, usager_id)
        if not usager:
            flash('Usager non trouvé', 'danger')
            return redirect(url_for('nouvel_emprunt'))
        
        if usager.statut != 'actif':
            flash(f'Usager {usager.prenom} {usager.nom} non actif', 'danger')
            return redirect(url_for('nouvel_emprunt'))
        
        # Compter les emprunts en cours
        emprunts_actifs = Emprunt.query.filter_by(
            usager_id=usager_id, 
            statut='en_cours'
        ).count()
        
        if emprunts_actifs >= 5:
            flash(f'Usager {usager.prenom} {usager.nom} a déjà {emprunts_actifs} emprunts en cours', 'danger')
            return redirect(url_for('nouvel_emprunt'))
        
        # Vérifier si l'ouvrage est disponible
        ouvrage = db.session.get(Ouvrage, ouvrage_id)
        if not ouvrage:
            flash('Ouvrage non trouvé', 'danger')
            return redirect(url_for('nouvel_emprunt'))
        
        if not ouvrage.est_disponible():
            flash(f'Ouvrage "{ouvrage.titre}" non disponible', 'danger')
            return redirect(url_for('nouvel_emprunt'))
        
        # Trouver un exemplaire disponible
        exemplaire = None
        for e in ouvrage.exemplaires:
            if e.est_disponible():
                exemplaire = e
                break
        
        if not exemplaire:
            flash('Aucun exemplaire disponible', 'danger')
            return redirect(url_for('nouvel_emprunt'))
        
        # Créer l'emprunt
        emprunt = Emprunt(
            usager_id=usager_id,
            exemplaire_id=exemplaire.id
        )
        
        # Date de retour personnalisée
        if request.form.get('date_retour'):
            try:
                date_retour = datetime.strptime(request.form['date_retour'], '%Y-%m-%d')
                emprunt.date_retour_prevue = date_retour
            except:
                pass  # Garder la date par défaut
        
        db.session.add(emprunt)
        db.session.commit()
        
        flash(f'✅ Emprunt enregistré pour {usager.prenom} {usager.nom}', 'success')
        return redirect(url_for('liste_emprunts'))
    
    # GET : Afficher le formulaire
    usagers = Usager.query.filter_by(statut='actif').order_by(Usager.nom).all()
    ouvrages = Ouvrage.query.order_by(Ouvrage.titre).all()
    
    return render_template('nouvel_emprunt.html', 
                          usagers=usagers, 
                          ouvrages=ouvrages,
                          now=datetime.now())

@app.route('/admin/emprunt/retour/<int:id>')
@login_required
def retourner_emprunt(id):
    """Retour d'un emprunt"""
    
    emprunt = Emprunt.query.get_or_404(id)
    emprunt.date_retour_reelle = datetime.utcnow()
    emprunt.statut = 'retourné'
    db.session.commit()
    
    flash(f'✅ Emprunt #{id} retourné avec succès', 'success')
    return redirect(url_for('liste_emprunts'))

@app.route('/admin/emprunt/prolonger/<int:id>')
@login_required
def prolonger_emprunt(id):
    """Prolonger un emprunt"""
    emprunt = Emprunt.query.get_or_404(id)
    
    if emprunt.statut != 'en_cours':
        flash('❌ Impossible de prolonger un emprunt déjà retourné', 'danger')
        return redirect(url_for('liste_emprunts'))
    
    if emprunt.prolongations >= 2:
        flash('❌ Nombre maximum de prolongations atteint (2)', 'danger')
        return redirect(url_for('liste_emprunts'))
    
    emprunt.date_retour_prevue += timedelta(days=7)
    emprunt.prolongations += 1
    db.session.commit()
    
    flash(f'✅ Emprunt #{id} prolongé de 7 jours', 'success')
    return redirect(url_for('liste_emprunts'))

# ==================== GESTION DES RÉSERVATIONS ====================

@app.route('/admin/reservations')
@login_required
def liste_reservations():
    """Liste toutes les réservations avec filtrage"""
    query = Reservation.query
    
    # Filtrage par statut
    statut = request.args.get('statut', 'active')
    if statut != 'toutes':
        query = query.filter_by(statut=statut)
    
    # Recherche textuelle
    search = request.args.get('search', '').strip()
    if search:
        # Rechercher dans le titre de l'ouvrage ou le nom/prénom de l'usager
        query = query.join(Ouvrage).join(Usager).filter(
            db.or_(
                Ouvrage.titre.ilike(f'%{search}%'),
                Ouvrage.auteur.ilike(f'%{search}%'),
                Usager.nom.ilike(f'%{search}%'),
                Usager.prenom.ilike(f'%{search}%')
            )
        )
    
    reservations = query.all()
    return render_template('reservations.html', reservations=reservations, now=datetime.now())


# ==================== RÉSERVATIONS (CREATION) ====================
@app.route('/admin/ouvrage/<int:id>/reserver', methods=['GET', 'POST'])
@login_required
def reserver_ouvrage(id):
    """Formulaire et action pour créer une réservation pour un ouvrage (admin)"""
    ouvrage = Ouvrage.query.get_or_404(id)

    if request.method == 'POST':
        usager_id = request.form.get('usager_id')
        if not usager_id:
            flash('Veuillez sélectionner un usager', 'danger')
            return redirect(url_for('reserver_ouvrage', id=id))

        usager = db.session.get(Usager, usager_id)
        if not usager:
            flash('Usager non trouvé', 'danger')
            return redirect(url_for('reserver_ouvrage', id=id))

        # Vérifier s'il existe déjà une réservation active pour cet usager et cet ouvrage
        existante = Reservation.query.filter_by(usager_id=usager_id, ouvrage_id=id, statut='active').first()
        if existante:
            flash('Cet usager a déjà une réservation active pour cet ouvrage', 'warning')
            return redirect(url_for('liste_reservations'))

        priorite = Reservation.query.filter_by(ouvrage_id=id, statut='active').count() + 1
        reservation = Reservation(
            usager_id=usager_id,
            ouvrage_id=id,
            priorite=priorite
        )

        db.session.add(reservation)
        db.session.commit()

        flash('✅ Réservation créée avec succès', 'success')
        return redirect(url_for('liste_reservations'))

    # GET : afficher le formulaire de sélection d'usager
    usagers = Usager.query.order_by(Usager.nom).all()
    return render_template('reserver_ouvrage.html', ouvrage=ouvrage, usagers=usagers)


# Route pour créer une réservation depuis un formulaire général (choix usager + ouvrage)
@app.route('/admin/reservation/nouveau', methods=['GET', 'POST'])
@login_required
def nouvelle_reservation():
    """Formulaire générique pour créer une réservation (choix usager + ouvrage)"""
    if request.method == 'POST':
        usager_id = request.form.get('usager_id')
        ouvrage_id = request.form.get('ouvrage_id')

        if not usager_id or not ouvrage_id:
            flash('Veuillez sélectionner un usager et un ouvrage', 'danger')
            return redirect(url_for('nouvelle_reservation'))

        usager = db.session.get(Usager, usager_id)
        ouvrage = db.session.get(Ouvrage, ouvrage_id)
        if not usager or not ouvrage:
            flash('Usager ou ouvrage non trouvé', 'danger')
            return redirect(url_for('nouvelle_reservation'))

        existante = Reservation.query.filter_by(usager_id=usager_id, ouvrage_id=ouvrage_id, statut='active').first()
        if existante:
            flash('Réservation active déjà existante pour cet usager et cet ouvrage', 'warning')
            return redirect(url_for('liste_reservations'))

        priorite = Reservation.query.filter_by(ouvrage_id=ouvrage_id, statut='active').count() + 1
        reservation = Reservation(usager_id=usager_id, ouvrage_id=ouvrage_id, priorite=priorite)
        db.session.add(reservation)
        db.session.commit()

        flash('✅ Réservation créée avec succès', 'success')
        return redirect(url_for('liste_reservations'))

    usagers = Usager.query.order_by(Usager.nom).all()
    ouvrages = Ouvrage.query.order_by(Ouvrage.titre).all()
    return render_template('nouvelle_reservation.html', usagers=usagers, ouvrages=ouvrages)


@app.route('/admin/reservation/honorer/<int:id>')
@login_required
def honorer_reservation(id):
    """Marque une réservation comme honorée"""
    reservation = Reservation.query.get_or_404(id)
    reservation.statut = 'honorée'
    db.session.commit()
    flash('✅ Réservation marquée comme honorée', 'success')
    return redirect(url_for('liste_reservations'))


@app.route('/admin/reservation/annuler/<int:id>')
@login_required
def annuler_reservation(id):
    """Annule une réservation"""
    reservation = Reservation.query.get_or_404(id)
    reservation.statut = 'annulée'
    db.session.commit()
    flash('✅ Réservation annulée', 'info')
    return redirect(url_for('liste_reservations'))

# ==================== API ====================

@app.route('/api/ouvrage/<int:id>/disponibilite')
def disponibilite_ouvrage(id):
    """API pour vérifier la disponibilité d'un ouvrage"""
    ouvrage = Ouvrage.query.get_or_404(id)
    return jsonify({
        'disponible': ouvrage.est_disponible(),
        'exemplaires_disponibles': ouvrage.exemplaires_disponibles(),
        'total_exemplaires': ouvrage.nombre_exemplaires
    })

# ==================== INITIALISATION ====================

def create_default_admin():
    with app.app_context():
        admin = Bibliothecaire.query.filter_by(login="admin").first()
        if not admin:
            admin = Bibliothecaire(
                nom="Admin",
                prenom="System",
                login="admin",
            )
        # Toujours définir le mot de passe (pour mise à jour)
        admin.set_password("admin123")  # Changez "admin123" par le mot de passe souhaité
        db.session.add(admin)
        db.session.commit()
        print("✅ Administrateur 'admin' configuré avec le mot de passe défini")

if __name__ == '__main__':
    create_default_admin()
    app.run(debug=True, port=5000)