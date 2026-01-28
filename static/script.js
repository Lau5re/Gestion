// static/script.js

const API_BASE = 'http://127.0.0.1:5000';

// Charger la liste au démarrage
window.onload = () => chargerProduits();

async function chargerProduits() {
    document.getElementById('loading').style.display = 'block';
    try {
        const res = await fetch(`${API_BASE}/produits`);
        if (!res.ok) throw new Error('Erreur chargement');
        const produits = await res.json();
        afficherProduits(produits);
    } catch (err) {
        document.getElementById('tbody').innerHTML = `<tr><td colspan="4" class="error">Erreur : ${err.message}</td></tr>`;
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

function afficherProduits(produits) {
    const tbody = document.getElementById('tbody');
    tbody.innerHTML = '';
    produits.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${p.id}</td>
            <td>${p.nom}</td>
            <td>${p.quantite}</td>
            <td style="white-space: nowrap;">
                <input type="number" id="delta-${p.id}" placeholder="Δ" min="-${p.quantite}" step="1" style="width: 80px; text-align: center;">
                <button onclick="appliquerDelta(${p.id})" style="background:#2196F3; margin-left: 8px;">Mettre à jour</button>
                <button class="delete-btn" onclick="supprimerProduit(${p.id})" style="margin-left: 8px;">Supprimer</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function appliquerDelta(id) {
    const input = document.getElementById(`delta-${id}`);
    const delta = parseInt(input.value);

    if (isNaN(delta) || delta === 0) {
        alert("Entrez une quantité valide (différente de 0)");
        return;
    }

    if (!confirm(`Appliquer un changement de ${delta} à ce produit ?`)) return;

    try {
        const res = await fetch(`${API_BASE}/produits/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ delta })
        });

        if (!res.ok) {
            const err = await res.json();
            alert(err.error || "Erreur lors de la mise à jour");
            return;
        }

        // Succès
        input.value = '';
        chargerProduits();
    } catch (err) {
        alert('Erreur réseau : ' + err.message);
    }
}

async function addProduit() {
    const nom = document.getElementById('nom').value.trim();
    const quantite = parseInt(document.getElementById('quantite').value);
    const messageEl = document.getElementById('add-message');

    if (!nom || isNaN(quantite) || quantite < 0) {
        messageEl.textContent = 'Nom et quantité positive requis !';
        return;
    }
    

    try {
        const res = await fetch(`${API_BASE}/produits`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nom, quantite })
        });
        if (!res.ok) throw new Error(await res.text());
        messageEl.textContent = '';
        document.getElementById('nom').value = '';
        document.getElementById('quantite').value = '';
        chargerProduits();
    } catch (err) {
        messageEl.textContent = err.message;
    }
}

async function supprimerProduit(id) {
    if (!confirm('Supprimer ce produit ?')) return;
    try {
        const res = await fetch(`${API_BASE}/produits/${id}`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error('Erreur suppression');
        chargerProduits();
    } catch (err) {
        alert('Erreur : ' + err.message);
    }
}

async function rechercher() {
    const query = document.getElementById('search').value.trim();
    if (!query) {
        chargerProduits();
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/recherche?nom=${encodeURIComponent(query)}`);
        if (!res.ok) throw new Error('Erreur recherche');
        const resultats = await res.json();
        afficherProduits(resultats);
    } catch (err) {
        document.getElementById('tbody').innerHTML = `<tr><td colspan="4" class="error">${err.message}</td></tr>`;
    }
}