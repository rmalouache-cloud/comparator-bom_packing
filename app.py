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
# CONFIG
# ==============================
st.set_page_config(page_title="BOM Comparator", layout="wide")

# ==============================
# LOGO
# ==============================
try:
    logo = Image.open("logo.jfif")
    st.image(logo, width=1500)
except:
    st.title("BOM Comparator")

st.markdown("## 📊  BOM vs Packing Comparison Tool  ⚖️")

# ==============================
# INPUTS
# ==============================
bom_file = st.file_uploader("📄  Upload BOM file", type=["xlsx", "xls"])
packing_file = st.file_uploader("📦 Upload Packing file", type=["xlsx", "xls"])

model_input = st.text_input("📺 Enter Model")
lot_input = st.text_input(" 🔢 Enter Lot Quantity")

run = st.button("🚀 Compare")

# ==============================
# KPI
# ==============================
def show_kpis(df):
    total = len(df)
    
    # Compter les articles uniques avec changement de référence
    # Chaque paire de changement compte comme 1 dans le compteur
    ref_change_pairs = len(st.session_state.get("ref_changes", {}))
    
    conform = (df["Remark"] == "✅ Conform").sum()
    missing = (df["Remark"] == "❌ Missing item").sum()
    packing_only = (df["Remark"] == "📦 Packing only").sum()
    qty_missing = (df["Remark"] == "⚠ Qty missing").sum()
    
    # Afficher le nombre de paires de changement, pas le nombre d'articles
    st.markdown(f"### 📊 Total Articles: {total}")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("✅ Conform", conform)
    c2.metric("❌ Missing", missing)
    c3.metric("📦 Packing only", packing_only)
    c4.metric("⚠ Qty missing", qty_missing)
    c5.metric("🔄 Ref Change", ref_change_pairs)  # Utiliser le nombre de paires

# ==============================
# PIE CHART
# ==============================
def generate_pie_chart(df):
    conform = (df["Remark"] == "✅ Conform").sum()
    missing = (df["Remark"] == "❌ Missing item").sum()
    packing_only = (df["Remark"] == "📦 Packing only").sum()
    qty_missing = (df["Remark"] == "⚠ Qty missing").sum()
    ref_change_pairs = len(st.session_state.get("ref_changes", {}))
    
    # Pour le graphique, on utilise le nombre de paires
    labels = ["Conform", "Missing", "Packing Only", "Qty Missing", "Ref Change"]
    values = [conform, missing, packing_only, qty_missing, ref_change_pairs]
    colors = ['#4CAF50', '#F44336', '#2196F3', '#FF9800', '#9C27B0']

    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors)
    ax.set_title("KPI Distribution (Articles)")
    return fig

# ==============================
# TABLE STYLE
# ==============================
def highlight_remark_column(df):
    styles = []
    for val in df["Remark"]:
        if val == "✅ Conform":
            styles.append("background-color: #4CAF50; color: white; font-weight: bold; border: 2px solid #2E7D32; border-radius: 5px;")
        elif val == "⚠ Qty missing":
            styles.append("background-color: #FF9800; color: white; font-weight: bold; border: 2px solid #E65100; border-radius: 5px;")
        elif val == "❌ Missing item":
            styles.append("background-color: #F44336; color: white; font-weight: bold; border: 2px solid #C62828; border-radius: 5px;")
        elif val == "📦 Packing only":
            styles.append("background-color: #2196F3; color: white; font-weight: bold; border: 2px solid #1565C0; border-radius: 5px;")
        elif val == "🔄 Reference Change":
            styles.append("background-color: #9C27B0; color: white; font-weight: bold; border: 2px solid #6A1B9A; border-radius: 5px;")
        else:
            styles.append("")
    
    style_df = pd.DataFrame("", index=df.index, columns=df.columns)
    style_df["Remark"] = styles
    return style_df

# ==============================
# EXCEL EXPORT
# ==============================
def export_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Result")
    output.seek(0)
    wb = load_workbook(output)
    ws = wb.active
    color_map = {
        "✅ Conform": "C6EFCE",
        "⚠ Qty missing": "FFEB9C",
        "❌ Missing item": "FFC7CE",
        "📦 Packing only": "BDD7EE",
        "🔄 Reference Change": "E6D0FF"
    }
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        remark = row[8].value
        color = color_map.get(remark)
        if color:
            for cell in row:
                cell.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
    final = BytesIO()
    wb.save(final)
    final.seek(0)
    return final

