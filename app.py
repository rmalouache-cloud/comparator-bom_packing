import streamlit as st
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Alignment
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("📊 BOM Comparator PRO")

bom_file = st.file_uploader("BOM", type=["xlsx"])
pack_file = st.file_uploader("Packing", type=["xlsx"])

model = st.text_input("Model")
lot = st.text_input("Lot")

# ==============================
# KPI
# ==============================
def show_kpi(df):
    df_kpi = df[df["Status"] != "⬆️"]

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Conform", (df_kpi["Status"]=="✅ Conform").sum())
    c2.metric("Missing", (df_kpi["Status"]=="❌ Missing").sum())
    c3.metric("Packing", (df_kpi["Status"]=="📦 Packing only").sum())
    c4.metric("Qty Missing", (df_kpi["Status"]=="⚠ Qty missing").sum())
    c5.metric("Ref Change", (df_kpi["Status"]=="🔁 Reference change").sum())

# ==============================
# PIE CHART
# ==============================
def pie_chart(df):

    df_kpi = df[df["Status"] != "⬆️"]

    labels = ["Conform","Missing","Packing","Qty Missing","Ref Change"]
    values = [
        (df_kpi["Status"]=="✅ Conform").sum(),
        (df_kpi["Status"]=="❌ Missing").sum(),
        (df_kpi["Status"]=="📦 Packing only").sum(),
        (df_kpi["Status"]=="⚠ Qty missing").sum(),
        (df_kpi["Status"]=="🔁 Reference change").sum()
    ]

    fig, ax = plt.subplots(figsize=(2.5,2.5))

    wedges, _, autotexts = ax.pie(
        values,
        autopct=lambda p: f"{p:.1f}%" if p>3 else "",
        startangle=90
    )

    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(-0.6,0.5), fontsize=8)

    for t in autotexts:
        t.set_size(8)

    return fig

# ==============================
# EXPORT EXCEL
# ==============================
def export_excel(df, groups):

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    output.seek(0)
    wb = load_workbook(output)
    ws = wb.active

    col_status = list(df.columns).index("Status") + 1

    colors = {
        "✅ Conform": "C6EFCE",
        "❌ Missing": "FFC7CE",
        "📦 Packing only": "BDD7EE",
        "⚠ Qty missing": "FFEB9C",
        "🔁 Reference change": "D9B3FF"
    }

    for row in ws.iter_rows(min_row=2):
        status = row[col_status-1].value
        if status in colors:
            for cell in row:
                cell.fill = PatternFill(start_color=colors[status], end_color=colors[status], fill_type="solid")

    # fusion Excel
    for g in groups:
        r1, r2 = g[0]+2, g[1]+2
        ws.merge_cells(start_row=r1, start_column=col_status,
                       end_row=r2, end_column=col_status)

        ws.cell(row=r1, column=col_status).alignment = Alignment(horizontal="center", vertical="center")
        ws.cell(row=r2, column=col_status).value = None

    final = BytesIO()
    wb.save(final)
    final.seek(0)
    return final

# ==============================
# MAIN
# ==============================
if st.button("Compare"):

    lot = int(lot)

    bom = pd.read_excel(bom_file)
    pack = pd.read_excel(pack_file)

    pack["Model"] = pack["Model"].ffill()
    pack = pack[pack["Model"] == model]

    bom_g = bom.groupby(["PN","Description"])["bom_qty"].sum().reset_index()
    pack_g = pack.groupby(["PN","Description"])["packing_qty"].sum().reset_index()

    df = pd.merge(bom_g, pack_g, on="PN", how="outer", suffixes=("_BOM","_PACK"), indicator=True)

    df["bom_qty"] = df["bom_qty"].fillna(0)
    df["packing_qty"] = df["packing_qty"].fillna(0)
    df["Description_BOM"] = df["Description_BOM"].fillna(df["Description_PACK"])

    df["MP"] = df["bom_qty"] * lot
    df["Total"] = df["MP"] * 1.02

    def detect(r):
        if r["_merge"] == "left_only":
            return "❌ Missing"
        elif r["_merge"] == "right_only":
            return "📦 Packing only"
        elif r["packing_qty"] >= r["Total"]:
            return "✅ Conform"
        else:
            return "⚠ Qty missing"

    df["Status"] = df.apply(detect, axis=1)

    # REF CHANGE
    groups = []
    for i, r1 in df.iterrows():
        for j, r2 in df.iterrows():

            if i >= j:
                continue

            if (
                r1["Status"] == "❌ Missing" and
                r2["Status"] == "📦 Packing only" and
                r1["Description_BOM"] == r2["Description_BOM"] and
                abs(r1["MP"] - r2["packing_qty"]) <= 1
            ):
                df.at[i, "Status"] = "🔁 Reference change"
                df.at[j, "Status"] = "⬆️"
                groups.append([i, j])

    result = df[[
        "PN",
        "Description_BOM",
        "bom_qty",
        "packing_qty",
        "MP",
        "Total",
        "Status"
    ]].rename(columns={
        "Description_BOM":"Description",
        "bom_qty":"Qty BOM",
        "packing_qty":"Packing"
    })

    st.session_state["df"] = result
    st.session_state["groups"] = groups

# ==============================
# DISPLAY
# ==============================
if "df" in st.session_state:

    df = st.session_state["df"]

    show_kpi(df)

    st.markdown("### ✏️ Editable Table")

    edited = st.data_editor(df, use_container_width=True)

    if st.button("💾 Save"):
        st.session_state["df"] = edited
        st.success("Saved ✅")

    df = st.session_state["df"]

    st.markdown("### 📊 KPI Chart")
    st.pyplot(pie_chart(df))

    excel = export_excel(df, st.session_state["groups"])

    st.download_button("📥 Download Excel", excel, "result.xlsx")
