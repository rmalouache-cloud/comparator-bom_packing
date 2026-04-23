import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Image as RLImage
import tempfile

# ==============================
# CONFIGURATION DE LA PAGE
# ==============================
st.set_page_config(
    page_title="BOM Comparator", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================
# STYLES CSS PERSONNALISÉS
# ==============================
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1E3A8A;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #6B7280;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================
# LOGO ET TITRE
# ==============================
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        logo = Image.open("logo.jfif")
        st.image(logo, width=200)
    except:
        pass

st.markdown('<div class="main-header">📊 BOM Comparator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Outil de comparaison BOM vs Packing List</div>', unsafe_allow_html=True)

# ==============================
# SIDEBAR POUR LES INPUTS
# ==============================
with st.sidebar:
    st.markdown("## 📂 Upload des fichiers")
    bom_file = st.file_uploader("📄 BOM", type=["xlsx", "xls"], key="bom")
    packing_file = st.file_uploader("📦 Packing List", type=["xlsx", "xls"], key="packing")
    
    st.markdown("---")
    st.markdown("## 📝 Informations")
    model_input = st.text_input("📺 Modèle", placeholder="Ex: iPhone 13")
    lot_input = st.text_input("🔢 Quantité Lot", placeholder="Ex: 1000")
    
    st.markdown("---")
    run = st.button("🚀 Lancer la comparaison", use_container_width=True, type="primary")

# ==============================
# FONCTIONS UTILITAIRES
# ==============================
def show_kpis(df):
    """Affiche les KPIs avec des cartes stylisées"""
    total = len(df)
    conform = (df["Remark"] == "✅ Conform").sum()
    missing = (df["Remark"] == "❌ Missing item").sum()
    packing_only = (df["Remark"] == "📦 Packing only").sum()
    qty_missing = (df["Remark"] == "⚠ Qty missing").sum()
    
    # Métriques principales
    st.markdown("### 📈 Indicateurs de Performance")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📊 Total Articles", total)
    col2.metric("✅ Conformes", conform, delta=f"{conform/total*100:.1f}%" if total > 0 else "0%")
    col3.metric("❌ Manquants", missing, delta=f"-{missing/total*100:.1f}%" if total > 0 else "0%", delta_color="inverse")
    col4.metric("📦 Packing Only", packing_only, delta=f"{packing_only/total*100:.1f}%" if total > 0 else "0%")
    col5.metric("⚠️ Quantités", qty_missing, delta=f"{qty_missing/total*100:.1f}%" if total > 0 else "0%", delta_color="inverse")
    
    return total, conform, missing, packing_only, qty_missing

def generate_pie_chart(df):
    """Génère un graphique circulaire amélioré"""
    conform = (df["Remark"] == "✅ Conform").sum()
    missing = (df["Remark"] == "❌ Missing item").sum()
    packing_only = (df["Remark"] == "📦 Packing only").sum()
    qty_missing = (df["Remark"] == "⚠ Qty missing").sum()
    
    labels = ["✅ Conform", "❌ Missing", "📦 Packing Only", "⚠️ Qty Missing"]
    values = [conform, missing, packing_only, qty_missing]
    colors = ['#10B981', '#EF4444', '#3B82F6', '#F59E0B']
    explode = (0.05, 0.05, 0.05, 0.05)
    
    fig, ax = plt.subplots(figsize=(8, 6))
    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        autopct='%1.1f%%',
        startangle=90,
        colors=colors,
        explode=explode,
        shadow=True,
        textprops={'fontsize': 10, 'fontweight': 'bold'}
    )
    
    # Styliser les textes
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(11)
        autotext.set_fontweight('bold')
    
    ax.set_title("Distribution des Articles", fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    
    return fig

def color_remark_column(val):
    """Colorie la colonne Remark"""
    colors = {
        "✅ Conform": "background-color: #10B981; color: white; font-weight: bold; padding: 5px; border-radius: 5px;",
        "⚠ Qty missing": "background-color: #F59E0B; color: white; font-weight: bold; padding: 5px; border-radius: 5px;",
        "❌ Missing item": "background-color: #EF4444; color: white; font-weight: bold; padding: 5px; border-radius: 5px;",
        "📦 Packing only": "background-color: #3B82F6; color: white; font-weight: bold; padding: 5px; border-radius: 5px;"
    }
    return colors.get(val, "")

def highlight_dataframe(df):
    """Applique le style au dataframe"""
    styled_df = df.style
    
    # Styler la colonne Remark
    styled_df = styled_df.map(color_remark_column, subset=['Remark'])
    
    # Styler les colonnes numériques
    numeric_cols = ['Qty BOM', 'Packing list qty', 'MP', 'SAV', 'Qty (MP+SAV)', 'Balance']
    styled_df = styled_df.format({col: '{:.0f}' for col in numeric_cols if col in df.columns})
    
    return styled_df

def export_excel(df):
    """Exporte vers Excel avec mise en forme"""
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Résultats")
    
    output.seek(0)
    wb = load_workbook(output)
    ws = wb.active
    
    # Ajouter des couleurs
    color_map = {
        "✅ Conform": "92D050",
        "⚠ Qty missing": "FFC000",
        "❌ Missing item": "FF0000",
        "📦 Packing only": "00B0F0"
    }
    
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        remark_cell = row[8]  # Colonne Remark
        if remark_cell.value in color_map:
            color = color_map[remark_cell.value]
            for cell in row:
                cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
                if remark_cell.value == "❌ Missing item":
                    cell.font = cell.font.copy(color="FFFFFF")
    
    # Ajuster la largeur des colonnes
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 30)
        ws.column_dimensions[column_letter].width = adjusted_width
    
    final = BytesIO()
    wb.save(final)
    final.seek(0)
    return final

