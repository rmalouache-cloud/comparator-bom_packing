import streamlit as st
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt

st.set_page_config(layout="wide")

st.title("📊 BOM Comparator")

bom_file = st.file_uploader("BOM", type=["xlsx"])
pack_file = st.file_uploader("Packing", type=["xlsx"])

model = st.text_input("Model")
lot = st.text_input("Lot")

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

    df["Remark"] = df.apply(detect, axis=1)

    # 🔥 REF CHANGE FUSION VISUELLE
    df["Remark_display"] = df["Remark"]

    for i, r1 in df.iterrows():
        for j, r2 in df.iterrows():

            if i >= j:
                continue

            if (
                r1["Remark"] == "❌ Missing" and
                r2["Remark"] == "📦 Packing only" and
                r1["Description_BOM"] == r2["Description_BOM"] and
                abs(r1["MP"] - r2["packing_qty"]) <= 1
            ):
                df.at[i, "Remark_display"] = "🔁 Reference change"
                df.at[j, "Remark_display"] = "⬆️"   # effet fusion

    result = df[[
        "PN",
        "Description_BOM",
        "bom_qty",
        "packing_qty",
        "MP",
        "Total",
        "Remark_display"
    ]].rename(columns={
        "Description_BOM":"Description",
        "bom_qty":"Qty BOM",
        "packing_qty":"Packing",
        "Remark_display":"Status"
    })

    st.dataframe(result, use_container_width=True)

    # KPI FIX
    df_kpi = result[result["Status"] != "⬆️"]

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

    st.pyplot(fig)
