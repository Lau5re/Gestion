from flask import Flask, render_template, jsonify, request
import sqlite3
import threading
from bisect import bisect_left

app = Flask(__name__)

# Verrou pour gérer les mises à jour concurrentes
lock = threading.Lock()

# Cache pour recherche optimisée
produits_tries_cache = []
noms_tries_cache = []
cache_valide = False

def init_db():
    """Crée les tables produits et categories si elles n'existent pas"""
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    
    # Table des catégories
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Table des produits avec clé étrangère vers catégories
    c.execute('''
        CREATE TABLE IF NOT EXISTS produits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            quantite INTEGER NOT NULL CHECK(quantite >= 0),
            categorie_id INTEGER,
            FOREIGN KEY (categorie_id) REFERENCES categories (id)
        )
    ''')
    
    # Insérer les catégories par défaut si elles n'existent pas
    categories_defaut = ['Informatique', 'Électroménager', 'Montres']
    for cat in categories_defaut:
        c.execute("INSERT OR IGNORE INTO categories (nom) VALUES (?)", (cat,))
        
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def accueil():
    return render_template('index.html')

@app.route('/categories', methods=['GET'])
def get_categories():
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute("SELECT id, nom FROM categories")
    rows = c.fetchall()
    conn.close()
    return jsonify([{"id": row[0], "nom": row[1]} for row in rows])

@app.route('/produits', methods=['GET'])
def get_produits():
    global produits_tries_cache, noms_tries_cache, cache_valide
    
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute('''
        SELECT p.id, p.nom, p.quantite, c.nom 
        FROM produits p 
        LEFT JOIN categories c ON p.categorie_id = c.id
    ''')
    rows = c.fetchall()
    conn.close()
    
    produits = [{"id": row[0], "nom": row[1], "quantite": row[2], "categorie": row[3]} for row in rows]
    
    produits_tries_cache = sorted(produits, key=lambda x: x['nom'].lower())
    noms_tries_cache = [p['nom'].lower() for p in produits_tries_cache]
    cache_valide = True
    
    return jsonify(produits)

@app.route('/produits', methods=['POST'])
def add_produit():
    global cache_valide
    
    data = request.json
    nom = data.get('nom')
    quantite = int(data.get('quantite', 0))
    categorie_id = data.get('categorie_id')
    
    if not nom or quantite < 0:
        return jsonify({"error": "Nom requis et quantité >= 0"}), 400
    
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute("INSERT INTO produits (nom, quantite, categorie_id) VALUES (?, ?, ?)", 
              (nom, quantite, categorie_id))
    conn.commit()
    conn.close()
    
    cache_valide = False
    return jsonify({"message": "Produit ajouté"}), 201

@app.route('/produits/<int:id>', methods=['PUT'])
def update_quantite(id):
    global cache_valide
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
    
    cache_valide = False
    return jsonify({"message": f"Quantité mise à jour : {nouvelle_quantite}"}), 200

@app.route('/produits/<int:id>', methods=['DELETE'])
def delete_produit(id):
    global cache_valide
    conn = sqlite3.connect('stock.db')
    c = conn.cursor()
    c.execute("DELETE FROM produits WHERE id = ?", (id,))
    if c.rowcount == 0:
        conn.close()
        return jsonify({"error": "Produit non trouvé"}), 404
    conn.commit()
    conn.close()
    
    cache_valide = False
    return jsonify({"message": "Produit supprimé"}), 200

@app.route('/recherche', methods=['GET'])
def recherche():
    global produits_tries_cache, noms_tries_cache, cache_valide
    nom_recherche = request.args.get('nom', '').strip().lower()
    
    if not nom_recherche:
        return jsonify([])
    
    if not cache_valide:
        get_produits()
    
    if not produits_tries_cache:
        return jsonify([])
    
    index_depart = bisect_left(noms_tries_cache, nom_recherche)
    resultats = []
    index = index_depart
    while index < len(noms_tries_cache) and noms_tries_cache[index].startswith(nom_recherche):
        resultats.append(produits_tries_cache[index])
        index += 1
    
    return jsonify(resultats)

if __name__ == '__main__':
    app.run(debug=True)
    
