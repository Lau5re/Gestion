from flask import Flask, render_template, jsonify, request
import sqlite3
import threading
from bisect import bisect_left

app = Flask(__name__)

# Verrou pour gérer les mises à jour concurrentes
lock = threading.Lock()

# Cache pour recherche optimisée (O(log n) au lieu de O(n))
produits_tries_cache = []
noms_tries_cache = []
cache_valide = False  # True = cache à jour, False = besoin rafraîchir

def init_db():
    """Crée la table produits si elle n'existe pas"""
    conn = sqlite3.connect('stock.db')
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

init_db()

@app.route('/')
def accueil():
    return render_template('index.html')

@app.route('/produits', methods=['GET'])
def get_produits():
    """Retourne tous les produits et met à jour le cache"""
    global produits_tries_cache, noms_tries_cache, cache_valide
    
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute("SELECT id, nom, quantite FROM produits")
    rows = c.fetchall()
    conn.close()
    
    produits = [{"id": row[0], "nom": row[1], "quantite": row[2]} for row in rows]
    
    # Mise à jour du cache trié pour recherche binaire
    produits_tries_cache = sorted(produits, key=lambda x: x['nom'].lower())
    noms_tries_cache = [p['nom'].lower() for p in produits_tries_cache]
    cache_valide = True
    
    return jsonify(produits)

@app.route('/produits', methods=['POST'])
def add_produit():
    """Ajoute un produit et invalide le cache"""
    global cache_valide
    
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
    
    cache_valide = False  # Cache invalide car nouveau produit
    
    return jsonify({"message": "Produit ajouté"}), 201

@app.route('/produits/<int:id>', methods=['PUT'])
def update_quantite(id):
    """Met à jour la quantité avec verrouillage concurrentiel"""
    global cache_valide
    
    data = request.json
    delta = int(data.get('delta', 0))
    
    if delta == 0:
        return jsonify({"error": "Delta requis et non nul"}), 400
    
    # Verrouillage pessimiste : un seul thread peut modifier à la fois
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
    
    cache_valide = False  # Cache invalide car quantité modifiée
    
    return jsonify({"message": f"Quantité mise à jour : {nouvelle_quantite}"}), 200

@app.route('/produits/<int:id>', methods=['DELETE'])
def delete_produit(id):
    """Supprime un produit et invalide le cache"""
    global cache_valide
    
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute("DELETE FROM produits WHERE id = ?", (id,))
    if c.rowcount == 0:
        conn.close()
        return jsonify({"error": "Produit non trouvé"}), 404
    conn.commit()
    conn.close()
    
    cache_valide = False  # Cache invalide car produit supprimé
    
    return jsonify({"message": "Produit supprimé"}), 200

@app.route('/recherche', methods=['GET'])
def recherche():
    """RECHERCHE OPTIMISÉE avec algorithme de recherche binaire (bisect)"""
    global produits_tries_cache, noms_tries_cache, cache_valide
    
    nom_recherche = request.args.get('nom', '').strip().lower()
    
    if not nom_recherche:
        return jsonify([])
    
    # Si cache pas valide, le mettre à jour
    if not cache_valide:
        conn = sqlite3.connect('stock.db')
        c = conn.cursor()
        c.execute("SELECT id, nom, quantite FROM produits")
        rows = c.fetchall()
        conn.close()
        
        produits = [{"id": row[0], "nom": row[1], "quantite": row[2]} for row in rows]
        produits_tries_cache = sorted(produits, key=lambda x: x['nom'].lower())
        noms_tries_cache = [p['nom'].lower() for p in produits_tries_cache]
        cache_valide = True
    
    if not produits_tries_cache:
        return jsonify([])
    
    # RECHERCHE BINAIRE : O(log n) au lieu de O(n)
    # bisect_left donne le premier index où le préfixe pourrait être inséré
    index_depart = bisect_left(noms_tries_cache, nom_recherche)
    resultats = []
    
    # On parcourt uniquement vers l'avant à partir du premier match trouvé par bisect_left
    index = index_depart
    while index < len(noms_tries_cache) and noms_tries_cache[index].startswith(nom_recherche):
        resultats.append(produits_tries_cache[index])
        index += 1
    
    return jsonify(resultats)

if __name__ == '__main__':
    app.run(debug=True)