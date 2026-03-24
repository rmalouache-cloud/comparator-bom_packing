import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Image as RLImage

# CONFIG
st.set_page_config(page_title="BOM Comparator", layout="wide")

# LOGO
try:
    logo = Image.open("logo.jfif")
    st.image(logo, width=1500)
except:
    st.title("BOM Comparator")

st.markdown("## 📊  BOM vs Packing Comparison Tool  ⚖️")

# INPUTS
bom_file = st.file_uploader("📄  Upload BOM file", type=["xlsx", "xls"])
packing_file = st.file_uploader("📦 Upload Packing file", type=["xlsx", "xls"])

model_input = st.text_input("📺Enter Model")
lot_input = st.text_input(" 🔢 Enter Lot Quantity")

run = st.button("🚀 Compare")

# KPI
def show_kpis(df):
    conform = (df["Remark"] == "✅ Conform").sum()
    missing = (df["Remark"] == "❌ Missing item").sum()
    packing_only = (df["Remark"] == "📦 Packing only").sum()
    qty_missing = (df["Remark"] == "⚠ Qty missing").sum()
    ref_change = (df["Remark"] == "🔁 Reference Change").sum()

    st.markdown("### 📊 KPI Summary")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("✅ Conform", conform)
    c2.metric("❌ Missing", missing)
    c3.metric("📦 Packing only", packing_only)
    c4.metric("⚠ Qty missing", qty_missing)
    c5.metric("🔁 Ref Change", ref_change)

    # 🎨 légende couleurs
    st.markdown("""
    🟢 Conform &nbsp;&nbsp;
    🔴 Missing &nbsp;&nbsp;
    🔵 Packing Only &nbsp;&nbsp;
    🟠 Qty Missing &nbsp;&nbsp;
    🟣 Ref Change
    """)

# PIE
def generate_pie_chart(df):
    conform = (df["Remark"] == "✅ Conform").sum()
    missing = (df["Remark"] == "❌ Missing item").sum()
    packing_only = (df["Remark"] == "📦 Packing only").sum()
    qty_missing = (df["Remark"] == "⚠ Qty missing").sum()
    ref_change = (df["Remark"] == "🔁 Reference Change").sum()

    labels = ["Conform", "Missing", "Packing Only", "Qty Missing", "Ref Change"]
    values = [conform, missing, packing_only, qty_missing, ref_change]

    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    return fig

# EXCEL EXPORT
def export_excel(df):

    # ❌ supprimer colonnes inutiles
    df_export = df.drop(columns=["Select"], errors="ignore")

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False)

    output.seek(0)
    wb = load_workbook(output)
    ws = wb.active

    color_map = {
        "✅ Conform": "C6EFCE",
        "⚠ Qty missing": "FFEB9C",
        "❌ Missing item": "FFC7CE",
        "📦 Packing only": "BDD7EE",
        "🔁 Reference Change": "D9D2E9",
        "🔄 Replacement": "B2EBF2"
    }

    for row in ws.iter_rows(min_row=2):
        remark = row[8].value
        if remark in color_map:
            for cell in row:
                cell.fill = PatternFill(start_color=color_map[remark], fill_type="solid")

    final = BytesIO()
    wb.save(final)
    final.seek(0)
    return final

# MAIN
if run:

    lot = int(lot_input)

    bom = pd.read_excel(bom_file)
    packing = pd.read_excel(packing_file)

    bom.columns = bom.columns.str.strip()
    packing.columns = packing.columns.str.strip()

    packing["Model"] = packing["Model"].astype(str).str.strip().replace("", None).ffill()
    packing_model = packing[packing["Model"] == model_input]

    bom_g = bom.groupby(["PN", "Description"])["bom_qty"].sum().reset_index()
    packing_g = packing_model.groupby(["PN", "Description"])["packing_qty"].sum().reset_index()

    df = pd.merge(bom_g, packing_g, on="PN", how="outer", suffixes=("_BOM", "_Packing"), indicator=True)

    df["bom_qty"] = df["bom_qty"].fillna(0)
    df["packing_qty"] = df["packing_qty"].fillna(0)

    df["MP"] = df["bom_qty"] * lot
    df["SAV"] = df["MP"] * 0.02
    df["Qty (MP+SAV)"] = df["MP"] + df["SAV"]
    df["Balance"] = df["packing_qty"] - df["Qty (MP+SAV)"]

    def detect(row):
        if row["_merge"] == "left_only":
            return "❌ Missing item"
        elif row["_merge"] == "right_only":
            return "📦 Packing only"
        elif row["packing_qty"] >= row["Qty (MP+SAV)"]:
            return "✅ Conform"
        else:
            return "⚠ Qty missing"

    df["Remark"] = df.apply(detect, axis=1)

    result = df[["PN","Description_BOM","bom_qty","packing_qty","MP","SAV","Qty (MP+SAV)","Balance","Remark"]]
    result.columns = ["PN","Description","Qty BOM","Packing list qty","MP","SAV","Qty (MP+SAV)","Balance","Remark"]

    result["Comment"] = ""
    result["Select"] = False

    st.session_state["result"] = result

# DISPLAY
if "result" in st.session_state:

    df = st.session_state["result"]

    show_kpis(df)

    st.markdown("---")

    # 🎨 colonne couleur visuelle
    df["Status"] = df["Remark"].apply(lambda x:
        "🟢" if x=="✅ Conform" else
        "🔴" if x=="❌ Missing item" else
        "🔵" if x=="📦 Packing only" else
        "🟠" if x=="⚠ Qty missing" else
        "🟣" if x=="🔁 Reference Change" else ""
    )

    edited = st.data_editor(df, use_container_width=True)

    st.session_state["result"] = edited

    # 🔁 REF CHANGE
    if st.button("🔁 Apply Reference Change"):

        selected = edited[edited["Select"] == True]

        if len(selected) == 2:
            idx = selected.index

            for i in idx:
                if edited.loc[i, "Remark"] == "❌ Missing item":
                    edited.loc[i, "Remark"] = "🔁 Reference Change"
                    edited.loc[i, "Comment"] = "Original BOM item"
                else:
                    edited.loc[i, "Remark"] = "🔄 Replacement"
                    edited.loc[i, "Comment"] = "Replacement item"

                edited.loc[i, "Select"] = False

            st.session_state["result"] = edited
            st.success("Reference Change applied")

    st.pyplot(generate_pie_chart(st.session_state["result"]))

    excel_file = export_excel(st.session_state["result"])

    st.download_button(
        "📥 Download Excel",
        data=excel_file.getvalue(),
        file_name="BOM_vs_Packing.xlsx"
    )
