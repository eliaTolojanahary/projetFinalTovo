# test_connection.py
import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="dwhImprimantes",
        user="postgres",
        password="NouveauMotDePasse"
    )
    print("✅ Connexion réussie !")
    conn.close()
except Exception as e:
    print(f"❌ Erreur : {e}")