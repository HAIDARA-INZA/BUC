// Scripts JavaScript pour l'application

document.addEventListener('DOMContentLoaded', function () {
    // Fermeture auto des alertes flash
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach((alert) => {
        setTimeout(() => {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {
                // Ignore si l'alerte est deja retiree
            }
        }, 5000);
    });

    // Validation HTML5
    const forms = document.querySelectorAll('form');
    forms.forEach((form) => {
        form.addEventListener(
            'submit',
            function (e) {
                if (!this.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                }
                this.classList.add('was-validated');
            },
            false
        );
    });

    // Verification disponibilite ouvrage
    window.checkDisponibilite = function (ouvrageId) {
        fetch(`/api/ouvrage/${ouvrageId}/disponibilite`)
            .then((response) => response.json())
            .then((data) => {
                if (data.disponible) {
                    alert(`Disponible : ${data.exemplaires_disponibles}/${data.total_exemplaires} exemplaires`);
                } else {
                    alert('Non disponible actuellement');
                }
            });
    };

    // Rafraichissement dynamique dashboard usager
    const userDashboard = document.querySelector('[data-user-dashboard="true"]');
    if (userDashboard) {
        const updateDashboard = () => {
            fetch('/api/espace-usager/dashboard')
                .then((res) => res.json())
                .then((payload) => {
                    if (!payload || !payload.stats) return;

                    const stats = payload.stats;
                    const emprunts = document.getElementById('kpi-emprunts');
                    const retards = document.getElementById('kpi-retards');
                    const reservations = document.getElementById('kpi-reservations');
                    const demandes = document.getElementById('kpi-demandes');

                    if (emprunts) emprunts.textContent = stats.emprunts_en_cours;
                    if (retards) retards.textContent = stats.emprunts_en_retard;
                    if (reservations) reservations.textContent = stats.reservations_actives;
                    if (demandes) demandes.textContent = stats.demandes_en_attente;

                    const list = document.getElementById('demandes-live-list');
                    if (list && Array.isArray(payload.demandes)) {
                        if (payload.demandes.length === 0) {
                            list.innerHTML = '<div class="p-4 text-muted">Aucune demande pour le moment.</div>';
                            return;
                        }

                        list.innerHTML = payload.demandes
                            .map((d) => {
                                let badgeClass = 'bg-warning text-dark';
                                if (d.statut === 'acceptee') badgeClass = 'bg-success';
                                if (d.statut === 'refusee') badgeClass = 'bg-danger';

                                return `
                                <div class="list-group-item">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <strong>${d.ouvrage}</strong>
                                        <span class="badge ${badgeClass}">${d.statut}</span>
                                    </div>
                                    <small>${d.type_demande} - ${d.date_creation}</small>
                                </div>`;
                            })
                            .join('');
                    }
                })
                .catch(() => {
                    // Laisse l'etat actuel en cas d'erreur reseau ponctuelle
                });
        };

        updateDashboard();
        setInterval(updateDashboard, 15000);
    }
});
