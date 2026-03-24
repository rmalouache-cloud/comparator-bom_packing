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
# INPUT
# ==============================
bom_file = st.file_uploader("📄 BOM file", type=["xlsx", "xls"])
packing_file = st.file_uploader("📦 Packing file", type=["xlsx", "xls"])

model_input = st.text_input("📺 Model")
lot_input = st.text_input("🔢 Lot")

run = st.button("🚀 Compare")

# ==============================
# KPI
# ==============================
def show_kpis(df):

    st.markdown("### 📊 KPI")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("✅ Conform", (df["Remark"] == "Conform").sum())
    c2.metric("❌ Missing", (df["Remark"] == "Missing item").sum())
    c3.metric("📦 Packing only", (df["Remark"] == "Packing only").sum())
    c4.metric("🔁 Ref Change", (df["Remark"] == "Reference change").sum())

# ==============================
# PIE
# ==============================
def pie(df):

    labels = ["Conform", "Missing", "Packing only", "Reference change"]

    values = [
        (df["Remark"] == "Conform").sum(),
        (df["Remark"] == "Missing item").sum(),
        (df["Remark"] == "Packing only").sum(),
        (df["Remark"] == "Reference change").sum()
    ]

    fig, ax = plt.subplots()
    ax.pie(values, labels=labels, autopct="%1.1f%%")
    return fig

# ==============================
# PROCESS
# ==============================
if run:

    if not bom_file or not packing_file:
        st.error("Upload files")
        st.stop()

    lot = int(lot_input)

    bom = pd.read_excel(bom_file)
    packing = pd.read_excel(packing_file)

    bom.columns = bom.columns.str.strip()
    packing.columns = packing.columns.str.strip()

    packing_model = packing[packing["Model"].astype(str).str.strip() == model_input]

    bom_g = bom.groupby(["PN", "Description"])["bom_qty"].sum().reset_index()
    pack_g = packing_model.groupby(["PN", "Description"])["packing_qty"].sum().reset_index()

    df = pd.merge(bom_g, pack_g, on="PN", how="outer", suffixes=("_BOM", "_PACK"), indicator=True)

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
    ]].rename(columns={"Description_BOM": "Description"})

    st.session_state["result"] = result
    st.session_state["ready"] = True

# ==============================
# DISPLAY
# ==============================
if "ready" in st.session_state:

    df = st.session_state["result"]

    st.success("Ready ✅")

    # ==============================
    # TABLE (1 SEUL)
    # ==============================
    edited = st.data_editor(df, use_container_width=True)

    # ==============================
    # REFERENCE CHANGE BUTTON
    # ==============================
    if st.button("🔁 Reference Change"):

        # Missing → Reference change
        mask_missing = edited["Remark"] == "Missing item"
        edited.loc[mask_missing, "Remark"] = "Reference change"

        # Packing only → Replacement
        mask_pack = edited["Remark"] == "Packing only"
        edited.loc[mask_pack, "Remark"] = "Replacement"

        st.session_state["result"] = edited

        st.success("Updated ✅")

    df = st.session_state["result"]

    # ==============================
    # KPI + PIE
    # ==============================
    show_kpis(df)

    st.pyplot(pie(df))
