import random
import folium
import gspread
import pandas as pd
import streamlit as st
from streamlit_folium import folium_static

# Configuration de la page
st.set_page_config(
    page_title="Suivi de Recherche d'Appartements",
    page_icon="🏡",
    layout="wide",
)

SPREADSHEET_NAME = (  # Assurez-vous que c'est le nom exact de votre Google Sheet
    "Appartements Arles"
)


# Connexion sécurisée avec affichage de l'erreur exacte si échec
@st.cache_resource
def init_connection():
  try:
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    spreadsheet = gc.open(SPREADSHEET_NAME)
    return spreadsheet
  except Exception as e:
    st.error(f"Détail technique de l'erreur Google Sheets : {e}")
    return None


spreadsheet = init_connection()


@st.cache_data(ttl=10)
def load_data_from_sheet():
  if spreadsheet:
    try:
      sheet = spreadsheet.worksheet("Listing")
      data = sheet.get_all_records()
      return pd.DataFrame(data)
    except Exception:
      # Fallback sur la première feuille si "Listing" échoue
      try:
        sheet = spreadsheet.get_worksheet(0)
        data = sheet.get_all_records()
        return pd.DataFrame(data)
      except Exception:
        pass
  # Fallback par défaut si pas de connexion API active
  fallback_url = "https://docs.google.com/spreadsheets/d/1kaozoe4IX09695Ibf-Cl99x3B0O_BSq954lCS_889xo/export?format=csv&gid=0"
  return pd.read_csv(fallback_url)


df = load_data_from_sheet()

