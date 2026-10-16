# 🏡 Application de Suivi de Recherche d'Appartements

Une application web interactive développée avec **Streamlit** et **Python** pour organiser, filtrer, cartographier et suivre à deux votre recherche d'appartements en toute simplicité.

---

## ✨ Fonctionnalités principales

- **Tableau de bord & KPIs :** Visualisez rapidement le nombre d'annonces affichées et le loyer moyen calculé dynamiquement.
- **Filtres avancés :** Filtrez les annonces par recherche textuelle (mots-clés, agence), par ville/quartier, par nombre de pièces ou via un curseur de budget maximum.
- **Planning des RDV :** Un onglet dédié qui isole automatiquement les biens pour lesquels un rendez-vous ou une visite a été planifié.
- **Carte Interactive :** Visualisez l'emplacement des appartements sur une carte interactive (via `folium`) avec des marqueurs positionnés intelligemment et des pop-ups contenant les détails et un lien direct vers l'annonce.
- **Mode Sombre (Dark Mode) optimisé :** Une interface moderne et épurée conçue pour un confort visuel maximal.

---

## 🛠️ Stack Technique

- **Langage :** Python 3.10+
- **Framework Web :** Streamlit
- **Manipulation de données :** Pandas
- **Cartographie :** Folium, Streamlit-Folium
- **Source de données :** Google Sheets (synchro en lecture via export CSV public)

---

## 📁 Structure du Projet

```text
├── app.py               # Code source principal de l'application Streamlit
├── requirements.txt     # Liste des dépendances Python requises
└── README.md            # Documentation du projet