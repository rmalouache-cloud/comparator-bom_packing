import streamlit as st
import pandas as pd
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="BOM Comparator", layout="wide")

st.title("📊 BOM vs Packing Comparator")

# ==============================
# INPUTS
# ==============================
bom_file = st.file_uploader("📄 Upload BOM file", type=["xlsx", "xls"])
packing_file = st.file_uploader("📦 Upload Packing file", type=["xlsx", "xls"])

model_input = st.text_input("📺 Enter Model")
lot_input = st.text_input("🔢 Enter Lot Quantity")

run = st.button("🚀 Compare")

# ==============================
# KPI FUNCTION
# ==============================
def show_kpis(df):

    st.markdown("### 📊 KPI Summary")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("✅ Conform", (df["Remark"] == "Conform").sum())
    c2.metric("❌ Missing", (df["Remark"] == "Missing item").sum())
    c3.metric("📦 Packing only", (df["Remark"] == "Packing only").sum())
    c4.metric("🔁 Ref Change", (df["Remark"] == "Reference change").sum())

# ==============================
# PIE CHART
# ==============================
def generate_pie(df):

    labels = ["Conform", "Missing", "Packing only", "Reference change"]

    values = [
        (df["Remark"] == "Conform").sum(),
        (df["Remark"] == "Missing item").sum(),
        (df["Remark"] == "Packing only").sum(),
        (df["Remark"] == "Reference change").sum()
    ]

    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.set_title("KPI Distribution")

    return fig

# ==============================
# MAIN PROCESS
# ==============================
if run:

    if not bom_file or not packing_file:
        st.error("Please upload both files")
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

    packing_model = packing[
        packing["Model"].astype(str).str.strip() == model_input
    ]

    if packing_model.empty:
        st.error("Model not found")
        st.stop()

    # ==============================
    # GROUP DATA
    # ==============================
    bom_g = bom.groupby(["PN", "Description"])["bom_qty"].sum().reset_index()
    pack_g = packing_model.groupby(["PN", "Description"])["packing_qty"].sum().reset_index()

    df = pd.merge(
        bom_g,
        pack_g,
        on="PN",
        how="outer",
        suffixes=("_BOM", "_PACK"),
        indicator=True
    )

    df["bom_qty"] = df["bom_qty"].fillna(0)
    df["packing_qty"] = df["packing_qty"].fillna(0)

    df["Remark"] = df["_merge"].map({
        "both": "Conform",
        "left_only": "Missing item",
        "right_only": "Packing only"
    })

    result = df[[
        "PN",
        "Description_BOM",
        "bom_qty",
        "packing_qty",
        "Remark"
    ]].rename(columns={
        "Description_BOM": "Description"
    })

    st.session_state["result"] = result
    st.session_state["ready"] = True

# ==============================
# DISPLAY (1 TABLE ONLY)
# ==============================
if "ready" in st.session_state:

    df = st.session_state["result"]

    st.success("Comparison ready ✅")

    # ==============================
    # TABLE EDITABLE
    # ==============================
    edited_df = st.data_editor(df, use_container_width=True)

    # ==============================
    # REFERENCE CHANGE BUTTON
    # ==============================
    if st.button("🔁 Reference Change"):

        # Missing → Reference change
        edited_df.loc[
            edited_df["Remark"] == "Missing item",
            "Remark"
        ] = "Reference change"

        # Packing only → Replacement
        edited_df.loc[
            edited_df["Remark"] == "Packing only",
            "Remark"
        ] = "Replacement"

        st.session_state["result"] = edited_df

        st.success("Reference Change applied ✅")

    df = st.session_state["result"]

    # ==============================
    # KPI
    # ==============================
    show_kpis(df)

    # ==============================
    # PIE CHART
    # ==============================
    st.pyplot(generate_pie(df))
