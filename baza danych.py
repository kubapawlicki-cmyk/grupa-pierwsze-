import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px  # Dodajemy do wykresów

# --- KONFIGURACJA ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
except:
    URL = "TWÓJ_URL"
    KEY = "TWÓJ_KLUCZ"

supabase: Client = create_client(URL, KEY)
st.set_page_config(page_title="Magazyn PRO v2", layout="wide")

# --- FUNKCJE ---
def fetch_data():
    prod_resp = supabase.table("produkty").select("*").execute()
    kat_resp = supabase.table("kategorie").select("*").execute()
    return pd.DataFrame(prod_resp.data), pd.DataFrame(kat_resp.data)

def ensure_categories(df_k):
    """Dodaje domyślne kategorie, jeśli tabela jest pusta"""
    if df_k.empty:
        default_kats = ["Elektronika", "AGD", "Biurowe", "Spożywcze", "Inne"]
        for cat in default_kats:
            supabase.table("kategorie").insert({"nazwa": cat}).execute()
        st.rerun()

# --- GŁÓWNA LOGIKA ---
try:
    df_p, df_k = fetch_data()
    ensure_categories(df_k)

    kat_dict = dict(zip(df_k['id'], df_k['nazwa']))
    kat_rev = dict(zip(df_k['nazwa'], df_k['id']))

    st.title("📦 Inteligentny Magazyn")

    # --- SIDEBAR (FILTRY) ---
    st.sidebar.header("🔍 Filtry")
    search = st.sidebar.text_input("Szukaj produktu")
    selected_cat = st.sidebar.multiselect("Filtruj kategoria", options=list(kat_rev.keys()))

    # --- STATYSTYKI ---
    if not df_p.empty:
        df_p['kategoria_nazwa'] = df_p['kategoria_id'].map(kat_dict)
        
        # Filtrowanie danych do wyświetlenia
        df_filtered = df_p.copy()
        if search:
            df_filtered = df_filtered[df_filtered['nazwa'].str.contains(search, case=False)]
        if selected_cat:
            df_filtered = df_filtered[df_filtered['kategoria_nazwa'].isin(selected_cat)]

        c1, c2, c3 = st.columns(3)
        c1.metric("Produkty", len(df_filtered))
        total_val = (df_filtered['cena'] * df_filtered['liczba']).sum()
        c2.metric("Wartość (PLN)", f"{total_val:,.2f} zł")
        c3.metric("Łączna ilość", int(df_filtered['liczba'].sum()))

        # --- WYKRESY ---
        st.markdown("---")
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.subheader("💰 Wartość wg kategorii")
            df_p['wartosc_total'] = df_p['cena'] * df_p['liczba']
            fig_pie = px.pie(df_p, values='wartosc_total', names='kategoria_nazwa', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_chart2:
            st.subheader("📊 Stan zapasów")
            fig_bar = px.bar(df_p, x='nazwa', y='liczba', color='kategoria_nazwa', text_auto=True)
            st.plotly_chart(fig_bar, use_container_width=True)

    # --- FORMULARZ DODAWANIA ---
    with st.expander("➕ Dodaj nowy towar"):
        with st.form("add_form", clear_on_submit=True):
            c_a, c_b = st.columns(2)
            name = c_a.text_input("Nazwa")
            cat_name = c_a.selectbox("Kategoria", options=list(kat_rev.keys()))
            price = c_b.number_input("Cena (zł)", min_value=0.0, step=0.1)
            qty = c_b.number_input("Ilość (szt)", min_value=0, step=1)
            
            if st.form_submit_button("Dodaj do bazy"):
                if name:
                    supabase.table("produkty").insert({
                        "nazwa": name, "cena": price, 
                        "liczba": qty, "kategoria_id": kat_rev[cat_name]
                    }).execute()
                    st.cache_data.clear() # Czyścimy cache po zmianach
                    st.success(f"Dodano: {name}")
                    st.rerun()

    # --- LISTA PRODUKTÓW ---
    st.subheader("📋 Aktualne stany")
    if not df_p.empty:
        # Tabela w ładniejszym formacie
        st.dataframe(
            df_filtered[['nazwa', 'kategoria_nazwa', 'cena', 'liczba']], 
            use_container_width=True,
            column_config={
                "cena": st.column_config.NumberColumn(format="%.2f zł"),
                "liczba": st.column_config.ProgressColumn(min_value=0, max_value=int(df_p['liczba'].max()))
            }
        )

        # Opcja usuwania w sekcji poniżej
        with st.expander("🗑️ Zarządzanie / Usuwanie"):
            for _, row in df_filtered.iterrows():
                col_del1, col_del2 = st.columns([5, 1])
                col_del1.write(f"{row['nazwa']} ({row['kategoria_nazwa']})")
                if col_del2.button("Usuń", key=f"del_{row['id']}"):
                    supabase.table("produkty").delete().eq("id", row['id']).execute()
                    st.cache_data.clear()
                    st.rerun()
    else:
        st.warning("Magazyn jest pusty. Dodaj pierwszy produkt!")

except Exception as e:
    st.error(f"Błąd krytyczny: {e}")
