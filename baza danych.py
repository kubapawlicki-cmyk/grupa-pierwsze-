import streamlit as st
from supabase import create_client, Client

# Konfiguracja połączenia z Supabase
URL = "TWOJ_URL_SUPABASE"
KEY = "TWOJ_KLUCZ_API"
supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Zarządzanie Produktami", layout="centered")

st.title("📦 System Zarządzania Produktami")

# --- SEKCOJA 1: DODAWANIE PRODUKTU ---
st.subheader("Dodaj nowy produkt")

# Pobieranie kategorii do listy rozwijanej
categories_query = supabase.table("kategorie").select("id, nazwa").execute()
categories = {item['nazwa']: item['id'] for item in categories_query.data}

with st.form("add_form", clear_on_submit=True):
    nazwa = st.text_input("Nazwa produktu")
    liczba = st.number_input("Ilość (liczba)", min_value=0, step=1)
    cena = st.number_input("Cena", min_value=0.0, format="%.2f")
    kat_nazwa = st.selectbox("Kategoria", options=list(categories.keys()))
    
    submit_button = st.form_submit_button("Dodaj produkt")

    if submit_button:
        if nazwa:
            new_product = {
                "nazwa": nazwa,
                "liczba": liczba,
                "cena": cena,
                "kategoria_id": categories[kat_nazwa]
            }
            supabase.table("produkty").insert(new_product).execute()
            st.success(f"Dodano produkt: {nazwa}")
        else:
            st.error("Nazwa nie może być pusta!")

---

# --- SEKCOJA 2: LISTA I USUWANIE ---
st.subheader("Aktualna lista produktów")

# Pobranie produktów z dołączoną nazwą kategorii
products_query = supabase.table("produkty").select("id, nazwa, liczba, cena, kategorie(nazwa)").execute()

if products_query.data:
    for prod in products_query.data:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        
        col1.write(f"**{prod['nazwa']}** ({prod['kategorie']['nazwa']})")
        col2.write(f"{prod['cena']} zł")
        col3.write(f"Sztuk: {prod['liczba']}")
        
        if col4.button("Usuń", key=f"del_{prod['id']}"):
            supabase.table("produkty").delete().eq("id", prod['id']).execute()
            st.rerun()
else:
    st.info("Brak produktów w bazie.")
