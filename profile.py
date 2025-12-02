import streamlit as st
import pandas as pd
import altair as alt
import script as sc # Import script untuk koneksi database (opsional utk nanti)
import datetime

# --- DUMMY DATA GENERATOR ---
def get_dummy_data():
    # Data 1: Timeline Bacaan (7 Hari Terakhir)
    timeline_data = pd.DataFrame({
        'Tanggal': [
            (datetime.date.today() - datetime.timedelta(days=i)).strftime("%d %b") 
            for i in range(6, -1, -1)
        ],
        'Komik Dibaca': [2, 5, 1, 3, 4, 6, 2] # Contoh data acak
    })

    # Data 2: Genre Favorit
    genre_data = pd.DataFrame({
        'Genre': ['Action', 'Romance', 'Fantasy', 'Horror', 'Comedy'],
        'Jumlah': [40, 25, 20, 10, 5]
    })
    
    return timeline_data, genre_data

def show_profile():
    # --- HEADER SECTION ---
    # Mengambil username dari session state, default 'Guest' jika error
    username = st.session_state.get('username', 'Guest')
    
    col_header, col_spacer = st.columns([1, 4])
    with col_header:
        st.markdown(f"### Profile &nbsp; <span style='background-color:#ffeaa7; padding: 5px 15px; border-radius: 10px; border: 1px solid black;'>{username}</span>", unsafe_allow_html=True)

    st.divider()

    # --- REKAP BACAAN SECTION ---
    st.subheader("Rekap bacaan komik")
    
    # Load Dummy Data
    df_timeline, df_genre = get_dummy_data()

    # Layout: Kolom Kiri (Timeline Bar) & Kolom Kanan (Genre Pie)
    col_chart1, col_chart2 = st.columns([2, 1], gap="medium")

    with col_chart1:
        st.markdown("##### 📅 Timeline Aktivitas")
        # Membuat Bar Chart dengan Altair
        bar_chart = alt.Chart(df_timeline).mark_bar(color='#fdcb6e', cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X('Tanggal', sort=None),
            y='Komik Dibaca',
            tooltip=['Tanggal', 'Komik Dibaca']
        ).properties(
            height=250
        )
        st.altair_chart(bar_chart, use_container_width=True)

    with col_chart2:
        st.markdown("##### 🎭 Genre Favorit")
        # Membuat Pie Chart dengan Altair
        pie_chart = alt.Chart(df_genre).mark_arc(innerRadius=40).encode(
            theta=alt.Theta(field="Jumlah", type="quantitative"),
            color=alt.Color(field="Genre", type="nominal", legend=None), # Hilangkan legend agar bersih
            tooltip=['Genre', 'Jumlah']
        ).properties(
            height=250
        )
        st.altair_chart(pie_chart, use_container_width=True)
        # Menampilkan legend manual kecil di bawah agar rapi
        st.caption("Dominan: " + ", ".join(df_genre['Genre'].head(3).tolist()))

    st.markdown("<br>", unsafe_allow_html=True)

    # --- EDIT PROFILE FORM ---
    with st.container(border=True):
        st.subheader("Edit Profile")
        
        new_username = st.text_input("Edit Username", value=username, placeholder="Masukkan username baru")
        new_password = st.text_input("Edit Password", type="password", placeholder="Masukkan password baru")
        
        col_btn1, col_btn2 = st.columns([1, 5])
        with col_btn1:
            if st.button("Simpan Perubahan", type="primary"):
                if not new_username or not new_password:
                    st.warning("Username dan Password tidak boleh kosong.")
                else:
                    # Di sini nanti kamu panggil fungsi update database dari script.py
                    # sc.update_user(st.session_state.username, new_username, new_password)
                    st.success("Data berhasil diperbarui (Dummy)!")
                    st.session_state.username = new_username # Update session sementara
                    st.rerun()

# Agar file ini bisa dijalankan langsung atau diimport
if __name__ == "__main__":
    # Setup dummy session state jika dijalankan mandiri
    if 'username' not in st.session_state:
        st.session_state.username = "Kiya"
    st.set_page_config(layout="wide")
    show_profile()