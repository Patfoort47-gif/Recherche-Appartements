import random
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

# Configuration de la page
st.set_page_config(
    page_title="Suivi Avancé - Recherche Appartements",
    page_icon="🏡",
    layout="wide",
)

# URL d'export CSV de votre Google Sheet
SHEET_URL = "https://docs.google.com/spreadsheets/d/1kaozoe4IX09695Ibf-Cl99x3B0O_BSq954lCS_889xo/export?format=csv&gid=0"


@st.cache_data(ttl=30)
def load_data():
  try:
    df = pd.read_csv(SHEET_URL)
    return df
  except Exception as e:
    st.error(f"Erreur lors du chargement du Google Sheet : {e}")
    return pd.DataFrame()


df = load_data()

st.title("🏡 Super Suivi de Recherche d'Appartements")
st.markdown(
    "Application collaborative pour suivre, filtrer, cartographier et gérer"
    " vos visites à deux !"
)

if not df.empty:
  # Nettoyage sécurisé du loyer pour les filtres
  if "Loyer" in df.columns:
    df["Loyer_Num"] = (
        df["Loyer"]
        .astype(str)
        .str.replace("€", "", regex=True)
        .str.replace(" ", "", regex=True)
    )
    df["Loyer_Num"] = pd.to_numeric(df["Loyer_Num"], errors="coerce")

  # --- BARRE LATÉRALE DE FILTRES ---
  st.sidebar.header("🔍 Filtres & Paramètres")

  if "Ville / Quartier" in df.columns:
    villes = ["Toutes"] + list(df["Ville / Quartier"].dropna().unique())
    ville_choisie = st.sidebar.selectbox("Filtrer par Ville / Quartier", villes)
    if ville_choisie != "Toutes":
      df = df[df["Ville / Quartier"] == ville_choisie]

  if "Pièces" in df.columns:
    pieces = ["Toutes"] + list(df["Pièces"].dropna().unique())
    piece_choisie = st.sidebar.selectbox("Filtrer par Pièces", pieces)
    if piece_choisie != "Toutes":
      df = df[df["Pièces"] == piece_choisie]

  if "Loyer_Num" in df.columns and not df["Loyer_Num"].dropna().empty:
    max_loyer_val = int(df["Loyer_Num"].max())
  else:
    max_loyer_val = 1000

  budget_max = st.sidebar.slider("Budget Loyer Max (€)", 400, 1500, max_loyer_val, 25)
  if "Loyer_Num" in df.columns:
    df = df[df["Loyer_Num"].fillna(budget_max) <= budget_max]

  # --- KPIs ---
  col1, col2, col3, col4 = st.columns(4)
  col1.metric("Annonces affichées", len(df))
  if "Loyer_Num" in df.columns and not df["Loyer_Num"].dropna().empty:
    loyer_moyen = int(df["Loyer_Num"].mean())
    col2.metric("Loyer Moyen", f"{loyer_moyen} €")
  col3.metric("Visites / RDV", "À suivre")
  col4.metric("Mode", "Collaboratif 👥")

  # --- ONGLETS ---
  tab1, tab2, tab3 = st.tabs(
      ["📋 Tableau & Modifications", "🗺️ Carte Interactive", "➕ Ajouter un bien"]
  )

  with tab1:
    st.subheader("Tableau interactif des annonces")
    st.data_editor(
        df.drop(columns=["Loyer_Num"], errors="ignore"),
        use_container_width=True,
        num_rows="dynamic",
        key="main_editor",
    )

  with tab2:
    st.subheader("🗺️ Carte Interactive des Appartements")
    st.markdown(
        "Cliquez sur un marqueur pour afficher la bulle d'information, puis"
        " **cliquez sur le lien** pour ouvrir directement l'annonce."
    )

    coords_villes = {
        "Arles": {"lat": 43.6767, "lon": 4.6278},
        "Saint-Gilles": {"lat": 43.6811, "lon": 4.4328},
        "Bellegarde": {"lat": 43.7533, "lon": 4.5158},
        "Garons": {"lat": 43.7844, "lon": 4.4372},
        "Fourques": {"lat": 43.6822, "lon": 4.6033},
        "Mas thibert": {"lat": 43.5858, "lon": 4.6897},
    }

    # Création de la carte Folium centrée sur Arles
    m = folium.Map(location=[43.6767, 4.6278], zoom_level=11)

    if "Ville / Quartier" in df.columns:
      for index, row in df.iterrows():
        ville_text = str(row["Ville / Quartier"])
        base_coords = {"lat": 43.6767, "lon": 4.6278}
        for v_key, coords in coords_villes.items():
          if v_key.lower() in ville_text.lower():
            base_coords = coords
            break

        # Légère variation pour éviter les superpositions exactes
        lat_var = base_coords["lat"] + random.uniform(-0.003, 0.003)
        lon_var = base_coords["lon"] + random.uniform(-0.003, 0.003)

        loyer = str(row.get("Loyer", "N/C"))
        surface = str(row.get("M²", "N/C"))
        pieces = str(row.get("Pièces", "N/C"))
        agence = str(row.get("Agence", "N/C"))
        lien = str(row.get("Lien Annonce", "#"))
        if not lien.startswith("http"):
          lien = "#"

        # Contenu HTML du pop-up qui reste affiché au clic
        popup_html = f"""
                <div style="font-family: sans-serif; width: 200px;">
                    <b>{ville_text}</b><br>
                    <b>Loyer :</b> {loyer}<br>
                    <b>Surface :</b> {surface} m²<br>
                    <b>Pièces :</b> {pieces}<br>
                    <b>Agence :</b> {agence}<br><br>
                    <a href="{lien}" target="_blank" style="background-color: #ff4b4b; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold;">🔗 Voir l'annonce</a>
                </div>
                """

        folium.Marker(
            [lat_var, lon_var],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{loyer} - {ville_text}",
            icon=folium.Icon(color="red", icon="home", prefix="fa"),
        ).add_to(m)

    # Affichage de la carte dans Streamlit
    st_folium(m, width=1200, height=550)

  with tab3:
    st.subheader("➕ Ajouter un nouvel appartement")
    with st.form("ajout_appartement_form"):
      c1, c2, c3 = st.columns(3)
      with c1:
        f_loyer = st.text_input("Loyer (ex: 690€)")
        f_m2 = st.text_input("Surface (M²)")
        f_pieces = st.text_input("Pièces (ex: 3 Pièces)")
      with c2:
        f_ville = st.text_input("Ville / Quartier (ex: Arles Centre-ville)")
        f_lien = st.text_input("Lien de l'annonce")
        f_agence = st.text_input("Agence ou Particulier")
      with c3:
        f_nono = st.text_input("Avis Nono (ex: Oui++)")
        f_victor = st.text_input("Avis Victor (ex: Oui+)")
        f_rdv = st.text_input("RDV pris ?")

      submitted = st.form_submit_button("Générer les informations à copier")

      if submitted:
        st.success(
            "Appartement validé ! Vous pouvez copier ces informations et les"
            " coller tout en bas de votre Google Sheet partagé."
        )
        st.code(
            f"Loyer: {f_loyer} | M²: {f_m2} | Pièces: {f_pieces} | Ville:"
            f" {f_ville} | Lien: {f_lien} | Agence: {f_agence} | Nono:"
            f" {f_nono} | Victor: {f_victor} | RDV: {f_rdv}"
        )

else:
  st.warning("Impossible de charger les données.")