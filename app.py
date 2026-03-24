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
# KPI
# ==============================
def show_kpis(df):
    total = len(df)

    conform = (df["Remark"] == "✅ Conform").sum()
    missing = (df["Remark"] == "❌ Missing item").sum()
    packing_only = (df["Remark"] == "📦 Packing only").sum()
    qty_missing = (df["Remark"] == "⚠ Qty missing").sum()
    ref_change = (df["Remark"] == "🔁 Reference Change").sum()
    replacement = (df["Remark"] == "🔄 Replacement").sum()

    st.markdown(f"### 📊 Total Articles: {total}")

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric("✅ Conform", conform)
    c2.metric("❌ Missing", missing)
    c3.metric("📦 Packing only", packing_only)
    c4.metric("⚠ Qty missing", qty_missing)
    c5.metric("🔁 Ref Change", ref_change)
    c6.metric("🔄 Replacement", replacement)

# ==============================
# PIE CHART (FIXED)
# ==============================
def generate_pie_chart(df):

    conform = (df["Remark"] == "✅ Conform").sum()
    missing = (df["Remark"] == "❌ Missing item").sum()
    packing_only = (df["Remark"] == "📦 Packing only").sum()
    qty_missing = (df["Remark"] == "⚠ Qty missing").sum()
    ref_change = (df["Remark"] == "🔁 Reference Change").sum()
    replacement = (df["Remark"] == "🔄 Replacement").sum()

    values = [conform, missing, packing_only, qty_missing, ref_change, replacement]

    labels = [
        "🟢 Conform",
        "🔴 Missing",
        "🔵 Packing Only",
        "🟠 Qty Missing",
        "🟣 Ref Change",
        "🟦 Replacement"
    ]

    colors = [
        "#2E7D32",
        "#C62828",
        "#1565C0",
        "#EF6C00",
        "#6A1B9A",
        "#00838F"
    ]

    fig, ax = plt.subplots(figsize=(6, 4))

    wedges, texts, autotexts = ax.pie(
        values,
        colors=colors,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops=dict(width=0.4)  # DONUT
    )

    # ❌ remove overlapping labels
    for t in texts:
        t.set_visible(False)

    ax.set_title("KPI Distribution (Articles)")

    total = sum(values)

    legend_labels = [
        f"{labels[i]} : {values[i]} ({values[i]/total*100:.1f}%)"
        for i in range(len(values)) if values[i] > 0
    ]

    ax.legend(
        wedges,
        legend_labels,
        loc="center left",
        bbox_to_anchor=(1, 0.5)
    )

    return fig

# ==============================
# TABLE STYLE
# ==============================
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
        elif val == "🔄 Replacement":
            styles.append("background-color: #00838F; color: white; font-weight: bold;")
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
        "🔁 Reference Change": "D9D2E9",
        "🔄 Replacement": "B2EBF2"
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
# MAIN
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

    result = df[
        [
            "PN",
            "Description_BOM",
            "bom_qty",
            "packing_qty",
            "MP",
            "SAV",
            "Qty (MP+SAV)",
            "Balance",
            "Remark"
        ]
    ].rename(columns={
        "Description_BOM": "Description",
        "bom_qty": "Qty BOM",
        "packing_qty": "Packing list qty"
    })

    result["Comment"] = ""
    result["Select"] = False

    st.session_state["result"] = result

# ==============================
# DISPLAY
# ==============================
if "result" in st.session_state:

    result = st.session_state["result"]

    st.success("Comparison completed ✅")

    show_kpis(result)

    st.markdown("---")

    st.dataframe(
        result.style.apply(highlight_remark_column, axis=None),
        use_container_width=True
    )

    st.markdown("### 📊 KPI Distribution")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        fig = generate_pie_chart(result)
        st.pyplot(fig)

    excel_file = export_excel(result)

    st.download_button(
        "📥 Download Excel Result",
        data=excel_file.getvalue(),
        file_name="BOM_vs_Packing.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
