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
    st.markdown(f"### 📊 Total Articles: {total}")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("✅ Conform", (df["Remark"] == "✅ Conform").sum())
    c2.metric("❌ Missing", (df["Remark"] == "❌ Missing item").sum())
    c3.metric("📦 Packing only", (df["Remark"] == "📦 Packing only").sum())
    c4.metric("⚠ Qty missing", (df["Remark"] == "⚠ Qty missing").sum())
    c5.metric("🔁 Ref Change", (df["Remark"] == "🔁 Reference change").sum())

# ==============================
# PIE CHART
# ==============================
def generate_pie_chart(df):

    labels = [
        "Conform",
        "Missing",
        "Packing Only",
        "Qty Missing",
        "Ref Change"
    ]

    values = [
        (df["Remark"] == "✅ Conform").sum(),
        (df["Remark"] == "❌ Missing item").sum(),
        (df["Remark"] == "📦 Packing only").sum(),
        (df["Remark"] == "⚠ Qty missing").sum(),
        (df["Remark"] == "🔁 Reference change").sum()
    ]

    colors = [
        "#2ecc71",
        "#e74c3c",
        "#f39c12",
        "#3498db",
        "#9b59b6"
    ]

    total = sum(values)

    legend_labels = [
        f"🟢 Conform ({values[0]/total*100:.1f}%)",
        f"🔴 Missing ({values[1]/total*100:.1f}%)",
        f"🟠 Packing Only ({values[2]/total*100:.1f}%)",
        f"🔵 Qty Missing ({values[3]/total*100:.1f}%)",
        f"🟣 Ref Change ({values[4]/total*100:.1f}%)"
    ]

    fig, ax = plt.subplots(figsize=(4, 4))

    wedges, _ = ax.pie(
        values,
        colors=colors,
        startangle=90
    )

    ax.set_title("KPI Distribution", fontsize=11)

    ax.legend(
        wedges,
        legend_labels,
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        fontsize=9
    )

    plt.tight_layout()

    return fig

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

    result["Select"] = False

    st.session_state["result"] = result
    st.session_state["data_ready"] = True

# ==============================
# DISPLAY
# ==============================
if "data_ready" in st.session_state and st.session_state["data_ready"]:

    st.success("Comparison completed ✅")

    # ==============================
    # ONLY SELECT IS EDITABLE
    # ==============================
    columns_config = {
        "PN": st.column_config.TextColumn(disabled=True),
        "Description": st.column_config.TextColumn(disabled=True),
        "Qty BOM": st.column_config.NumberColumn(disabled=True),
        "Packing list qty": st.column_config.NumberColumn(disabled=True),
        "MP": st.column_config.NumberColumn(disabled=True),
        "SAV": st.column_config.NumberColumn(disabled=True),
        "Qty (MP+SAV)": st.column_config.NumberColumn(disabled=True),
        "Balance": st.column_config.NumberColumn(disabled=True),
        "Remark": st.column_config.TextColumn(disabled=True),
        "Select": st.column_config.CheckboxColumn("Select")
    }

    edited_df = st.data_editor(
        st.session_state["result"],
        use_container_width=True,
        num_rows="fixed",
        key="editor",
        column_config=columns_config
    )

    st.session_state["result"] = edited_df.copy()

    # ==============================
    # REFERENCE CHANGE
    # ==============================
    if st.button("🔁 Reference Change"):

        selected_idx = edited_df[edited_df["Select"] == True].index.tolist()

        if len(selected_idx) < 2:
            st.warning("Select at least 2 articles")

        else:
            half = len(selected_idx) // 2

            updated_df = edited_df.copy()

            for i, idx in enumerate(selected_idx):
                if i < half:
                    updated_df.at[idx, "Remark"] = "🔁 Reference change"
                else:
                    updated_df.at[idx, "Remark"] = "📦 Replacement"

            st.session_state["result"] = updated_df
            st.rerun()

    result = st.session_state["result"]

    show_kpis(result)

    st.markdown("---")

    fig = generate_pie_chart(result)
    st.pyplot(fig)
