import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- POŁĄCZENIE ---
# Jeśli używasz Streamlit Cloud, dodaj te zmienne w Settings -> Secrets
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
except:
    URL = "TWÓJ_URL_Z_SUPABASE"
    KEY = "TWÓJ_KLUCZ_API_Z_SUPABASE"

supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Magazyn PRO", layout="wide")

# --- FUNKCJE POBIERANIA DANYCH ---
def fetch_data():
    # Pobieramy produkty i kategorie osobno, żeby uniknąć błędów relacji
    prod_resp = supabase.table("produkty").select("*").execute()
    kat_resp = supabase.table("kategorie").select("*").execute()
    
    df_p = pd.DataFrame(prod_resp.data)
    df_k = pd.DataFrame(kat_resp.data)
    
    return df_p, df_k

# --- GŁÓWNA LOGIKA ---
try:
    df_produkty, df_kategorie = fetch_data()

    # Tworzymy słownik ID -> Nazwa Kategorii dla łatwego wyświetlania
    kat_dict = dict(zip(df_kategorie['id'], df_kategorie['nazwa']))
    # Tworzymy słownik Nazwa -> ID dla formularza dodawania
    kat_reverse_dict = dict(zip(df_kategorie['nazwa'], df_kategorie['id']))

    st.title("📦 Panel Zarządzania Magazynem")

    # --- STATYSTYKI ---
    if not df_produkty.empty:
        c1, c2, c3 = st.columns(3)
        c1.metric("Wszystkie produkty", len(df_produkty))
        total_val = (df_produkty['cena'] * df_produkty['liczba']).sum()
        c2.metric("Wartość magazynu", f"{total_val:,.2f} zł")
        c3.metric("Liczba sztuk", int(df_produkty['liczba'].sum()))

    # --- DODAWANIE ---
    with st.expander("➕ Dodaj nowy produkt"):
        with st.form("add_form", clear_on_submit=True):
            name = st.text_input("Nazwa produktu")
            price = st.number_input("Cena", min_value=0.0)
            quantity = st.number_input("Ilość", min_value=0)
            category_name = st.selectbox("Kategoria", options=list(kat_reverse_dict.keys()))
            
            if st.form_submit_button("Zatwierdź"):
                if name:
                    supabase.table("produkty").insert({
                        "nazwa": name,
                        "cena": price,
                        "liczba": quantity,
                        "kategoria_id": kat_reverse_dict[category_name]
                    }).execute()
                    st.success("Dodano produkt!")
                    st.rerun()

    # --- LISTA I USUWANIE ---
    st.subheader("📋 Lista towarów")
    if not df_produkty.empty:
        # Mapujemy ID kategorii na nazwy dla użytkownika
        df_display = df_produkty.copy()
        df_display['kategoria'] = df_display['kategoria_id'].map(kat_dict)
        
        # Wyświetlanie wiersz po wierszu z przyciskiem usuń
        for _, row in df_display.iterrows():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
            col1.write(f"**{row['nazwa']}**")
            col2.write(f"📁 {row['kategoria']}")
            col3.write(f"{row['cena']} zł")
            col4.write(f"szt: {row['liczba']}")
            
            if col5.button("Usuń", key=f"del_{row['id']}"):
                supabase.table("produkty").delete().eq("id", row['id']).execute()
                st.rerun()
    else:
        st.info("Baza jest pusta.")

except Exception as e:
    st.error(f"Wystąpił błąd: {e}")
    st.info("Sprawdź czy tabele 'produkty' i 'kategorie' istnieją w Twoim Supabase.")
