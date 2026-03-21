import streamlit as st
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")
st.title("📊 BOM vs Packing Comparator")

# ==============================
# UPLOAD
# ==============================
bom_file = st.file_uploader("Upload BOM", type=["xlsx"])
packing_file = st.file_uploader("Upload Packing", type=["xlsx"])

model = st.text_input("Model")
lot = st.number_input("Lot", min_value=1)

# ==============================
# FUNCTION REF CHANGE DETECTION
# ==============================
def detect_reference_change(df):

    missing = df[df["Remark"] == "❌ Missing item"]
    packing_only = df[df["Remark"] == "📦 Packing only"]

    ref_changes = []

    used_packing = set()

    for i, miss in missing.iterrows():
        for j, pack in packing_only.iterrows():

            if j in used_packing:
                continue

            # condition simple (tu peux améliorer)
            if miss["Description"] == pack["Description"]:

                ref_changes.append((i, j))
                used_packing.add(j)
                break

    return ref_changes


# ==============================
# RUN
# ==============================
if st.button("Compare"):

    bom = pd.read_excel(bom_file)
    packing = pd.read_excel(packing_file)

    bom_g = bom.groupby(["PN","Description"])["bom_qty"].sum().reset_index()
    packing_g = packing.groupby(["PN","Description"])["packing_qty"].sum().reset_index()

    df = pd.merge(bom_g, packing_g, on="PN", how="outer", indicator=True)

    df["bom_qty"] = df["bom_qty"].fillna(0)
    df["packing_qty"] = df["packing_qty"].fillna(0)

    df["MP"] = df["bom_qty"] * lot
    df["Qty"] = df["MP"] * 1.02
    df["Balance"] = df["packing_qty"] - df["Qty"]

    def remark(r):
        if r["_merge"] == "left_only":
            return "❌ Missing item"
        elif r["_merge"] == "right_only":
            return "📦 Packing only"
        elif r["packing_qty"] >= r["Qty"]:
            return "✅ Conform"
        else:
            return "⚠ Qty missing"

    df["Remark"] = df.apply(remark, axis=1)

    df["🔁 Ref Change"] = ""

    st.session_state.df = df

# ==============================
# DISPLAY
# ==============================
if "df" in st.session_state:

    df = st.session_state.df

    # 🔘 BUTTON AUTO DETECT
    if st.button("🔁 Auto Detect Reference Change"):

        pairs = detect_reference_change(df)

        for i, j in pairs:
            df.at[i, "🔁 Ref Change"] = "🔁 Reference Change"
            df.at[j, "🔁 Ref Change"] = "🔁 Reference Change"

        st.session_state.df = df

    # ==============================
    # KPI CORRIGÉ
    # ==============================
    ref_change_count = len(df[df["🔁 Ref Change"] == "🔁 Reference Change"]) // 2

    conform = (df["Remark"] == "✅ Conform").sum()
    missing = (df["Remark"] == "❌ Missing item").sum()
    packing_only = (df["Remark"] == "📦 Packing only").sum()
    qty_missing = (df["Remark"] == "⚠ Qty missing").sum()

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("✅ Conform", conform)
    col2.metric("❌ Missing", missing)
    col3.metric("📦 Packing Only", packing_only)
    col4.metric("⚠ Qty Missing", qty_missing)
    col5.metric("🔁 Ref Change", ref_change_count)

    st.markdown("---")

    # ==============================
    # COLOR TABLE
    # ==============================
    def style(row):
        if row["🔁 Ref Change"] == "🔁 Reference Change":
            return ["background-color: purple"] * len(row)
        if row["Remark"] == "❌ Missing item":
            return ["background-color: red"] * len(row)
        if row["Remark"] == "📦 Packing only":
            return ["background-color: blue"] * len(row)
        if row["Remark"] == "⚠ Qty missing":
            return ["background-color: orange"] * len(row)
        return [""] * len(row)

    st.dataframe(df.style.apply(style, axis=1), use_container_width=True)

    # ==============================
    # PIE
    # ==============================
    fig, ax = plt.subplots()

    values = [conform, missing, packing_only, qty_missing, ref_change_count]
    labels = ["Conform","Missing","Packing","Qty Missing","Ref Change"]

    ax.pie(values, labels=labels, autopct='%1.1f%%')

    st.pyplot(fig)

    # ==============================
    # EXPORT KPI
    # ==============================
    def export_kpi():

        kpi_df = pd.DataFrame({
            "Type": ["Conform","Missing","Packing Only","Qty Missing","Ref Change"],
            "Value": [conform, missing, packing_only, qty_missing, ref_change_count]
        })

        buffer = BytesIO()
        kpi_df.to_excel(buffer, index=False)
        buffer.seek(0)

        return buffer

    st.download_button(
        "📥 Download KPI",
        data=export_kpi(),
        file_name="KPI.xlsx"
    )
