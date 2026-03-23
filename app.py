import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Image as RLImage
import tempfile

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
    total = len(df)
    conform = (df["Remark"] == "✅ Conform").sum()
    missing = (df["Remark"] == "❌ Missing item").sum()
    packing_only = (df["Remark"] == "📦 Packing only").sum()
    qty_missing = (df["Remark"] == "⚠ Qty missing").sum()
    ref_change = (df["Remark"] == "🔁 Reference Change").sum()

    st.markdown(f"### 📊 Total Articles: {total}")

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("✅ Conform", conform)
    c2.metric("❌ Missing", missing)
    c3.metric("📦 Packing only", packing_only)
    c4.metric("⚠ Qty missing", qty_missing)
    c5.metric("🔁 Ref Change", ref_change)

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
    ax.set_title("KPI Distribution (Articles)")
    return fig

# STYLE
def highlight_remark_column(df):
    styles = []
    for val in df["Remark"]:
        if val == "✅ Conform":
            styles.append("background-color: #1B5E20; color: white; font-weight: bold;")
        elif val == "⚠ Qty missing":
            styles.append("background-color: #F57F17; color: black; font-weight: bold;")
        elif val == "❌ Missing item":
            styles.append("background-color: #B71C1C; color: white; font-weight: bold;")
        elif val == "📦 Packing only":
            styles.append("background-color: #0D47A1; color: white; font-weight: bold;")
        elif val == "🔁 Reference Change":
            styles.append("background-color: #6A1B9A; color: white; font-weight: bold;")
        else:
            styles.append("")
    style_df = pd.DataFrame("", index=df.index, columns=df.columns)
    style_df["Remark"] = styles
    return style_df

# EXCEL
def export_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

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

    st.session_state["result"] = result
    st.session_state["data_ready"] = True

# DISPLAY
if "data_ready" in st.session_state:

    result = st.session_state["result"]

    show_kpis(result)

    st.dataframe(result.style.apply(highlight_remark_column, axis=None))

    # 👉 MANUAL REF CHANGE
    st.markdown("### 🔄 Manual Reference Change")

    editable = result.copy()
    editable["Select"] = False

    edited = st.data_editor(editable, use_container_width=True)

    if st.button("🔁 Apply Reference Change"):
        sel = edited[edited["Select"]]

        if len(sel) == 2:
            idx = sel.index
            new = sel.iloc[0].copy()
            new["PN"] = str(sel.iloc[0]["PN"]) + " → " + str(sel.iloc[1]["PN"])
            new["Remark"] = "🔁 Reference Change"

            result = result.drop(index=idx)
            result = pd.concat([result, pd.DataFrame([new])])

            st.session_state["result"] = result
            st.success("Done")

    st.download_button("Download Excel", export_excel(result))
