// static/script.js

const API_BASE = ''; 

let derniereRecherche = '';  // chaîne vide = "tout afficher"

// Charger les données au démarrage
window.onload = () => {
    chargerCategories();
    chargerProduits();
};

async function chargerCategories() {
    try {
        const res = await fetch(`${API_BASE}/categories`);
        if (!res.ok) throw new Error('Erreur de chargement des catégories');
        const categories = await res.json();
        const select = document.getElementById('categorie');
        select.innerHTML = categories.map(c => `<option value="${c.id}">${c.nom}</option>`).join('');
    } catch (err) {
        console.error(err);
    }
}

async function chargerProduits() {
    const loading = document.getElementById('loading');
    const tbody = document.getElementById('tbody');
    
    loading.classList.remove('hidden');
    try {
        const res = await fetch(`${API_BASE}/produits`);
        if (!res.ok) throw new Error('Erreur de chargement');
        const produits = await res.json();
        afficherProduits(produits);
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="5" class="px-6 py-8 text-center text-red-500 font-medium bg-red-50"><i class="fas fa-exclamation-triangle mr-2"></i>Erreur : ${err.message}</td></tr>`;
    } finally {
        loading.classList.add('hidden');
    }
}

function afficherProduits(produits) {
    const tbody = document.getElementById('tbody');
    tbody.innerHTML = '';
    
    if (produits.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="px-6 py-12 text-center text-slate-400 italic">Aucun produit trouvé dans l'inventaire.</td></tr>`;
        return;
    }

    produits.forEach(p => {
        const tr = document.createElement('tr');
        tr.className = "hover:bg-slate-50 transition-colors group";
        
        let badgeColor = p.quantite <= 5 ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700';
        if (p.quantite === 0) badgeColor = 'bg-red-100 text-red-700';

        tr.innerHTML = `
            <td class="px-6 py-4 text-sm text-slate-500 font-mono">#${p.id}</td>
            <td class="px-6 py-4">
                <div class="font-semibold text-slate-800">${p.nom}</div>
            </td>
            <td class="px-6 py-4">
                <span class="px-2 py-1 rounded text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
                    ${p.categorie || 'Sans catégorie'}
                </span>
            </td>
            <td class="px-6 py-4">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${badgeColor}">
                    ${p.quantite} en stock
                </span>
            </td>
            <td class="px-6 py-4 text-right">
                <div class="flex items-center justify-end space-x-3">
                    <div class="flex items-center bg-slate-100 rounded-lg p-1 border border-slate-200">
                        <input type="number" id="delta-${p.id}" placeholder="±" step="1" 
                            class="w-16 bg-transparent text-center text-sm font-medium outline-none border-none focus:ring-0">
                        <button onclick="appliquerDelta(${p.id})" 
                            class="bg-white text-indigo-600 hover:bg-indigo-600 hover:text-white p-1.5 rounded-md shadow-sm transition-all text-xs font-bold">
                            VALIDER
                        </button>
                    </div>
                    <button onclick="supprimerProduit(${p.id})" 
                        class="text-slate-400 hover:text-red-600 transition-colors p-2" title="Supprimer">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function rechargerListe() {
    // On remet le texte de recherche dans l'input (pour que l'utilisateur voie toujours ce qu'il cherchait)
    document.getElementById('search').value = derniereRecherche;

    if (derniereRecherche) {
        // On refait exactement la même recherche
        try {
            const res = await fetch(`${API_BASE}/recherche?nom=${encodeURIComponent(derniereRecherche)}`);
            if (!res.ok) throw new Error('Erreur rechargement recherche');
            const resultats = await res.json();
            afficherProduits(resultats);
        } catch (err) {
            const tbody = document.getElementById('tbody');
            tbody.innerHTML = `<tr><td colspan="5" class="px-6 py-8 text-center text-red-500">${err.message}</td></tr>`;
        }
    } else {
        // Pas de recherche active → on recharge la liste complète
        chargerProduits();
    }
}

async function appliquerDelta(id) {
    const input = document.getElementById(`delta-${id}`);
    const delta = parseInt(input.value);

    if (isNaN(delta) || delta === 0) return;

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

        input.value = '';
        rechargerListe();  // ← Ici on utilise la fonction intelligente
    } catch (err) {
        alert('Erreur réseau : ' + err.message);
    }
}

async function addProduit() {
    const nomInput = document.getElementById('nom');
    const qteInput = document.getElementById('quantite');
    const catSelect = document.getElementById('categorie');
    
    const nom = nomInput.value.trim();
    const quantite = parseInt(qteInput.value);
    const categorie_id = parseInt(catSelect.value);
    const messageEl = document.getElementById('add-message');

    if (!nom || isNaN(quantite) || quantite < 0) {
        messageEl.textContent = 'Veuillez remplir tous les champs correctement.';
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE}/produits`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nom, quantite, categorie_id })
        });
        
        if (!res.ok) {
            const errorText = await res.json();
            throw new Error(errorText.error || 'Erreur lors de l\'ajout');
        }
        
        messageEl.textContent = '';
        nomInput.value = '';
        qteInput.value = '';
        rechargerListe();  // ← Changé ici aussi
        
        const btn = document.querySelector('button[onclick="addProduit()"]');
        const originalContent = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-check"></i> <span>Ajouté !</span>';
        btn.classList.replace('bg-indigo-600', 'bg-emerald-500');
        setTimeout(() => {
            btn.innerHTML = originalContent;
            btn.classList.replace('bg-emerald-500', 'bg-indigo-600');
        }, 2000);

    } catch (err) {
        messageEl.textContent = err.message;
    }
}

async function supprimerProduit(id) {
    if (!confirm('Voulez-vous vraiment supprimer ce produit de l\'inventaire ?')) return;
    try {
        const res = await fetch(`${API_BASE}/produits/${id}`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error('Erreur de suppression');
        rechargerListe();  // ← Changé ici aussi
    } catch (err) {
        alert('Erreur : ' + err.message);
    }
}

async function rechercher() {
    const query = document.getElementById('search').value.trim();
    derniereRecherche = query;  // on mémorise ce qu’on cherche

    if (!query) {
        chargerProduits();  // recherche vide → on montre tout
        return;
    }

    try {
        const res = await fetch(`${API_BASE}/recherche?nom=${encodeURIComponent(query)}`);
        if (!res.ok) throw new Error('Erreur de recherche');
        const resultats = await res.json();
        afficherProduits(resultats);
    } catch (err) {
        const tbody = document.getElementById('tbody');
        tbody.innerHTML = `<tr><td colspan="5" class="px-6 py-8 text-center text-red-500">${err.message}</td></tr>`;
    }
}