# Style CSS 100% Mode Sombre soigné (sans blocs blancs parasites)
st.markdown(
    """
    <style>
    .main {
        background-color: #0e1117;
    }
    .kpi-card {
        background: linear-gradient(135deg, #1f2937 100%, #111827 0%);
        padding: 24px;
        border-radius: 14px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        text-align: center;
        border: 1px solid #374151;
        margin-bottom: 20px;
    }
    .kpi-title {
        font-size: 14px;
        color: #9ca3af;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    .kpi-value {
        font-size: 36px;
        color: #f9fafb;
        font-weight: 800;
    }
    .rdv-card {
        background-color: #1f2937;
        padding: 22px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
        margin-bottom: 15px;
        border-left: 6px solid #ef4444;
        border-top: 1px solid #374151;
        border-right: 1px solid #374151;
        border-bottom: 1px solid #374151;
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

  recherche_texte = st.sidebar.text_input(
      "Recherche rapide", placeholder="Ex: Agence, Centre..."
  )

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

  if recherche_texte:
    mask = df.astype(str).apply(
        lambda x: x.str.contains(recherche_texte, case=False, na=False)
    ).any(axis=1)
    df = df[mask]

  # --- KPIs ---
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

  # --- ONGLETS ---
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
        "Modifiez vos données ci-dessous et cliquez sur le bouton de"
        " synchronisation pour enregistrer les changements dans le Google"
        " Sheet."
    )

    edited_df = st.data_editor(
        df.drop(columns=["Loyer_Num"], errors="ignore"),
        use_container_width=True,
        num_rows="dynamic",
        key="main_editor",
    )

    if st.button("💾 Enregistrer les modifications dans le Google Sheet"):
      if spreadsheet:
        try:
          sheet = spreadsheet.worksheet("Listing")
          # Nettoyage et mise à jour de la feuille Google Sheet
          data_to_save = edited_df.fillna("").values.tolist()
          header = list(edited_df.columns)
          sheet.clear()
          sheet.update([header] + data_to_save)
          st.success(" Modifications enregistrées avec succès dans Google Sheets !")
          st.cache_data.clear()
        except Exception as e:
          st.error(f"Erreur lors de la synchronisation : {e}")
      else:
        st.error(
            "Connexion API Google Sheets non active. Vérifiez vos secrets"
            " Streamlit."
        )

  with tab2:
    st.subheader("📅 Planning des RDV et Visites confirmées")
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
          btn_html = f"<a href='{lien}' target='_blank' style='background-color: #ef4444; color: white; padding: 8px 14px; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 14px; float: right;'>🔗 Voir l'annonce</a>"

        st.markdown(
            f"""
                <div class="rdv-card">
                    {btn_html}
                    <h3 style="margin-top:0; color: #f9fafb;">🏠 {row.get('Ville / Quartier', 'Appartement')}</h3>
                    <p style="margin: 6px 0; color: #9ca3af;"><b>💰 Loyer :</b> {row.get('Loyer', 'N/C')} | <b>📐 Surface :</b> {row.get('M²')} m² | <b>🚪 Pièces :</b> {row.get('Pièces')}</p>
                    <p style="margin: 6px 0; color: #9ca3af;"><b>🏢 Agence / Contact :</b> {row.get('Agence', 'N/C')}</p>
                    <hr style="margin: 12px 0; border: none; border-top: 1px solid #374151;">
                    <p style="margin: 6px 0; color: #4ade80; font-size: 16px;"><b>📅 RDV :</b> {row.get('RDV pris ?')}</p>
                    {"<p style='margin: 6px 0; color: #d1d5db;'><b>💬 Notes :</b> " + str(row.get('Réponse')) + "</p>" if pd.notna(row.get('Réponse')) and str(row.get('Réponse')).strip() != '' else ""}
                </div>
                """,
            unsafe_allow_html=True,
        )
    else:
      st.info("Aucun rendez-vous n'est actuellement renseigné.")

  with tab3:
    st.subheader("🗺️ Carte Interactive des Appartements")

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
                <div style="font-family: sans-serif; width: 210px; color: #333;">
                    <b style="color: #111; font-size: 14px;">{ville_text}</b><hr style="margin: 5px 0;">
                    <b>Loyer :</b> {loyer}<br>
                    <b>Surface :</b> {surface} m²<br>
                    <b>Pièces :</b> {pieces}<br>
                    <b>Agence :</b> {agence}<br><br>
                    <a href="{lien}" target="_blank" style="background-color: #ef4444; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold; text-align: center;">🔗 Voir l'annonce</a>
                </div>
                """

        folium.Marker(
            [lat_var, lon_var],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{loyer} - {ville_text}",
            icon=folium.Icon(color="red", icon="home", prefix="fa"),
        ).add_to(m)

    # Affichage de la carte propre sans conteneur blanc parasite au-dessus
    folium_static(m, width=1150, height=550)

  with tab4:
    st.subheader("➕ Ajouter un nouvel appartement")
    st.markdown(
        "Remplissez le formulaire pour ajouter directement l'appartement dans"
        " votre Google Sheet."
    )
    st.markdown("<br>", unsafe_allow_html=True)

    with st.form("ajout_form", clear_on_submit=True):
      c1, c2, c3 = st.columns(3)
      with c1:
        n_loyer = st.text_input("Loyer (ex: 690€)")
        n_m2 = st.text_input("Surface (M²)")
        n_pieces = st.text_input("Pièces (ex: 3 Pièces)")
      with c2:
        n_ville = st.text_input("Ville / Quartier")
        n_lien = st.text_input("Lien de l'annonce")
        n_agence = st.text_input("Agence ou Particulier")
      with c3:
        n_nono = st.text_input("Avis Nono")
        n_victor = st.text_input("Avis Victor")
        n_rdv = st.text_input("RDV pris ?")

      submitted = st.form_submit_button(
          "Ajouter l'appartement au Google Sheet"
      )

      if submitted:
        if spreadsheet:
          try:
            sheet = spreadsheet.worksheet("Listing")
            # Création du nouveau ID automatique
            new_id = len(df) + 1
            new_row = [
                new_id,
                n_loyer,
                n_m2,
                n_pieces,
                n_ville,
                n_lien,
                n_agence,
                n_nono,
                n_victor,
                "",
                "",
                n_rdv,
                "",
            ]
            sheet.append_row(new_row)
            st.success(
                "Appartement ajouté avec succès et synchronisé dans le Google"
                " Sheet !"
            )
            st.cache_data.clear()
          except Exception as e:
            st.error(f"Erreur lors de l'ajout : {e}")
        else:
          st.error("Connexion Google Sheets non configurée.")

else:
  st.warning("Impossible de charger les données.")