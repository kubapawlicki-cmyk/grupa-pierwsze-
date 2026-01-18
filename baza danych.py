import streamlit as st
from supabase import create_client, Client

# --- KONFIGURACJA POŁĄCZENIA ---
# Zalecane użycie st.secrets dla bezpieczeństwa na Streamlit Cloud
try:
    URL = st.secrets["SUPABASE_URL"]
    KEY = st.secrets["SUPABASE_KEY"]
except:
    # Jeśli uruchamiasz lokalnie i nie masz secrets, podaj dane tutaj:
    URL = "TWOJ_URL_Z_SUPABASE"
    KEY = "TWOJ_KLUCZ_API_Z_SUPABASE"

supabase: Client = create_client(URL, KEY)

st.set_page_config(page_title="Zarządzanie Magazynem", layout="wide")
st.title("📦 System Zarządzania Produktami")

# --- SEKCJA 1: DODAWANIE PRODUKTÓW ---
with st.expander("➕ Dodaj nowy produkt", expanded=False):
    # Pobieranie kategorii do listy rozwijanej
    try:
        kat_res = supabase.table("kategorie").select("id, nazwa").execute()
        kategorie = {item['nazwa']: item['id'] for item in kat_res.data}
        
        with st.form("dodaj_produkt_form", clear_on_submit=True):
            nazwa = st.text_input("Nazwa produktu")
            liczba = st.number_input("Ilość", min_value=0, step=1)
            cena = st.number_input("Cena (zł)", min_value=0.0, format="%.2f")
            kat_nazwa = st.selectbox("Kategoria", options=list(kategorie.keys()))
            
            if st.form_submit_button("Dodaj do bazy"):
                if nazwa:
                    data = {
                        "nazwa": nazwa,
                        "liczba": liczba,
                        "cena": cena,
                        "kategoria_id": kategorie[kat_nazwa]
                    }
                    supabase.table("produkty").insert(data).execute()
                    st.success(f"Dodano: {nazwa}")
                    st.rerun()
                else:
                    st.warning("Podaj nazwę produktu!")
    except Exception as e:
        st.error(f"Problem z kategoriami: {e}")

# --- SEKCJA 2: LISTA I USUWANIE (TU BYŁ BŁĄD) ---
st.subheader("Aktualny stan magazynowy")

try:
    # Pobieramy dane w sposób bezpieczny
    response = supabase.table("produkty").select("id, nazwa, liczba, cena, kategoria_id").execute()
    produkty = response.data if response.data else []

    if not produkty:
        st.info("Magazyn jest pusty.")
    else:
        # Nagłówki tabeli
        cols = st.columns([3, 1, 1, 1])
        cols[0].write("**Produkt**")
        cols[1].write("**Cena**")
        cols[2].write("**Ilość**")
        cols[3].write("**Akcja**")
        st.divider()

        for prod in produkty:
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            
            c1.write(prod['nazwa'])
            c2.write(f"{prod['cena']} zł")
            c3.write(str(prod['liczba']))
            
            # Przycisk usuwania z unikalnym kluczem
            if c4.button("Usuń", key=f"btn_{prod['id']}", type="secondary"):
                supabase.table("produkty").delete().eq("id", prod['id']).execute()
                st.toast(f"Usunięto: {prod['nazwa']}")
                st.rerun()

except Exception as e:
    st.error(f"Wystąpił błąd podczas wyświetlania danych: {e}")
