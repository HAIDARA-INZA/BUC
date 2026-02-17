from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, g
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError

# Creer l'application d'abord
app = Flask(__name__)

# Importer et initialiser la base de donnees
from database import db, init_app, ensure_schema

init_app(app)

# Importer les modeles APRES l'initialisation de l'application
from models import Bibliothecaire, Usager, Ouvrage, Exemplaire, Emprunt, Reservation, DemandeUsager

# Creer les nouvelles tables une fois les modeles charges
ensure_schema(app)

# Configuration de Flask-Login (admin)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Bibliothecaire, int(user_id))


def get_usager_session():
    usager_id = session.get('usager_id')
    if not usager_id:
        return None
    return db.session.get(Usager, usager_id)


def usager_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        usager = get_usager_session()
        if not usager:
            flash('Connectez-vous pour acceder a votre espace usager.', 'warning')
            return redirect(url_for('usager_login'))
        g.usager_session = usager
        return view(*args, **kwargs)

    return wrapped


@app.before_request
def inject_request_context():
    g.usager_session = get_usager_session()


@app.context_processor
def inject_global_context():
    return {
        'usager_session': get_usager_session(),
        'is_admin_connected': current_user.is_authenticated,
    }


# ==================== ROUTES PUBLIQUES ====================

@app.route('/')
def index():
    """Page d'accueil publique"""
    return render_template('index.html')


@app.route('/catalogue')
def catalogue():
    """Catalogue public des livres"""
    search = request.args.get('search', '').strip()
    if search:
        ouvrages = Ouvrage.query.filter(
            Ouvrage.titre.contains(search) | Ouvrage.auteur.contains(search)
        ).all()
    else:
        ouvrages = Ouvrage.query.all()

    return render_template('catalogue.html', ouvrages=ouvrages)


@app.route('/catalogue/<int:id>')
def detail_ouvrage_public(id):
    """Detail public d'un ouvrage"""
    ouvrage = Ouvrage.query.get_or_404(id)
    exemplaires = Exemplaire.query.filter_by(ouvrage_id=id).all()
    return render_template('detail_ouvrage_public.html', ouvrage=ouvrage, exemplaires=exemplaires)


# ==================== ROUTES AUTH ADMIN ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion admin"""
    if request.method == 'POST':
        login_input = request.form['login']
        password = request.form['password']

        bibliothecaire = Bibliothecaire.query.filter_by(login=login_input).first()

        if bibliothecaire and bibliothecaire.check_password(password):
            login_user(bibliothecaire)
            flash('Connexion admin reussie.', 'success')
            return redirect(url_for('dashboard'))

        flash('Identifiants admin incorrects.', 'danger')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Deconnexion admin"""
    logout_user()
    flash('Vous avez ete deconnecte.', 'info')
    return redirect(url_for('index'))


# ==================== ROUTES AUTH USAGER ====================

@app.route('/espace-usager/inscription', methods=['GET', 'POST'])
def usager_register():
    if request.method == 'POST':
        nom = request.form['nom'].strip()
        prenom = request.form['prenom'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']
        telephone = request.form.get('telephone', '').strip()
        adresse = request.form.get('adresse', '').strip()

        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caracteres.', 'danger')
            return redirect(url_for('usager_register'))

        existant = Usager.query.filter_by(email=email).first()
        if existant:
            flash('Un compte usager avec cet email existe deja.', 'warning')
            return redirect(url_for('usager_login'))

        usager = Usager(
            nom=nom,
            prenom=prenom,
            email=email,
            telephone=telephone,
            adresse=adresse,
            statut='actif',
        )
        usager.set_password(password)

        db.session.add(usager)
        db.session.commit()

        session['usager_id'] = usager.id
        flash('Compte usager cree avec succes.', 'success')
        return redirect(url_for('usager_dashboard'))

    return render_template('usager_register.html')


@app.route('/espace-usager/connexion', methods=['GET', 'POST'])
def usager_login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']

        usager = Usager.query.filter_by(email=email).first()
        if not usager or not usager.check_password(password):
            flash('Email ou mot de passe invalide.', 'danger')
            return redirect(url_for('usager_login'))

        if usager.statut != 'actif':
            flash('Votre compte est inactif. Contactez la bibliotheque.', 'warning')
            return redirect(url_for('usager_login'))

        session['usager_id'] = usager.id
        flash('Connexion usager reussie.', 'success')
        return redirect(url_for('usager_dashboard'))

    return render_template('usager_login.html')




@app.route('/espace-usager/mot-de-passe-oublie', methods=['GET', 'POST'])
def usager_forgot_password():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        nom = request.form['nom'].strip().lower()
        prenom = request.form['prenom'].strip().lower()
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        usager = Usager.query.filter_by(email=email).first()
        if not usager:
            flash('Aucun compte trouve avec cet email.', 'danger')
            return redirect(url_for('usager_forgot_password'))

        if usager.nom.strip().lower() != nom or usager.prenom.strip().lower() != prenom:
            flash('Verification identite echouee (nom ou prenom incorrect).', 'danger')
            return redirect(url_for('usager_forgot_password'))

        if len(new_password) < 6:
            flash('Le nouveau mot de passe doit contenir au moins 6 caracteres.', 'danger')
            return redirect(url_for('usager_forgot_password'))

        if new_password != confirm_password:
            flash('La confirmation du mot de passe ne correspond pas.', 'danger')
            return redirect(url_for('usager_forgot_password'))

        usager.set_password(new_password)
        db.session.commit()

        flash('Mot de passe reinitialise avec succes. Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('usager_login'))

    return render_template('usager_forgot_password.html')

@app.route('/espace-usager/deconnexion')
def usager_logout():
    session.pop('usager_id', None)
    flash('Vous etes deconnecte de votre espace usager.', 'info')
    return redirect(url_for('index'))


# ==================== DASHBOARD ADMIN ====================

@app.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord administrateur"""
    emprunts_en_cours = Emprunt.query.filter_by(statut='en_cours').all()

    stats = {
        'total_ouvrages': Ouvrage.query.count(),
        'total_usagers': Usager.query.count(),
        'emprunts_en_cours': len(emprunts_en_cours),
        'emprunts_en_retard': len([e for e in emprunts_en_cours if e.est_en_retard()]),
        'reservations_actives': Reservation.query.filter_by(statut='active').count(),
        'demandes_en_attente': DemandeUsager.query.filter_by(statut='en_attente').count(),
    }

    derniers_emprunts = Emprunt.query.order_by(Emprunt.date_emprunt.desc()).limit(6).all()

    return render_template(
        'dashboard.html',
        stats=stats,
        now=datetime.now(),
        derniers_emprunts=derniers_emprunts,
    )


