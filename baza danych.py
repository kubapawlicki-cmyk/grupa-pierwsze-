import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
except:
    # Do testów lokalnych:
    URL = "TWOJ_URL"
    KEY = "TWOJ_KLUCZ"

supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Magazyn PRO 2026", layout="wide", page_icon="🚀")

# --- STYLIZACJA ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_path=True)

st.title("🚀 Magazyn PRO v2.0")

# --- POBIERANIE DANYCH ---
@st.cache_data(ttl=10) # Odświeżaj co 10 sekund
def get_data():
    res_p = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
    res_k = supabase.table("kategorie").select("*").execute()
    return pd.DataFrame(res_p.data), {k['nazwa']: k['id'] for k in res_k.data}

try:
    df, kategorie_map = get_data()
    
    # Przetworzenie danych dla czytelności
    if not df.empty:
        df['nazwa_kategorii'] = df['kategorie'].apply(lambda x: x['nazwa'] if isinstance(x, dict) else "Brak")
        df['wartosc_razem'] = df['cena'] * df['liczba']

    # --- TOP METRICS (Dashboard) ---
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Liczba Produktów", len(df))
    with col_m2:
        st.metric("Łączna Wartość", f"{df['wartosc_razem'].sum():,.2f} zł")
    with col_m3:
        st.metric("Sztuk Razem", int(df['liczba'].sum()))
    with col_m4:
        st.metric("Kategorie", len(kategorie_map))

    st.divider()

    # --- BOCZNY PANEL (DODAWANIE) ---
    with st.sidebar:
        st.header("➕ Nowy Produkt")
        with st.form("add_form", clear_on_submit=True):
            n_nazwa = st.text_input("Nazwa")
            n_kat = st.selectbox("Kategoria", options=list(kategorie_map.keys()))
            n_cena = st.number_input("Cena", min_value=0.0)
            n_ilosc = st.number_input("Ilość", min_value=0)
            if st.form_submit_button("Dodaj do magazynu"):
                supabase.table("produkty").insert({
                    "nazwa": n_nazwa, "cena": n_cena, "liczba": n_ilosc, "kategoria_id": kategorie_map[n_kat]
                }).execute()
                st.success("Dodano!")
                st.rerun()

    # --- GŁÓWNY PANEL: FILTRY I WYKRESY ---
    tab1, tab2 = st.tabs(["📋 Lista Produktów", "📊 Analiza i Wykresy"])

    with tab1:
        search = st.text_input("🔍 Szukaj produktu po nazwie...", "")
        filtered_df = df[df['nazwa'].str.contains(search, case=False)] if search else df
        
        # Tabela edytowalna/podgląd
        st.dataframe(filtered_df[['nazwa', 'nazwa_kategorii', 'cena', 'liczba', 'wartosc_razem']], use_container_width=True)
        
        # Pobieranie CSV
        csv = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Pobierz raport CSV", csv, "magazyn.csv", "text/csv")

        st.subheader("🗑️ Szybkie usuwanie")
        to_delete = st.selectbox("Wybierz produkt do usunięcia", options=filtered_df['nazwa'].tolist())
        if st.button("Usuń wybrany produkt", type="primary"):
            id_del = filtered_df[filtered_df['nazwa'] == to_delete]['id'].values[0]
            supabase.table("produkty").delete().eq("id", id_del).execute()
            st.rerun()

    with tab2:
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.subheader("Wartość produktów wg kategorii")
            chart_data = df.groupby('nazwa_kategorii')['wartosc_razem'].sum()
            st.bar_chart(chart_data)
        
        with col_c2:
            st.subheader("Udział ilościowy")
            st.write("Liczba sztuk w podziale na kategorie")
            pie_data = df.groupby('nazwa_kategorii')['liczba'].sum()
            st.area_chart(pie_data)

except Exception as e:
    st.error(f"⚠️ Coś poszło nie tak: {e}")
    st.info("Upewnij się, że masz poprawnie ustawione relacje Foreign Key w Supabase.")
