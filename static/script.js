const listeProduits = document.getElementById("liste-produits");
const form = document.getElementById("form-produit");

// Charger les produits au chargement de la page
fetch("/produits")
    .then(response => response.json())
    .then(produits => afficherProduits(produits));

function afficherProduits(produits) {
    listeProduits.innerHTML = "";

    produits.forEach(produit => {
        const ligne = document.createElement("tr");

        ligne.innerHTML = `
            <td>${produit.nom}</td>
            <td>${produit.quantite}</td>
            <td>
                <button onclick="changerQuantite(${produit.id}, 1)">+1</button>
                <button onclick="changerQuantite(${produit.id}, -1)">-1</button>
            </td>
        `;

        listeProduits.appendChild(ligne);
    });
}

// Ajouter un produit
form.addEventListener("submit", function (event) {
    event.preventDefault();

    const nom = document.getElementById("nom").value;
    const quantite = document.getElementById("quantite").value;

    fetch("/produits", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ nom, quantite })
    })
    .then(() => location.reload());
});

// Modifier la quantité
function changerQuantite(id, valeur) {
    fetch(`/produits/${id}`, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ valeur })
    })
    .then(() => location.reload());
}