# ==================== DASHBOARD USAGER ====================

@app.route('/espace-usager/dashboard')
@usager_required
def usager_dashboard():
    usager = g.usager_session

    emprunts_en_cours = Emprunt.query.filter_by(usager_id=usager.id, statut='en_cours').all()
    reservations_actives = Reservation.query.filter_by(usager_id=usager.id, statut='active').count()
    demandes = DemandeUsager.query.filter_by(usager_id=usager.id).order_by(DemandeUsager.date_creation.desc()).all()
    emprunts_recents = Emprunt.query.filter_by(usager_id=usager.id).order_by(Emprunt.date_emprunt.desc()).limit(10).all()

    stats = {
        'emprunts_en_cours': len(emprunts_en_cours),
        'emprunts_en_retard': len([e for e in emprunts_en_cours if e.est_en_retard()]),
        'reservations_actives': reservations_actives,
        'demandes_total': len(demandes),
        'demandes_en_attente': len([d for d in demandes if d.statut == 'en_attente']),
        'demandes_acceptees': len([d for d in demandes if d.statut == 'acceptee']),
    }

    demandes_recentes = demandes[:8]
    ouvrages = Ouvrage.query.order_by(Ouvrage.date_ajout.desc()).limit(8).all()

    return render_template(
        'usager_dashboard.html',
        usager=usager,
        stats=stats,
        demandes=demandes_recentes,
        emprunts=emprunts_recents,
        ouvrages=ouvrages,
        now=datetime.now(),
    )


@app.route('/api/espace-usager/dashboard')
@usager_required
def api_usager_dashboard():
    usager = g.usager_session

    emprunts = Emprunt.query.filter_by(usager_id=usager.id, statut='en_cours').all()
    demandes = DemandeUsager.query.filter_by(usager_id=usager.id).order_by(DemandeUsager.date_creation.desc()).limit(5).all()

    payload = {
        'stats': {
            'emprunts_en_cours': len(emprunts),
            'emprunts_en_retard': len([e for e in emprunts if e.est_en_retard()]),
            'reservations_actives': Reservation.query.filter_by(usager_id=usager.id, statut='active').count(),
            'demandes_en_attente': DemandeUsager.query.filter_by(usager_id=usager.id, statut='en_attente').count(),
        },
        'demandes': [
            {
                'id': d.id,
                'ouvrage': d.ouvrage.titre,
                'type_demande': d.type_demande,
                'statut': d.statut,
                'date_creation': d.date_creation.strftime('%d/%m/%Y %H:%M'),
            }
            for d in demandes
        ],
    }
    return jsonify(payload)


