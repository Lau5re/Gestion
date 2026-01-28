from flask import Flask, render_template, jsonify, request
import sqlite3
import threading
from bisect import bisect_left

app = Flask(__name__)

# Verrou pour gérer les mises à jour concurrentes (comme dans l'étude de cas)
lock = threading.Lock()

# Fonction pour initialiser la base de données (exécutée une seule fois)
def init_db():
    conn = sqlite3.connect('stock.db')  # Crée le fichier stock.db dans le dossier projet
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            quantite INTEGER NOT NULL CHECK(quantite >= 0)
        )
    ''')
    conn.commit()
    conn.close()
    print("Base de données initialisée (ou déjà existante)")

# Appel à l'initialisation au démarrage
init_db()

@app.route('/')
def accueil():
    return render_template('index.html')

# Endpoint pour lister tous les produits (JSON)
@app.route('/produits', methods=['GET'])
def get_produits():
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute("SELECT id, nom, quantite FROM produits")
    rows = c.fetchall()
    conn.close()
    
    produits = [{"id": row[0], "nom": row[1], "quantite": row[2]} for row in rows]
    return jsonify(produits)

# Endpoint pour ajouter un produit
@app.route('/produits', methods=['POST'])
def add_produit():
    data = request.json
    nom = data.get('nom')
    quantite = int(data.get('quantite', 0))
    
    if not nom or quantite < 0:
        return jsonify({"error": "Nom requis et quantité >= 0"}), 400
    
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute("INSERT INTO produits (nom, quantite) VALUES (?, ?)", (nom, quantite))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Produit ajouté"}), 201

# Endpoint pour mettre à jour la quantité (avec verrouillage pour éviter les problèmes concurrents)
@app.route('/produits/<int:id>', methods=['PUT'])
def update_quantite(id):
    data = request.json
    delta = int(data.get('delta', 0))

    if delta == 0:
        return jsonify({"error": "Delta requis et non nul"}), 400

    with lock:
        conn = sqlite3.connect('stock.db')
        c = conn.cursor()
        
        c.execute("SELECT quantite FROM produits WHERE id = ?", (id,))
        row = c.fetchone()
        
        if not row:
            conn.close()
            return jsonify({"error": "Produit non trouvé"}), 404
        
        nouvelle_quantite = row[0] + delta
        
        if nouvelle_quantite < 0:
            conn.close()
            return jsonify({"error": "Quantité insuffisante"}), 400
        
        c.execute("UPDATE produits SET quantite = ? WHERE id = ?", (nouvelle_quantite, id))
        conn.commit()
        conn.close()
    
    return jsonify({"message": f"Quantité mise à jour : {nouvelle_quantite}"}), 200

@app.route('/produits/<int:id>', methods=['DELETE'])
def delete_produit(id):
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute("DELETE FROM produits WHERE id = ?", (id,))
    if c.rowcount == 0:
        conn.close()
        return jsonify({"error": "Produit non trouvé"}), 404
    conn.commit()
    conn.close()
    return jsonify({"message": "Produit supprimé"}), 200


@app.route('/recherche', methods=['GET'])
def recherche():
    nom_recherche = request.args.get('nom', '').strip().lower()
    if not nom_recherche:
        return jsonify([])

    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute("SELECT id, nom, quantite FROM produits ORDER BY nom")
    produits = c.fetchall()
    conn.close()

    # Liste triée par nom (déjà triée par SQL)
    noms = [p[1].lower() for p in produits]

    # Recherche binaire avec bisect
    index = bisect_left(noms, nom_recherche)
    resultats = []
    while index < len(noms) and noms[index].startswith(nom_recherche):
        p = produits[index]
        resultats.append({"id": p[0], "nom": p[1], "quantite": p[2]})
        index += 1

    return jsonify(resultats)

if __name__ == '__main__':
    app.run(debug=True)