# ==============================
# MAIN CALCULATION
# ==============================
if run:
    if not bom_file or not packing_file:
        st.error("Upload both files")
        st.stop()
    if not model_input:
        st.error("Enter model")
        st.stop()
    if not lot_input.isdigit():
        st.error("Lot must be numeric")
        st.stop()
    lot = int(lot_input)
    bom = pd.read_excel(bom_file)
    packing = pd.read_excel(packing_file)
    bom.columns = bom.columns.str.strip()
    packing.columns = packing.columns.str.strip()
    packing["Model"] = packing["Model"].astype(str).str.strip()
    packing["Model"] = packing["Model"].replace("", None).ffill()
    packing_model = packing[packing["Model"] == model_input]
    if packing_model.empty:
        st.error("Model not found")
        st.stop()
    bom_g = bom.groupby(["PN", "Description"])["bom_qty"].sum().reset_index()
    packing_g = packing_model.groupby(["PN", "Description"])["packing_qty"].sum().reset_index()
    df = pd.merge(bom_g, packing_g, on="PN", how="outer", suffixes=("_BOM", "_Packing"), indicator=True)
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
    # Initialiser les changements de référence
    if "ref_changes" not in st.session_state:
        st.session_state["ref_changes"] = {}

# ==============================
# AFFICHAGE DES RÉSULTATS
# ==============================
if "data_ready" in st.session_state and st.session_state["data_ready"]:
    result = st.session_state["result"].copy()
    
    # Appliquer les changements de référence
    for old_ref, new_ref in st.session_state["ref_changes"].items():
        result.loc[result["PN"] == old_ref, "Remark"] = "🔄 Reference Change"
        result.loc[result["PN"] == new_ref, "Remark"] = "🔄 Reference Change"
    
    st.success("Comparison completed ✅")
    
    # 1. KPIs
    show_kpis(result)
    
    st.markdown("---")
    
    # 2. TABLEAU
    styled = result.style.apply(highlight_remark_column, axis=None)
    st.dataframe(styled, use_container_width=True)
    
    st.markdown("---")
    
    # 3. GESTION CHANGEMENT REFERENCE (version simple comme demandé)
    st.markdown("### 🔄 Gestion des changements de référence")
    
    missing_items = result[result["Remark"] == "❌ Missing item"]
    packing_items = result[result["Remark"] == "📦 Packing only"]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Ancienne référence (Missing)**")
        if not missing_items.empty:
            selected_missing = st.selectbox(
                "Sélectionner",
                options=missing_items["PN"].tolist(),
                key="missing_select"
            )
        else:
            st.info("Aucun")
            selected_missing = None
    
    with col2:
        st.markdown("**Nouvelle référence (Packing only)**")
        if not packing_items.empty:
            selected_packing = st.selectbox(
                "Sélectionner",
                options=packing_items["PN"].tolist(),
                key="packing_select"
            )
        else:
            st.info("Aucun")
            selected_packing = None
    
    if selected_missing and selected_packing:
        if st.button("🔄 Appliquer changement de référence"):
            # Vérifier si déjà existant
            if selected_missing not in st.session_state["ref_changes"]:
                st.session_state["ref_changes"][selected_missing] = selected_packing
                st.success(f"✅ Changement appliqué : {selected_missing} → {selected_packing}")
                st.rerun()
            else:
                st.warning("⚠️ Ce changement existe déjà")
    
    # Afficher les changements actuels
    if st.session_state["ref_changes"]:
        st.markdown("**Changements actifs :**")
        for old, new in st.session_state["ref_changes"].items():
            st.write(f"• {old} → {new}")
        
        if st.button("🗑️ Réinitialiser tout"):
            st.session_state["ref_changes"] = {}
            st.rerun()
    
    st.markdown("---")
    
    # 4. CERCLE APRÈS TABLEAU
    st.markdown("### 📊 KPI Distribution")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        fig = generate_pie_chart(result)
        st.pyplot(fig)
        
        # PDF Export
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format="png")
        img_buffer.seek(0)
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(img_buffer.getvalue())
            tmp_path = tmp.name
        elements = [RLImage(tmp_path, width=300, height=300)]
        doc.build(elements)
        pdf_buffer.seek(0)
        st.download_button(
            "📄 Download KPI Chart (PDF)",
            data=pdf_buffer,
            file_name="KPI_Chart.pdf",
            mime="application/pdf"
        )
    
    # EXCEL DOWNLOAD
    excel_file = export_excel(result)
    st.download_button(
        "📥 Download Excel Result",
        data=excel_file,
        file_name="BOM_vs_Packing.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