# ==================== DEMANDES USAGER ====================

@app.route('/espace-usager/demande', methods=['POST'])
@usager_required
def creer_demande_usager():
    usager = g.usager_session

    ouvrage_id = request.form.get('ouvrage_id')
    type_demande = request.form.get('type_demande')
    commentaire = request.form.get('commentaire', '').strip()

    if type_demande not in {'emprunt', 'reservation'}:
        flash('Type de demande invalide.', 'danger')
        return redirect(url_for('usager_dashboard'))

    ouvrage = db.session.get(Ouvrage, ouvrage_id)
    if not ouvrage:
        flash('Ouvrage introuvable.', 'danger')
        return redirect(url_for('usager_dashboard'))

    deja_en_attente = DemandeUsager.query.filter_by(
        usager_id=usager.id,
        ouvrage_id=ouvrage.id,
        type_demande=type_demande,
        statut='en_attente',
    ).first()

    if deja_en_attente:
        flash('Une demande identique est deja en attente.', 'warning')
        return redirect(url_for('usager_dashboard'))

    demande = DemandeUsager(
        usager_id=usager.id,
        ouvrage_id=ouvrage.id,
        type_demande=type_demande,
        commentaire=commentaire,
    )

    db.session.add(demande)
    db.session.commit()

    flash('Demande envoyee. Elle sera traitee par l administrateur.', 'success')
    return redirect(url_for('usager_dashboard'))


# ==================== GESTION DES OUVRAGES ====================

@app.route('/admin/ouvrages')
@login_required
def liste_ouvrages():
    """Liste tous les ouvrages (admin)"""
    search = request.args.get('search', '').strip()
    if search:
        ouvrages = Ouvrage.query.filter(
            Ouvrage.titre.contains(search)
            | Ouvrage.auteur.contains(search)
            | Ouvrage.isbn.contains(search)
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
            nombre_exemplaires=nb_exemplaires,
        )

        db.session.add(ouvrage)
        db.session.flush()

        for i in range(nb_exemplaires):
            exemplaire = Exemplaire(
                ouvrage_id=ouvrage.id,
                numero=f"{isbn or ouvrage.id}-{i + 1:03d}",
                etat='bon',
            )
            db.session.add(exemplaire)

        db.session.commit()

        flash(f'Ouvrage "{titre}" ajoute avec succes.', 'success')
        return redirect(url_for('liste_ouvrages'))

    return render_template('ajouter_ouvrage.html')


@app.route('/admin/ouvrage/<int:id>')
@login_required
def detail_ouvrage(id):
    """Detail d'un ouvrage"""
    ouvrage = Ouvrage.query.get_or_404(id)
    exemplaires = Exemplaire.query.filter_by(ouvrage_id=id).all()
    return render_template('detail_ouvrage.html', ouvrage=ouvrage, exemplaires=exemplaires)


# ==================== GESTION DES USAGERS ====================

