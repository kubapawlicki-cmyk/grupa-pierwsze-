import streamlit as st
import pandas as pd
from supabase import create_client, Client
import plotly.express as px

# Konfiguracja strony
st.set_page_config(page_title="Magazyn Pro", layout="wide")

# Inicjalizacja połączenia
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# Funkcja pobierania danych z czyszczeniem cache
def fetch_data():
    prod_resp = supabase.table("produkty").select("*").execute()
    kat_resp = supabase.table("kategorie").select("*").execute()
    return pd.DataFrame(prod_resp.data), pd.DataFrame(kat_resp.data)

try:
    df_p, df_k = fetch_data()

    if df_k.empty:
        st.warning("Baza kategorii jest pusta. Dodaj kategorie w panelu Supabase.")
        st.stop()

    kat_dict = dict(zip(df_k['id'], df_k['nazwa']))
    kat_rev = dict(zip(df_k['nazwa'], df_k['id']))

    st.title("📦 System Magazynowy")

    # --- DASHBOARD ---
    if not df_p.empty:
        df_p['kategoria_nazwa'] = df_p['kategoria_id'].map(kat_dict)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Liczba produktów", len(df_p))
        m2.metric("Wartość magazynu", f"{(df_p['cena'] * df_p['liczba']).sum():,.2f} zł")
        m3.metric("Stan całkowity", int(df_p['liczba'].sum()))

        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.pie(df_p, values='liczba', names='kategoria_nazwa', title="Udział kategorii (szt.)")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            # Alert niskiego stanu
            low_stock = df_p[df_p['liczba'] < 5]
            if not low_stock.empty:
                st.error("⚠️ Niskie stany magazynowe (poniżej 5 szt.):")
                st.dataframe(low_stock[['nazwa', 'liczba']], hide_index=True)

    # --- ZAKŁADKI ---
    tab1, tab2 = st.tabs(["📋 Lista Produktów", "➕ Dodaj Nowy"])

    with tab1:
        if not df_p.empty:
            st.dataframe(df_p[['nazwa', 'cena', 'liczba', 'kategoria_nazwa']], use_container_width=True)
        else:
            st.info("Magazyn jest pusty.")

    with tab2:
        with st.form("new_product"):
            name = st.text_input("Nazwa produktu")
            cat = st.selectbox("Kategoria", options=list(kat_rev.keys()))
            price = st.number_input("Cena", min_value=0.0)
            qty = st.number_input("Ilość", min_value=0)
            
            if st.form_submit_button("Zapisz"):
                if name:
                    supabase.table("produkty").insert({
                        "nazwa": name, "cena": price, 
                        "liczba": qty, "kategoria_id": kat_rev[cat]
                    }).execute()
                    st.success("Dodano produkt!")
                    st.rerun()

except Exception as e:
    st.error(f"Wystąpił błąd: {e}")
