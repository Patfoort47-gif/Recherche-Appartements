import pandas as pd
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Suivi de Recherche d'Appartements",
    page_icon="🏠",
    layout="wide",
)

# URL d'export CSV de votre Google Sheet (basée sur votre lien)
# Astuce : on remplace /edit?gid=0#gid=0 par /export?format=csv&gid=0
SHEET_URL = "https://docs.google.com/spreadsheets/d/1kaozoe4IX09695Ibf-Cl99x3B0O_BSq954lCS_889xo/export?format=csv&gid=0"


@st.cache_data(ttl=60)
def load_data():
  try:
    df = pd.read_csv(SHEET_URL)
    return df
  except Exception as e:
    st.error(f"Erreur lors du chargement du Google Sheet : {e}")
    return pd.DataFrame()


df = load_data()

st.title("🏠 Mon Suivi de Recherche d'Appartements (Arles & alentours)")
st.markdown(
    "Application interactive pour suivre, ajouter et modifier vos recherches"
    " d'appartements en toute simplicité."
)

if not df.empty:
  # --- BARRE LATÉRALE DE FILTRES ---
  st.sidebar.header("🔍 Filtres de recherche")

  # Filtre par Ville / Quartier si la colonne existe
  if "Ville / Quartier" in df.columns:
    villes = ["Toutes"] + list(df["Ville / Quartier"].dropna().unique())
    ville_choisie = st.sidebar.selectbox("Filtrer par Ville / Quartier", villes)
    if ville_choisie != "Toutes":
      df = df[df["Ville / Quartier"] == ville_choisie]

  # Filtre par Pièces
  if "Pièces" in df.columns:
    pieces = ["Toutes"] + list(df["Pièces"].dropna().unique())
    piece_choisie = st.sidebar.selectbox("Filtrer par Pièces", pieces)
    if piece_choisie != "Toutes":
      df = df[df["Pièces"] == piece_choisie]

  # --- AFFICHAGE PRINCIPAL ---
  st.subheader(
      f"📋 Liste des appartements ({len(df)} annonces correspondantes)"
  )

  # Tableau interactif modifiable ou consultable
  edited_df = st.data_editor(
      df,
      num_rows="dynamic",  # Permet d'ajouter des lignes facilement
      use_container_width=True,
      key="appartement_editor",
  )

  # --- SECTION AJOUT RAPIDE ---
  st.markdown("---")
  with st.expander("➕ Ajouter un nouvel appartement rapidement"):
    with st.form("add_form"):
      col1, col2, col3 = st.columns(3)
      with col1:
        n_loyer = st.text_input("Loyer (ex: 690€)")
        n_surf = st.text_input("Surface (M²)")
        n_pieces = st.text_input("Pièces (ex: 3 Pièces)")
      with col2:
        n_ville = st.text_input("Ville / Quartier")
        n_lien = st.text_input("Lien Annonce")
        n_agence = st.text_input("Agence / Particulier")
      with col3:
        n_nono = st.text_input("Avis Nono")
        n_victor = st.text_input("Avis Victor")
        n_rdv = st.text_input("RDV pris ?")

      submit_button = st.form_submit_button(
          "Ajouter à la liste (À copier/coller dans votre Sheet)"
      )

      if submit_button:
        st.success(
            "Appartement configuré ! Vous pouvez l'ajouter directement dans"
            " votre Google Sheet ou l'intégrer via l'éditeur ci-dessus."
        )

else:
  st.warning("Impossible de charger les données du Google Sheet pour l'instant.")
