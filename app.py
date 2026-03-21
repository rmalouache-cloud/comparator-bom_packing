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

    st.markdown(f"### 📊 Total Articles: {total}")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("✅ Conform", conform)
    c2.metric("❌ Missing", missing)
    c3.metric("📦 Packing only", packing_only)
    c4.metric("⚠ Qty missing", qty_missing)
    c5.metric("🔁 Ref change", ref_change)

# ==============================
# PIE CHART
# ==============================
def generate_pie_chart(df):

    labels = ["Conform", "Missing", "Packing Only", "Qty Missing", "Ref Change"]
    values = [
        (df["Remark"] == "✅ Conform").sum(),
        (df["Remark"] == "❌ Missing item").sum(),
        (df["Remark"] == "📦 Packing only").sum(),
        (df["Remark"] == "⚠ Qty missing").sum(),
        (df["Remark"] == "🔁 Reference change").sum()
    ]

    fig, ax = plt.subplots(figsize=(3, 3))

    wedges, texts, autotexts = ax.pie(
        values,
        autopct="%1.1f%%",
        startangle=90
    )

    ax.legend(
        wedges,
        labels,
        title="Status",
        loc="center left",
        bbox_to_anchor=(-0.5, 0.5)
    )

    ax.set_title("KPI Distribution")

    return fig

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
        "🔁 Reference change": "D9B3FF"
    }

    for row in ws.iter_rows(min_row=2):
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

    packing["Model"] = packing["Model"].astype(str).str.strip().replace("", None).ffill()
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

    # ==============================
    # AUTO DETECT REFERENCE CHANGE
    # ==============================
    df["RefGroup"] = None
    group_id = 1

    for i, row1 in df.iterrows():
        for j, row2 in df.iterrows():

            if i >= j:
                continue

            if (
                row1["Remark"] == "❌ Missing item" and
                row2["Remark"] == "📦 Packing only" and
                row1["Description_BOM"] == row2["Description_BOM"] and
                abs(row1["MP"] - row2["packing_qty"]) <= 1
            ):
                df.at[i, "Remark"] = "🔁 Reference change"
                df.at[j, "Remark"] = "🔁 Reference change"

                df.at[i, "RefGroup"] = group_id
                df.at[j, "RefGroup"] = group_id

                group_id += 1

    result = df[[
        "PN",
        "Description_BOM",
        "bom_qty",
        "packing_qty",
        "MP",
        "SAV",
        "Qty (MP+SAV)",
        "Balance",
        "Remark",
        "RefGroup"
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
if "data_ready" in st.session_state:

    result = st.session_state["result"]

    st.success("Comparison completed ✅")

    show_kpis(result)

    st.markdown("### ✏️ Editable Table")

    edited_df = st.data_editor(
        result,
        use_container_width=True,
        column_config={
            "Select": st.column_config.CheckboxColumn("Select")
        }
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔁 Mark as Reference Change"):
            edited_df.loc[edited_df["Select"], "Remark"] = "🔁 Reference change"
            st.session_state["result"] = edited_df
            st.success("Applied ✅")

    with col2:
        if st.button("💾 Save modifications"):
            st.session_state["result"] = edited_df
            st.success("Saved ✅")

    result = st.session_state["result"]

    # KPI Chart
    st.markdown("### 📊 KPI Distribution")
    fig = generate_pie_chart(result)
    st.pyplot(fig)

    # PDF
    img_buffer = BytesIO()
    fig.savefig(img_buffer, format="png")
    img_buffer.seek(0)

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
        tmp.write(img_buffer.getvalue())
        tmp_path = tmp.name

    doc.build([RLImage(tmp_path, width=300, height=300)])

    pdf_buffer.seek(0)

    st.download_button("📄 Download PDF", pdf_buffer, "KPI.pdf")

    # Excel
    excel_file = export_excel(result)

    st.download_button(
        "📥 Download Excel",
        data=excel_file,
        file_name="BOM_vs_Packing.xlsx"
    )