# ==============================
# LOGIQUE PRINCIPALE
# ==============================
if run:
    # Validation des inputs
    if not bom_file or not packing_file:
        st.error("⚠️ Veuillez uploader les deux fichiers")
        st.stop()
    
    if not model_input:
        st.error("⚠️ Veuillez entrer un modèle")
        st.stop()
    
    if not lot_input.isdigit():
        st.error("⚠️ La quantité lot doit être un nombre")
        st.stop()
    
    lot = int(lot_input)
    
    # Lecture des fichiers
    with st.spinner("📖 Lecture des fichiers..."):
        bom = pd.read_excel(bom_file)
        packing = pd.read_excel(packing_file)
        
        bom.columns = bom.columns.str.strip()
        packing.columns = packing.columns.str.strip()
        
        packing["Model"] = packing["Model"].astype(str).str.strip()
        packing["Model"] = packing["Model"].replace("", None).ffill()
    
    # Filtrage par modèle
    packing_model = packing[packing["Model"] == model_input]
    
    if packing_model.empty:
        st.error(f"⚠️ Modèle '{model_input}' non trouvé dans le fichier Packing")
        st.stop()
    
    # Traitement des données
    with st.spinner("🔄 Traitement des données..."):
        bom_g = bom.groupby(["PN", "Description"])["bom_qty"].sum().reset_index()
        packing_g = packing_model.groupby(["PN", "Description"])["packing_qty"].sum().reset_index()
        
        df = pd.merge(
            bom_g,
            packing_g,
            on="PN",
            how="outer",
            suffixes=("_BOM", "_Packing"),
            indicator=True
        )
        
        df["bom_qty"] = pd.to_numeric(df["bom_qty"], errors="coerce").fillna(0)
        df["packing_qty"] = pd.to_numeric(df["packing_qty"], errors="coerce").fillna(0)
        df["Description_BOM"] = df["Description_BOM"].fillna(df["Description_Packing"])
        
        df["MP"] = df["bom_qty"] * lot
        df["SAV"] = df["MP"] * 0.02
        df["Qty (MP+SAV)"] = df["MP"] + df["SAV"]
        df["Balance"] = df["packing_qty"] - df["Qty (MP+SAV)"]
        
        def detect_remark(row):
            if row["_merge"] == "left_only":
                return "❌ Missing item"
            elif row["_merge"] == "right_only":
                return "📦 Packing only"
            elif row["packing_qty"] >= row["Qty (MP+SAV)"]:
                return "✅ Conform"
            else:
                return "⚠ Qty missing"
        
        df["Remark"] = df.apply(detect_remark, axis=1)
        
        result = df[[
            "PN", "Description_BOM", "bom_qty", "packing_qty", 
            "MP", "SAV", "Qty (MP+SAV)", "Balance", "Remark"
        ]].rename(columns={
            "Description_BOM": "Description",
            "bom_qty": "Qty BOM",
            "packing_qty": "Packing list qty"
        })
    
    st.session_state["result"] = result
    st.session_state["data_ready"] = True

# ==============================
# AFFICHAGE DES RÉSULTATS
# ==============================
if "data_ready" in st.session_state and st.session_state["data_ready"]:
    result = st.session_state["result"]
    
    # Message de succès
    st.balloons()
    st.success("✅ Comparaison terminée avec succès !")
    
    # KPIs
    total, conform, missing, packing_only, qty_missing = show_kpis(result)
    
    # Créer deux colonnes pour le graphique et le tableau
    col_left, col_right = st.columns([1, 2])
    
    with col_left:
        st.markdown("### 📊 Distribution")
        fig = generate_pie_chart(result)
        st.pyplot(fig, use_container_width=True)
        
        # Bouton PDF
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format="png", dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(img_buffer.getvalue())
            tmp_path = tmp.name
        
        elements = [RLImage(tmp_path, width=350, height=350)]
        doc.build(elements)
        pdf_buffer.seek(0)
        
        st.download_button(
            "📄 Télécharger graphique (PDF)",
            data=pdf_buffer,
            file_name="KPI_Chart.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    with col_right:
        st.markdown("### 📋 Détail des articles")
        styled_df = highlight_dataframe(result)
        st.dataframe(styled_df, use_container_width=True, height=400)
    
    # Section export
    st.markdown("---")
    col_export1, col_export2, col_export3 = st.columns([1, 1, 1])
    
    with col_export2:
        excel_file = export_excel(result)
        st.download_button(
            "📥 Télécharger rapport Excel",
            data=excel_file,
            file_name=f"BOM_vs_Packing_{model_input}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary"
        )
