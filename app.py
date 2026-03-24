# ==============================
# TABLE + REF CHANGE MODE
# ==============================

# bouton toggle
if "ref_change_mode" not in st.session_state:
    st.session_state["ref_change_mode"] = False

if st.button("🔁 Activer sélection Ref Change"):
    st.session_state["ref_change_mode"] = not st.session_state["ref_change_mode"]

# copie du dataframe
display_df = result.copy()

# SI MODE ACTIVÉ → ajouter colonne
if st.session_state["ref_change_mode"]:
    if "🔁 Ref Change" not in display_df.columns:
        display_df["🔁 Ref Change"] = False

    st.warning("Mode sélection activé : coche les articles concernés")

    edited_df = st.data_editor(
        display_df,
        use_container_width=True
    )

else:
    # mode normal sans checkbox
    styled = display_df.style.apply(highlight_remark_column, axis=1)
    st.write(styled)

    edited_df = display_df

# sauvegarde
st.session_state["result"] = edited_df
