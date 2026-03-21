import streamlit as st
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("📊 BOM vs Packing Comparator")

# ==============================
# INPUT
# ==============================
bom_file = st.file_uploader("Upload BOM", type=["xlsx"])
packing_file = st.file_uploader("Upload Packing", type=["xlsx"])

model = st.text_input("Model")
lot = st.number_input("Lot", min_value=1)

run = st.button("Compare")

# ==============================
# KPI SIMPLE
# ==============================
def show_kpis(df):

    conform = (df["Remark"] == "✅ Conform").sum()
    missing = (df["Remark"] == "❌ Missing item").sum()
    packing = (df["Remark"] == "📦 Packing only").sum()
    qty = (df["Remark"] == "⚠ Qty missing").sum()

    # 🔁 IMPORTANT : diviser par 2
    ref = (df["Remark"] == "🔁 Reference Change").sum() // 2

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Conform", conform)
    c2.metric("Missing", missing)
    c3.metric("Packing", packing)
    c4.metric("Qty Missing", qty)
    c5.metric("Ref Change", ref)

# ==============================
# MAIN
# ==============================
if run:

    bom = pd.read_excel(bom_file)
    packing = pd.read_excel(packing_file)

    bom.columns = bom.columns.str.strip()
    packing.columns = packing.columns.str.strip()

    packing["Model"] = packing["Model"].ffill()

    packing = packing[packing["Model"] == model]

    bom_g = bom.groupby("PN")["bom_qty"].sum().reset_index()
    packing_g = packing.groupby("PN")["packing_qty"].sum().reset_index()

    df = pd.merge(bom_g, packing_g, on="PN", how="outer", indicator=True)

    df["bom_qty"] = df["bom_qty"].fillna(0)
    df["packing_qty"] = df["packing_qty"].fillna(0)

    def remark(row):
        if row["_merge"] == "left_only":
            return "❌ Missing item"
        elif row["_merge"] == "right_only":
            return "📦 Packing only"
        elif row["packing_qty"] >= row["bom_qty"] * lot:
            return "✅ Conform"
        else:
            return "⚠ Qty missing"

    df["Remark"] = df.apply(remark, axis=1)

    df["Select"] = False

    st.session_state["df"] = df

# ==============================
# DISPLAY
# ==============================
if "df" in st.session_state:

    df = st.session_state["df"]

    edited = st.data_editor(df, use_container_width=True)

    # 🔁 BOUTON SIMPLE
    if st.button("🔁 Reference Change"):

        selected = edited[edited["Select"] == True].index

        if len(selected) != 2:
            st.warning("Select 2 rows only")
        else:
            edited.loc[selected, "Remark"] = "🔁 Reference Change"
            edited.loc[selected, "Select"] = False

            st.session_state["df"] = edited
            st.rerun()

    show_kpis(edited)

    # PIE SIMPLE
    fig, ax = plt.subplots()

    values = [
        (edited["Remark"] == "✅ Conform").sum(),
        (edited["Remark"] == "❌ Missing item").sum(),
        (edited["Remark"] == "📦 Packing only").sum(),
        (edited["Remark"] == "⚠ Qty missing").sum(),
        (edited["Remark"] == "🔁 Reference Change").sum() // 2
    ]

    labels = ["Conform", "Missing", "Packing", "Qty", "Ref Change"]

    ax.pie(values, labels=labels, autopct="%1.1f%%")
    st.pyplot(fig)
