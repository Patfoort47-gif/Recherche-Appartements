import random
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import folium_static

# Configuration de la page
st.set_page_config(
    page_title="Suivi de Recherche d'Appartements",
    page_icon="🏡",
    layout="wide",
)

# URL d'export CSV de votre Google Sheet
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

# Style CSS personnalisé pour des KPIs bien visibles, un tableau élégant et un design pro
st.markdown(
    """
    <style>
    .main {
        background-color: #f4f6f9;
    }
    /* Style des cartes KPI */
    .kpi-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        padding: 24px;
        border-radius: 14px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.06);
        text-align: center;
        border: 1px solid #e2e8f0;
        margin-bottom: 20px;
    }
    .kpi-title {
        font-size: 15px;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 36px;
        color: #1e293b;
        font-weight: 800;
    }
    /* Style des cartes RDV */
    .rdv-card {
        background-color: #ffffff;
        padding: 22px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border-left: 6px solid #ff4b4b;
        border-top: 1px solid #edf2f7;
        border-right: 1px solid #edf2f7;
        border-bottom: 1px solid #edf2f7;
    }
    /* Conteneur de la carte */
    .map-container {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #e2e8f0;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("🏡 Suivi de Recherche d'Appartements")
st.markdown(
    "Organisez, visitez et suivez vos coups de cœur à deux en toute simplicité."
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
  st.sidebar.header("🔍 Filtres & Recherche")

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

  budget_max = st.sidebar.slider(
      "Budget Loyer Max (€)", 400, 1500, max_loyer_val, 25
  )
  if "Loyer_Num" in df.columns:
    df = df[df["Loyer_Num"].fillna(budget_max) <= budget_max]

  # --- GROS KPIs VISUELS ---
  col_kpi1, col_kpi2 = st.columns(2)

  nb_annonces = len(df)
  loyer_moyen_val = (
      int(df["Loyer_Num"].mean())
      if "Loyer_Num" in df.columns and not df["Loyer_Num"].dropna().empty
      else 0
  )

  with col_kpi1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">📋 Annonces affichées</div>
            <div class="kpi-value">{nb_annonces}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  with col_kpi2:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">💰 Loyer Moyen</div>
            <div class="kpi-value">{loyer_moyen_val} €</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

  st.markdown("<br>", unsafe_allow_html=True)

  # --- ONGLETS PRINCIPAUX ---
  tab1, tab2, tab3, tab4 = st.tabs(
      [
          "📋 Tableau & Modifications",
          "📅 Planning des RDV",
          "🗺️ Carte Interactive",
          "➕ Ajouter un bien",
      ]
  )

  with tab1:
    st.subheader("📋 Tableau interactif des annonces")
    st.markdown(
        "Modifiez directement vos notes, avis ou statuts dans le tableau"
        " ci-dessous pour garder un suivi impeccable."
    )
    st.markdown("<br>", unsafe_allow_html=True)
    st.data_editor(
        df.drop(columns=["Loyer_Num"], errors="ignore"),
        use_container_width=True,
        num_rows="dynamic",
        key="main_editor",
    )

  with tab2:
    st.subheader("📅 Planning des RDV et Visites confirmées")
    st.markdown(
        "Retrouvez ici uniquement les appartements avec un rendez-vous ou une"
        " visite planifiée."
    )
    st.markdown("<br>", unsafe_allow_html=True)

    rdv_col = "RDV pris ?" if "RDV pris ?" in df.columns else None

    df_rdv = pd.DataFrame()
    if rdv_col:
      df_rdv = df[
          df[rdv_col].notna()
          & (df[rdv_col].astype(str).str.strip() != "")
          & (df[rdv_col].astype(str).str.lower() != "nan")
      ]

    if not df_rdv.empty:
      for index, row in df_rdv.iterrows():
        lien = row.get("Lien Annonce", "#")
        btn_html = ""
        if pd.notna(lien) and str(lien).startswith("http"):
          btn_html = f"<a href='{lien}' target='_blank' style='background-color: #ff4b4b; color: white; padding: 8px 14px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 14px; float: right;'>🔗 Voir l'annonce</a>"

        st.markdown(
            f"""
                <div class="rdv-card">
                    {btn_html}
                    <h3 style="margin-top:0; color: #1e293b;">🏠 {row.get('Ville / Quartier', 'Appartement')}</h3>
                    <p style="margin: 6px 0; color: #475569;"><b>💰 Loyer :</b> {row.get('Loyer', 'N/C')} | <b>📐 Surface :</b> {row.get('M²')} m² | <b>🚪 Pièces :</b> {row.get('Pièces')}</p>
                    <p style="margin: 6px 0; color: #475569;"><b>🏢 Agence / Contact :</b> {row.get('Agence', 'N/C')}</p>
                    <hr style="margin: 12px 0; border: none; border-top: 1px solid #e2e8f0;">
                    <p style="margin: 6px 0; color: #16a34a; font-size: 16px;"><b>📅 RDV :</b> {row.get('RDV pris ?')}</p>
                    {"<p style='margin: 6px 0; color: #334155;'><b>💬 Notes :</b> " + str(row.get('Réponse')) + "</p>" if pd.notna(row.get('Réponse')) and str(row.get('Réponse')).strip() != '' else ""}
                </div>
                """,
            unsafe_allow_html=True,
        )
    else:
      st.info(
          "Aucun rendez-vous n'est actuellement renseigné. Indiquez une"
          " information dans la colonne 'RDV pris ?' de votre Google Sheet pour"
          " qu'elle apparaisse ici."
      )

  with tab3:
    st.subheader("🗺️ Carte Interactive des Appartements")
    st.markdown(
        "Visualisez l'emplacement des biens. Cliquez sur un marqueur pour"
        " ouvrir l'infobulle et accéder au lien."
    )
    st.markdown("<br>", unsafe_allow_html=True)

    coords_villes = {
        "Arles": {"lat": 43.6767, "lon": 4.6278},
        "Saint-Gilles": {"lat": 43.6811, "lon": 4.4328},
        "Bellegarde": {"lat": 43.7533, "lon": 4.5158},
        "Garons": {"lat": 43.7844, "lon": 4.4372},
        "Fourques": {"lat": 43.6822, "lon": 4.6033},
        "Mas thibert": {"lat": 43.5858, "lon": 4.6897},
    }

    m = folium.Map(location=[43.6767, 4.6278], zoom_level=11, control_scale=True)

    if "Ville / Quartier" in df.columns:
      for index, row in df.iterrows():
        ville_text = str(row["Ville / Quartier"])
        base_coords = {"lat": 43.6767, "lon": 4.6278}
        for v_key, coords in coords_villes.items():
          if v_key.lower() in ville_text.lower():
            base_coords = coords
            break

        lat_var = base_coords["lat"] + random.uniform(-0.003, 0.003)
        lon_var = base_coords["lon"] + random.uniform(-0.003, 0.003)

        loyer = str(row.get("Loyer", "N/C"))
        surface = str(row.get("M²", "N/C"))
        pieces = str(row.get("Pièces", "N/C"))
        agence = str(row.get("Agence", "N/C"))
        lien = str(row.get("Lien Annonce", "#"))
        if not lien.startswith("http"):
          lien = "#"

        popup_html = f"""
                <div style="font-family: sans-serif; width: 210px;">
                    <b style="color: #1e293b; font-size: 14px;">{ville_text}</b><hr style="margin: 5px 0;">
                    <b>Loyer :</b> {loyer}<br>
                    <b>Surface :</b> {surface} m²<br>
                    <b>Pièces :</b> {pieces}<br>
                    <b>Agence :</b> {agence}<br><br>
                    <a href="{lien}" target="_blank" style="background-color: #ff4b4b; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold; text-align: center;">🔗 Voir l'annonce</a>
                </div>
                """

        folium.Marker(
            [lat_var, lon_var],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{loyer} - {ville_text}",
            icon=folium.Icon(color="red", icon="home", prefix="fa"),
        ).add_to(m)

    # Affichage de la carte dans un conteneur soigné
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    folium_static(m, width=1100, height=550)
    st.markdown("</div>", unsafe_allow_html=True)

  with tab4:
    st.subheader("➕ Ajouter un nouvel appartement")
    st.markdown(
        "Remplissez les informations ci-dessous pour générer la ligne à ajouter"
        " à votre Google Sheet."
    )
    st.markdown("<br>", unsafe_allow_html=True)

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