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

model_input = st.text_input("📺Enter Model")
lot_input = st.text_input(" 🔢 Enter Lot Quantity")

run = st.button("🚀 Compare")

# ==============================
# KPI (DONUT)
# ==============================
def generate_pie_chart(df):

    conform = (df["Remark"] == "✅ Conform").sum()
    missing = (df["Remark"] == "❌ Missing item").sum()
    packing_only = (df["Remark"] == "📦 Packing only").sum()
    qty_missing = (df["Remark"] == "⚠ Qty missing").sum()
    ref_change = (df["Remark"] == "🔁 Reference Change").sum()

    labels = ["🟢 Conform", "🔴 Missing", "🔵 Packing Only", "🟠 Qty Missing", "🟣 Ref Change"]
    values = [conform, missing, packing_only, qty_missing, ref_change]

    colors = ["#2E7D32", "#C62828", "#1565C0", "#EF6C00", "#6A1B9A"]

    fig, ax = plt.subplots(figsize=(4, 4))

    wedges, texts, autotexts = ax.pie(
        values,
        labels=labels,
        colors=colors,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops=dict(width=0.4)  # DONUT
    )

    # centre vide + total
    total = sum(values)
    ax.text(0, 0, f"{total}\nTotal", ha="center", va="center", fontsize=12, fontweight="bold")

    ax.set_title("KPI Distribution")

    return fig

# ==============================
# TABLE COLOR (EXCEL EXPORT)
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
        "🔁 Reference Change": "D9D2E9"
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

# ==============================
# MAIN
# ==============================
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

    df = pd.merge(
        bom_g,
        packing_g,
        on="PN",
        how="outer",
        suffixes=("_BOM", "_Packing"),
        indicator=True
    )

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

    result = df[[
        "PN",
        "Description_BOM",
        "bom_qty",
        "packing_qty",
        "MP",
        "SAV",
        "Qty (MP+SAV)",
        "Balance",
        "Remark"
    ]].rename(columns={
        "Description_BOM": "Description",
        "bom_qty": "Qty BOM",
        "packing_qty": "Packing list qty"
    })

    st.session_state["result"] = result

# ==============================
# DISPLAY
# ==============================
if "result" in st.session_state:

    result = st.session_state["result"]

    st.success("Comparison completed ✅")

    # KPI DONUT
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        fig = generate_pie_chart(result)
        st.pyplot(fig)

    # TABLE COLOR (EXCEL STYLE VIEW)
    def highlight_remark_column(df):
        styles = []
        for val in df["Remark"]:
            if val == "✅ Conform":
                styles.append("background-color: #1B5E20; color: white;")
            elif val == "⚠ Qty missing":
                styles.append("background-color: #F57F17; color: black;")
            elif val == "❌ Missing item":
                styles.append("background-color: #B71C1C; color: white;")
            elif val == "📦 Packing only":
                styles.append("background-color: #0D47A1; color: white;")
            elif val == "🔁 Reference Change":
                styles.append("background-color: #6A1B9A; color: white;")
            else:
                styles.append("")
        style_df = pd.DataFrame("", index=df.index, columns=df.columns)
        style_df["Remark"] = styles
        return style_df

    st.dataframe(result.style.apply(highlight_remark_column, axis=None), use_container_width=True)

    # EXPORT EXCEL
    excel_file = export_excel(result)

    st.download_button(
        "📥 Download Excel Result",
        data=excel_file,
        file_name="BOM_vs_Packing.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
