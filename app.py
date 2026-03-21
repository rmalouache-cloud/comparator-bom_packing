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
# EXPORT EXCEL (FUSION)
# ==============================
def export_excel(df, groups):

    output = BytesIO()
    df_export = df.copy()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_export.to_excel(writer, index=False)

    output.seek(0)
    wb = load_workbook(output)
    ws = wb.active

    status_col = list(df_export.columns).index("Status") + 1

    # couleurs
    colors = {
        "✅ Conform": "C6EFCE",
        "❌ Missing": "FFC7CE",
        "📦 Packing only": "BDD7EE",
        "⚠ Qty missing": "FFEB9C",
        "🔁 Reference change": "D9B3FF"
    }

    # appliquer couleurs
    for row in ws.iter_rows(min_row=2):
        status = row[status_col-1].value
        if status in colors:
            for cell in row:
                cell.fill = PatternFill(start_color=colors[status], end_color=colors[status], fill_type="solid")

    # 🔥 FUSION CELLULES
    for g in groups:
        if len(g) == 2:
            r1 = g[0] + 2
            r2 = g[1] + 2

            ws.merge_cells(start_row=r1, start_column=status_col,
                           end_row=r2, end_column=status_col)

            cell = ws.cell(row=r1, column=status_col)
            cell.alignment = Alignment(vertical="center", horizontal="center")

            ws.cell(row=r2, column=status_col).value = None

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

    # 🔥 DETECTION + GROUPES
    groups = []
    used = set()

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

    st.dataframe(result, use_container_width=True)

    # KPI + Graph
    st.pyplot(pie_chart(result))

    # EXPORT
    excel = export_excel(result, groups)

    st.download_button("📥 Download Excel (Fusion)", excel, "result.xlsx")
