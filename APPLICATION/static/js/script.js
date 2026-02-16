// Scripts JavaScript pour l'application

document.addEventListener('DOMContentLoaded', function() {
    // Gestion des messages flash
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Validation des formulaires
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!this.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            this.classList.add('was-validated');
        }, false);
    });

    // Fonction pour vérifier la disponibilité d'un ouvrage
    window.checkDisponibilite = function(ouvrageId) {
        fetch(`/api/ouvrage/${ouvrageId}/disponibilite`)
            .then(response => response.json())
            .then(data => {
                if (data.disponible) {
                    alert(`Disponible : ${data.exemplaires_disponibles}/${data.total_exemplaires} exemplaires`);
                } else {
                    alert('Non disponible actuellement');
                }
            });
    };

    // Fonction pour vérifier si un usager peut emprunter
    window.checkUsagerEmprunt = function(usagerId) {
        fetch(`/api/usager/${usagerId}/peut_emprunter`)
            .then(response => response.json())
            .then(data => {
                if (!data.peut_emprunter) {
                    alert(data.message);
                }
            });
    };
});