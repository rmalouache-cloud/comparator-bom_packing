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

st.markdown("## 📊 BOM vs Packing Comparison Tool ⚖️")

# ==============================
# INPUTS
# ==============================
bom_file = st.file_uploader("📄 Upload BOM file", type=["xlsx", "xls"])
packing_file = st.file_uploader("📦 Upload Packing file", type=["xlsx", "xls"])

model_input = st.text_input("📺 Enter Model")
lot_input = st.text_input("🔢 Enter Lot Quantity")

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
    ref_change = (df["Remark"] == "🔁 Reference change").sum()
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
# PIE CHART
# ==============================
def generate_pie_chart(df):

    labels = ["Conform", "Missing", "Packing Only", "Qty Missing", "Ref Change", "Replacement"]

    values = [
        (df["Remark"] == "✅ Conform").sum(),
        (df["Remark"] == "❌ Missing item").sum(),
        (df["Remark"] == "📦 Packing only").sum(),
        (df["Remark"] == "⚠ Qty missing").sum(),
        (df["Remark"] == "🔁 Reference change").sum(),
        (df["Remark"] == "🔄 Replacement").sum()
    ]

    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.set_title("KPI Distribution")

    return fig

# ==============================
# TABLE STYLE
# ==============================
def highlight_remark_column(df):

    styles = []

    for val in df["Remark"]:
        if val == "✅ Conform":
            styles.append("background-color:#1B5E20;color:white;font-weight:bold;")
        elif val == "⚠ Qty missing":
            styles.append("background-color:#F57F17;color:black;font-weight:bold;")
        elif val == "❌ Missing item":
            styles.append("background-color:#B71C1C;color:white;font-weight:bold;")
        elif val == "📦 Packing only":
            styles.append("background-color:#0D47A1;color:white;font-weight:bold;")
        elif val == "🔁 Reference change":
            styles.append("background-color:#6A1B9A;color:white;font-weight:bold;")
        elif val == "🔄 Replacement":
            styles.append("background-color:#283593;color:white;font-weight:bold;")
        else:
            styles.append("")

    style_df = pd.DataFrame("", index=df.index, columns=df.columns)
    style_df["Remark"] = styles
    return style_df

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

    # ==============================
    # ADD SELECT COLUMN (IMPORTANT FIX)
    # ==============================
    result["Select"] = False

    st.session_state["result"] = result
    st.session_state["data_ready"] = True

# ==============================
# DISPLAY SECTION
# ==============================
if "data_ready" in st.session_state and st.session_state["data_ready"]:

    result = st.session_state["result"]

    st.success("Comparison completed ✅")

    # ==============================
    # DATA EDITOR (SAFE)
    # ==============================
    edited_df = st.data_editor(
        result,
        use_container_width=True,
        num_rows="fixed",
        key="editor"
    )

    # 🔥 FIX IMPORTANT: force Select always exists
    if "Select" not in edited_df.columns:
        edited_df = result.copy()
        edited_df["Select"] = False

    edited_df["Select"] = edited_df["Select"].fillna(False).astype(bool)

    st.session_state["result"] = edited_df

    # ==============================
    # BUTTON REFERENCE CHANGE
    # ==============================
    if st.button("🔁 Reference Change"):

        selected_idx = edited_df[edited_df["Select"] == True].index.tolist()

        if len(selected_idx) < 2:
            st.warning("Select at least 2 articles")
        else:
            half = len(selected_idx) // 2

            for i, idx in enumerate(selected_idx):
                if i < half:
                    edited_df.at[idx, "Remark"] = "🔁 Reference change"
                else:
                    edited_df.at[idx, "Remark"] = "🔄 Replacement"

            st.session_state["result"] = edited_df
            st.success("Reference Change applied ✅")

    result = st.session_state["result"]

    # ==============================
    # KPI
    # ==============================
    show_kpis(result)

    st.markdown("---")

    # ==============================
    # STYLED TABLE
    # ==============================
    styled = result.style.apply(highlight_remark_column, axis=None)
    st.dataframe(styled, use_container_width=True)

    # ==============================
    # PIE CHART
    # ==============================
    st.markdown("### 📊 KPI Distribution")

    fig = generate_pie_chart(result)
    st.pyplot(fig)
