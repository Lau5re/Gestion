# Gestion des Stocks

Projet étudiant : Système de gestion de stocks avec Flask + SQLite + frontend vanilla JS.

## Fonctionnalités
- CRUD complet (Create, Read, Update, Delete)
- Mise à jour concurrente protégée (verrouillage pessimiste avec threading.Lock)
- Recherche optimisée par nom (recherche binaire avec bisect)
- Intégrité : quantités positives uniquement
- Interface web simple

## Lancement
1. `pip install flask`
2. `python app.py`
3. Ouvrir http://127.0.0.1:5000