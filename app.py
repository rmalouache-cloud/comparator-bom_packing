def auto_ref_change(df):

    missing = df[df["Remark"] == "❌ Missing item"]
    packing = df[df["Remark"] == "📦 Packing only"]

    used_m = set()
    used_p = set()
    new_rows = []

    for i, m in missing.iterrows():
        for j, p in packing.iterrows():

            if i in used_m or j in used_p:
                continue

            if str(m["Description_BOM"]).strip().lower() == str(p["Description_BOM"]).strip().lower():

                new = m.copy()
                new["PN"] = str(m["PN"]) + " → " + str(p["PN"])
                new["packing_qty"] = p["packing_qty"]
                new["Remark"] = "🔁 Reference Change"

                new_rows.append(new)

                used_m.add(i)
                used_p.add(j)
                break

    df = df.drop(index=list(used_m) + list(used_p))

    if new_rows:
        df = pd.concat([df, pd.DataFrame(new_rows)])

    return df
