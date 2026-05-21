
# PAGE 1 : VUE GLOBALE (OVERVIEW)

## BUT
Avoir une vision rapide et globale de la santé de l’entreprise.

## INDICATEURS (KPI)
- Chiffre d’affaires total (CA)
- Profit (CA - coûts)
- Quantité vendue
- Nombre de commandes
- Coût transport

## GRAPHIQUES

### 1. Graphique en courbes (évolution du CA)
- Axe X : dim_date[month_name]
- Valeur : Total CA

POURQUOI  
Permet de voir si les ventes augmentent ou diminuent dans le temps.

---

### 2. Graphique en barres horizontales (CA par vendeur)
- Axe : dim_seller[full_name]
- Valeur : Total CA

POURQUOI  
Permet de comparer rapidement les performances des vendeurs.

---

### 3. Graphique en colonnes (CA par produit)
- Axe : dim_product[product_name]
- Valeur : Total CA

POURQUOI  
Permet d’identifier les produits les plus rentables.

---

# PAGE 2 : VENDEURS

## BUT
Analyser la performance des commerciaux.

## GRAPHIQUES

### 1. Graphique en barres horizontales (CA par vendeur)
- Axe : dim_seller[full_name]
- Valeur : Total CA

POURQUOI  
Permet d’identifier les meilleurs et les moins performants.

---

### 2. Nuage de points (efficacité vendeur)
- Axe X : km_travelled
- Axe Y : net_sales_amount
- Détails : full_name

POURQUOI  
Permet d’analyser l’efficacité : comparer les ventes réalisées par rapport aux déplacements.

---

### 3. Tableau (classement vendeurs)
- Colonnes : vendeur, CA, km, profit

POURQUOI  
Donne une vue détaillée pour un classement précis.

---

# PAGE 3 : CLIENTS

## BUT
Analyser la rentabilité des clients.

## GRAPHIQUES

### 1. Graphique en barres horizontales (coût par client)
- Axe : customer_name
- Valeur : total_expense

POURQUOI  
Permet de voir quels clients coûtent le plus.

---

### 2. Graphique en barres horizontales (CA par client)
- Axe : customer_name
- Valeur : net_sales_amount

POURQUOI  
Permet d’identifier les clients les plus rentables.

---

### 3. Graphique combiné (CA vs coût)
- Axe : customer_name
- Valeurs : CA et coût

POURQUOI  
Permet de comparer directement revenu et dépenses pour chaque client.

---

# PAGE 4 : LOGISTIQUE

## BUT
Analyser les coûts liés aux déplacements et au transport.

## GRAPHIQUES

### 1. Graphique en barres horizontales (km par région)
- Axe : region_name
- Valeur : km_travelled

POURQUOI  
Permet d’identifier les zones les plus coûteuses en déplacement.

---

### 2. Graphique en colonnes (coût transport)
- Axe : region_name
- Valeur : total_expense

POURQUOI  
Permet de visualiser les dépenses liées au transport.

---

### 3. Graphique en nuage de points (carburant vs distance)
- Axe X : km_travelled
- Axe Y : fuel_amount

POURQUOI  
Permet d’analyser la relation entre distance parcourue et consommation de carburant.

---

# FILTRES (DANS TOUTES LES PAGES)

- Année : dim_date[year_num]
- Vendeur : dim_seller[full_name]
- Région : dim_customer[region_name]
- Produit : dim_product[product_name]

POURQUOI  
Les filtres permettent d’explorer les données selon différents critères et d’analyser des situations spécifiques.
