import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from io import BytesIO
from PIL import Image
import matplotlib.pyplot as plt

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="BOM Comparator", layout="wide")

# ==============================
# LOGO
# ==============================
try:
    logo = Image.open("logo.jfif")
    st.image(logo, width=1200)
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
    st.markdown(f"### 📊 Total Articles: {len(df)}")

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("✅ Conform", (df["Remark"] == "✅ Conform").sum())
    c2.metric("❌ Missing", (df["Remark"] == "❌ Missing item").sum())
    c3.metric("📦 Packing only", (df["Remark"] == "📦 Packing only").sum())
    c4.metric("⚠ Qty missing", (df["Remark"] == "⚠ Qty missing").sum())
    c5.metric("🔁 Ref Change", (df["Remark"] == "🔁 Reference Change").sum())

# ==============================
# PIE CHART + LEGEND
# ==============================
def generate_kpi_chart(df):

    labels = ["Conform", "Missing", "Packing Only", "Qty Missing", "Ref Change"]

    values = [
        (df["Remark"] == "✅ Conform").sum(),
        (df["Remark"] == "❌ Missing item").sum(),
        (df["Remark"] == "📦 Packing only").sum(),
        (df["Remark"] == "⚠ Qty missing").sum(),
        (df["Remark"] == "🔁 Reference Change").sum(),
    ]

    colors = ["#2E7D32", "#C62828", "#1565C0", "#F9A825", "#6A1B9A"]

    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(values, colors=colors, startangle=90)
    ax.set_title("KPI Distribution")

    total = sum(values)

    return fig, labels, values, colors, total

# ==============================
# EXPORT EXCEL
# ==============================
def export_excel(df):

    df_export = df.drop(columns=["Select", "Comment"], errors="ignore")

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False, sheet_name="Result")

    output.seek(0)
    wb = load_workbook(output)
    ws = wb.active

    color_map = {
        "✅ Conform": "C6EFCE",
        "❌ Missing item": "FFC7CE",
        "📦 Packing only": "BDD7EE",
        "⚠ Qty missing": "FFEB9C",
        "🔁 Reference Change": "D9D2E9",
    }

    remark_col = None
    for i, cell in enumerate(ws[1], 1):
        if cell.value == "Remark":
            remark_col = i

    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        remark = row[remark_col - 1].value
        color = color_map.get(remark)

        if color:
            for cell in row:
                cell.fill = PatternFill(
                    start_color=color,
                    end_color=color,
                    fill_type="solid"
                )

    final = BytesIO()
    wb.save(final)
    final.seek(0)
    return final

# ==============================
# MAIN PROCESS
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
    packing_model = packing[packing["Model"] == model_input]

    if packing_model.empty:
        st.error("Model not found")
        st.stop()

    bom_g = bom.groupby(["PN", "Description"])["bom_qty"].sum().reset_index()
    packing_g = packing_model.groupby(["PN", "Description"])["packing_qty"].sum().reset_index()

    df = pd.merge(bom_g, packing_g, on=["PN", "Description"], how="outer", indicator=True)

    df["bom_qty"] = pd.to_numeric(df["bom_qty"], errors="coerce").fillna(0)
    df["packing_qty"] = pd.to_numeric(df["packing_qty"], errors="coerce").fillna(0)

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
        "PN", "Description", "bom_qty", "packing_qty",
        "MP", "SAV", "Qty (MP+SAV)", "Balance", "Remark"
    ]]

    result["Comment"] = ""
    result["Select"] = False

    st.session_state["result"] = result

# ==============================
# DISPLAY
# ==============================
if "result" in st.session_state:

    df = st.session_state["result"]

    st.success("Comparison completed ✅")

    show_kpis(df)

    # ==============================
    # TABLE
    # ==============================
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        key="table",
        column_config={
            "Select": st.column_config.CheckboxColumn("Select")
        }
    )

    # IMPORTANT: only update selection
    df["Select"] = edited_df["Select"]
    st.session_state["result"] = df

    # ==============================
    # REFERENCE CHANGE
    # ==============================
    if st.button("🔁 Apply Reference Change"):

        df = st.session_state["result"]
        selected = df[df["Select"] == True]

        if len(selected) != 2:
            st.warning("⚠ Select exactly 2 rows")

        else:
            idx = selected.index.tolist()
            remarks = selected["Remark"].tolist()

            if ("❌ Missing item" in remarks) and ("📦 Packing only" in remarks):

                for i in idx:
                    if df.loc[i, "Remark"] == "❌ Missing item":
                        df.loc[i, "Remark"] = "🔁 Reference Change"
                        df.loc[i, "Comment"] = "Original BOM item"
                        df.loc[i, "Select"] = False

                st.session_state["result"] = df
                st.success("🔁 Reference Change applied")

            else:
                st.error("❌ Need 1 Missing + 1 Packing only")

    # ==============================
    # KPI CHART
    # ==============================
    st.markdown("### 📊 KPI Distribution")

    fig, labels, values, colors, total = generate_kpi_chart(df)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.pyplot(fig)

    with col2:
        for label, value, color in zip(labels, values, colors):
            percent = (value / total * 100) if total else 0

            st.markdown(
                f"""
                <div style="display:flex;align-items:center;margin-bottom:8px;">
                    <div style="width:15px;height:15px;background:{color};margin-right:8px;"></div>
                    <b>{label}</b>: {value} ({percent:.1f}%)
                </div>
                """,
                unsafe_allow_html=True
            )

    # ==============================
    # EXPORT
    # ==============================
    excel_file = export_excel(df)

    st.download_button(
        "📥 Download Excel Result",
        data=excel_file.getvalue(),
        file_name="BOM_vs_Packing.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