@app.route('/admin/usagers')
@login_required
def liste_usagers():
    """Liste tous les usagers"""
    search = request.args.get('search', '').strip()
    if search:
        usagers = Usager.query.filter(
            (Usager.nom.contains(search))
            | (Usager.prenom.contains(search))
            | (Usager.email.contains(search))
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
        email = request.form['email'].strip().lower()
        telephone = request.form.get('telephone', '')
        adresse = request.form.get('adresse', '')
        password = request.form.get('password', '').strip()

        existant = Usager.query.filter_by(email=email).first()
        if existant:
            flash('Un usager avec cet email existe deja.', 'danger')
            return redirect(url_for('ajouter_usager'))

        usager = Usager(
            nom=nom,
            prenom=prenom,
            email=email,
            telephone=telephone,
            adresse=adresse,
            statut='actif',
        )

        if password:
            usager.set_password(password)

        db.session.add(usager)
        db.session.commit()

        flash(f'Usager "{prenom} {nom}" ajoute avec succes.', 'success')
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

        new_password = request.form.get('password', '').strip()
        if new_password:
            usager.set_password(new_password)

        db.session.commit()
        flash(f'Usager "{usager.prenom} {usager.nom}" modifie avec succes.', 'success')
        return redirect(url_for('liste_usagers'))

    return render_template('modifier_usager.html', usager=usager)


@app.route('/admin/usager/<int:id>/supprimer', methods=['POST'])
@login_required
def supprimer_usager(id):
    """Supprimer un usager"""
    usager = Usager.query.get_or_404(id)
    prenom, nom = usager.prenom, usager.nom

    emprunts_actifs = Emprunt.query.filter(
        Emprunt.usager_id == id,
        Emprunt.statut.in_(['en_cours', 'en_retard'])
    ).count()
    if emprunts_actifs > 0:
        flash('Impossible de supprimer un usager avec des emprunts actifs.', 'danger')
        return redirect(url_for('liste_usagers'))

    try:
        DemandeUsager.query.filter_by(usager_id=id).delete(synchronize_session=False)
        Reservation.query.filter_by(usager_id=id).delete(synchronize_session=False)
        Emprunt.query.filter_by(usager_id=id).delete(synchronize_session=False)

        db.session.delete(usager)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash('Suppression impossible: cet usager est encore lie a des operations en cours.', 'danger')
        return redirect(url_for('liste_usagers'))

    flash(f'Usager "{prenom} {nom}" supprime avec succes.', 'success')
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

        usager = db.session.get(Usager, usager_id)
        if not usager:
            flash('Usager non trouve.', 'danger')
            return redirect(url_for('nouvel_emprunt'))

        if usager.statut != 'actif':
            flash(f'Usager {usager.prenom} {usager.nom} non actif.', 'danger')
            return redirect(url_for('nouvel_emprunt'))

        emprunts_actifs = Emprunt.query.filter_by(usager_id=usager_id, statut='en_cours').count()
        if emprunts_actifs >= 5:
            flash(f'Usager {usager.prenom} {usager.nom} a deja {emprunts_actifs} emprunts en cours.', 'danger')
            return redirect(url_for('nouvel_emprunt'))

        ouvrage = db.session.get(Ouvrage, ouvrage_id)
        if not ouvrage:
            flash('Ouvrage non trouve.', 'danger')
            return redirect(url_for('nouvel_emprunt'))

        if not ouvrage.est_disponible():
            flash(f'Ouvrage "{ouvrage.titre}" non disponible.', 'danger')
            return redirect(url_for('nouvel_emprunt'))

        exemplaire = next((e for e in ouvrage.exemplaires if e.est_disponible()), None)
        if not exemplaire:
            flash('Aucun exemplaire disponible.', 'danger')
            return redirect(url_for('nouvel_emprunt'))

        emprunt = Emprunt(usager_id=usager_id, exemplaire_id=exemplaire.id)

        if request.form.get('date_retour'):
            try:
                date_retour = datetime.strptime(request.form['date_retour'], '%Y-%m-%d')
                emprunt.date_retour_prevue = date_retour
            except ValueError:
                pass

        db.session.add(emprunt)
        db.session.commit()

        flash(f'Emprunt enregistre pour {usager.prenom} {usager.nom}.', 'success')
        return redirect(url_for('liste_emprunts'))

    usagers = Usager.query.filter_by(statut='actif').order_by(Usager.nom).all()
    ouvrages = Ouvrage.query.order_by(Ouvrage.titre).all()

    return render_template('nouvel_emprunt.html', usagers=usagers, ouvrages=ouvrages, now=datetime.now())


@app.route('/admin/emprunt/retour/<int:id>')
@login_required
def retourner_emprunt(id):
    """Retour d'un emprunt"""

    emprunt = Emprunt.query.get_or_404(id)
    emprunt.date_retour_reelle = datetime.utcnow()
    emprunt.statut = 'retourne'
    db.session.commit()

    flash(f'Emprunt #{id} retourne avec succes.', 'success')
    return redirect(url_for('liste_emprunts'))


@app.route('/admin/emprunt/prolonger/<int:id>')
@login_required
def prolonger_emprunt(id):
    """Prolonger un emprunt"""
    emprunt = Emprunt.query.get_or_404(id)

    if emprunt.statut != 'en_cours':
        flash('Impossible de prolonger un emprunt deja retourne.', 'danger')
        return redirect(url_for('liste_emprunts'))

    if emprunt.prolongations >= 2:
        flash('Nombre maximum de prolongations atteint (2).', 'danger')
        return redirect(url_for('liste_emprunts'))

    emprunt.date_retour_prevue += timedelta(days=7)
    emprunt.prolongations += 1
    db.session.commit()

    flash(f'Emprunt #{id} prolonge de 7 jours.', 'success')
    return redirect(url_for('liste_emprunts'))


# ==================== GESTION DES RESERVATIONS ====================

@app.route('/admin/reservations')
@login_required
def liste_reservations():
    """Liste toutes les reservations avec filtrage"""
    query = Reservation.query

    statut = request.args.get('statut', 'active')
    if statut != 'toutes':
        query = query.filter_by(statut=statut)

    search = request.args.get('search', '').strip()
    if search:
        query = query.join(Ouvrage).join(Usager).filter(
            (Ouvrage.titre.ilike(f'%{search}%'))
            | (Ouvrage.auteur.ilike(f'%{search}%'))
            | (Usager.nom.ilike(f'%{search}%'))
            | (Usager.prenom.ilike(f'%{search}%'))
        )

    reservations = query.all()
    return render_template('reservations.html', reservations=reservations, now=datetime.now())


@app.route('/admin/ouvrage/<int:id>/reserver', methods=['GET', 'POST'])
@login_required
def reserver_ouvrage(id):
    """Formulaire et action pour creer une reservation pour un ouvrage (admin)"""
    ouvrage = Ouvrage.query.get_or_404(id)

    if request.method == 'POST':
        usager_id = request.form.get('usager_id')
        if not usager_id:
            flash('Veuillez selectionner un usager.', 'danger')
            return redirect(url_for('reserver_ouvrage', id=id))

        usager = db.session.get(Usager, usager_id)
        if not usager:
            flash('Usager non trouve.', 'danger')
            return redirect(url_for('reserver_ouvrage', id=id))

        existante = Reservation.query.filter_by(usager_id=usager_id, ouvrage_id=id, statut='active').first()
        if existante:
            flash('Cet usager a deja une reservation active pour cet ouvrage.', 'warning')
            return redirect(url_for('liste_reservations'))

        priorite = Reservation.query.filter_by(ouvrage_id=id, statut='active').count() + 1
        reservation = Reservation(usager_id=usager_id, ouvrage_id=id, priorite=priorite)

        db.session.add(reservation)
        db.session.commit()

        flash('Reservation creee avec succes.', 'success')
        return redirect(url_for('liste_reservations'))

    usagers = Usager.query.order_by(Usager.nom).all()
    return render_template('reserver_ouvrage.html', ouvrage=ouvrage, usagers=usagers)


@app.route('/admin/reservation/nouveau', methods=['GET', 'POST'])
@login_required
def nouvelle_reservation():
    """Formulaire generique pour creer une reservation (choix usager + ouvrage)"""
    if request.method == 'POST':
        usager_id = request.form.get('usager_id')
        ouvrage_id = request.form.get('ouvrage_id')

        if not usager_id or not ouvrage_id:
            flash('Veuillez selectionner un usager et un ouvrage.', 'danger')
            return redirect(url_for('nouvelle_reservation'))

        usager = db.session.get(Usager, usager_id)
        ouvrage = db.session.get(Ouvrage, ouvrage_id)
        if not usager or not ouvrage:
            flash('Usager ou ouvrage non trouve.', 'danger')
            return redirect(url_for('nouvelle_reservation'))

        existante = Reservation.query.filter_by(usager_id=usager_id, ouvrage_id=ouvrage_id, statut='active').first()
        if existante:
            flash('Reservation active deja existante pour cet usager et cet ouvrage.', 'warning')
            return redirect(url_for('liste_reservations'))

        priorite = Reservation.query.filter_by(ouvrage_id=ouvrage_id, statut='active').count() + 1
        reservation = Reservation(usager_id=usager_id, ouvrage_id=ouvrage_id, priorite=priorite)
        db.session.add(reservation)
        db.session.commit()

        flash('Reservation creee avec succes.', 'success')
        return redirect(url_for('liste_reservations'))

    usagers = Usager.query.order_by(Usager.nom).all()
    ouvrages = Ouvrage.query.order_by(Ouvrage.titre).all()
    return render_template('nouvelle_reservation.html', usagers=usagers, ouvrages=ouvrages)


@app.route('/admin/reservation/honorer/<int:id>')
@login_required
def honorer_reservation(id):
    """Marque une reservation comme honoree"""
    reservation = Reservation.query.get_or_404(id)
    reservation.statut = 'honoree'
    db.session.commit()
    flash('Reservation marquee comme honoree.', 'success')
    return redirect(url_for('liste_reservations'))


@app.route('/admin/reservation/annuler/<int:id>')
@login_required
def annuler_reservation(id):
    """Annule une reservation"""
    reservation = Reservation.query.get_or_404(id)
    reservation.statut = 'annulee'
    db.session.commit()
    flash('Reservation annulee.', 'info')
    return redirect(url_for('liste_reservations'))


# ==================== DEMANDES COTE ADMIN ====================

@app.route('/admin/demandes')
@login_required
def admin_demandes():
    statut = request.args.get('statut', 'en_attente')
    query = DemandeUsager.query.order_by(DemandeUsager.date_creation.desc())
    if statut != 'toutes':
        query = query.filter_by(statut=statut)

    demandes = query.all()
    return render_template('admin_demandes.html', demandes=demandes, statut=statut)


@app.route('/admin/demande/<int:id>/accepter', methods=['POST'])
@login_required
def accepter_demande(id):
    demande = DemandeUsager.query.get_or_404(id)
    commentaire_admin = request.form.get('commentaire_admin', '').strip()

    if demande.statut != 'en_attente':
        flash('Cette demande est deja traitee.', 'warning')
        return redirect(url_for('admin_demandes'))

    usager = demande.usager
    ouvrage = demande.ouvrage

    if demande.type_demande == 'emprunt':
        peut, message = usager.peut_emprunter()
        if not peut:
            flash(f'Demande refusee automatiquement: {message}.', 'danger')
            return redirect(url_for('admin_demandes'))

        if not ouvrage.est_disponible():
            flash('Impossible d accepter: ouvrage non disponible.', 'danger')
            return redirect(url_for('admin_demandes'))

        exemplaire = next((e for e in ouvrage.exemplaires if e.est_disponible()), None)
        if not exemplaire:
            flash('Aucun exemplaire disponible.', 'danger')
            return redirect(url_for('admin_demandes'))

        db.session.add(Emprunt(usager_id=usager.id, exemplaire_id=exemplaire.id))

    elif demande.type_demande == 'reservation':
        deja_active = Reservation.query.filter_by(
            usager_id=usager.id,
            ouvrage_id=ouvrage.id,
            statut='active',
        ).first()
        if deja_active:
            flash('Reservation deja active pour cet usager.', 'warning')
            return redirect(url_for('admin_demandes'))

        priorite = Reservation.query.filter_by(ouvrage_id=ouvrage.id, statut='active').count() + 1
        db.session.add(Reservation(usager_id=usager.id, ouvrage_id=ouvrage.id, priorite=priorite))

    demande.statut = 'acceptee'
    demande.commentaire_admin = commentaire_admin
    demande.date_traitement = datetime.utcnow()
    demande.bibliothecaire_id = current_user.id

    db.session.commit()
    flash('Demande acceptee et traitee.', 'success')
    return redirect(url_for('admin_demandes'))


@app.route('/admin/demande/<int:id>/refuser', methods=['POST'])
@login_required
def refuser_demande(id):
    demande = DemandeUsager.query.get_or_404(id)
    commentaire_admin = request.form.get('commentaire_admin', '').strip()

    if demande.statut != 'en_attente':
        flash('Cette demande est deja traitee.', 'warning')
        return redirect(url_for('admin_demandes'))

    demande.statut = 'refusee'
    demande.commentaire_admin = commentaire_admin
    demande.date_traitement = datetime.utcnow()
    demande.bibliothecaire_id = current_user.id

    db.session.commit()
    flash('Demande refusee.', 'info')
    return redirect(url_for('admin_demandes'))


# ==================== API ====================

@app.route('/api/ouvrage/<int:id>/disponibilite')
def disponibilite_ouvrage(id):
    """API pour verifier la disponibilite d'un ouvrage"""
    ouvrage = Ouvrage.query.get_or_404(id)
    return jsonify(
        {
            'disponible': ouvrage.est_disponible(),
            'exemplaires_disponibles': ouvrage.exemplaires_disponibles(),
            'total_exemplaires': ouvrage.nombre_exemplaires,
        }
    )


# ==================== INITIALISATION ====================

def create_default_admin():
    with app.app_context():
        admin = Bibliothecaire.query.filter_by(login='admin').first()
        if not admin:
            admin = Bibliothecaire(nom='Admin', prenom='System', login='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Administrateur 'admin' configure")


if __name__ == '__main__':
    create_default_admin()
    app.run(debug=True, port=5000)

