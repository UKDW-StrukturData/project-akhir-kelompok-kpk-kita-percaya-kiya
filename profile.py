import streamlit as st
import pandas as pd
import altair as alt
import script.script as db 
import bookmark as bk
import requests
from io import BytesIO
import time
from bs4 import BeautifulSoup
import scrape as sc

def display_bookmark_grid():
    st.markdown("## ⭐ Daftar Bookmark Kamu")

    user_id = st.session_state.get("user_id")
    if not user_id:
        st.error("User ID tidak ditemukan.")
        return

    bookmarks = bk.get_bookmark(user_id)
    if not bookmarks:
        st.warning("Belum ada bookmark.")
        return

    cols = st.columns(4)

    for i, (title, url) in enumerate(bookmarks):
        detail = sc.get_comic_detail(url)

        with cols[i % 4]:
            with st.container(border=True):

                # Poster
                if detail["image"]:
                    st.image(detail["image"], use_container_width=True)
                else:
                    st.markdown(
                        "<div style='height:200px;background:#eee;text-align:center;line-height:200px;'>No Image</div>",
                        unsafe_allow_html=True
                    )

                st.markdown(f"**{title}**")
                # st.markdown(f"⭐ Rating: `{detail['rating']}`")
                st.divider()

                if st.button("Baca Sekarang", key=f"read_{i}", use_container_width=True):
                    st.session_state.selected_manga = {
                        "title": title,
                        "link": url,
                        "image": detail["image"],
                        "slug": title.lower().replace(" ", "-"),
                        "rating": detail["rating"]
                    }
                    st.session_state.chapterlist = []
                    st.rerun()

                if st.button("❌ Hapus Bookmark", key=f"del_{i}", use_container_width=True):
                    if bk.delete_bookmark(user_id, url):
                        st.success(f"{title} dihapus")
                        st.rerun()


def display_bookmark_grid():
    st.markdown("## ⭐ Daftar Bookmark Kamu")
    
    user_id = st.session_state.get("user_id")
    
    if not user_id:
        st.error("Error: Tidak dapat memuat bookmark karena User ID tidak ditemukan.")
        return
        
    # Ambil data bookmark dari database/modul
    bookmarks = bk.get_bookmark(user_id) 
    
    if not bookmarks:
        st.warning("Anda belum menyimpan bookmark apa pun.")
        return

    # Header yang diperlukan untuk mengakses gambar dari sumber eksternal
    headers_for_image = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.mangaread.org/" 
    }

    cols = st.columns(4) 
    
    for i, bm in enumerate(bookmarks):
        title = bm[0]
        url = bm[1] 
        
        # --- Caching Keys ---
        img_cache_key = f"bm_img_url_{title.replace(' ', '_')}_{i}"
        image_url = st.session_state.get(img_cache_key, "")
        
        rating_cache_key = f"bm_rating_{title.replace(' ', '_')}_{i}"
        rating = st.session_state.get(rating_cache_key, "N/A")
        
        # Lakukan scraping jika gambar belum ada ATAU rating masih N/A (untuk data lama)
        if not image_url or rating == "N/A":
            with st.spinner(f"Mengambil poster & rating {title}..."):
                try:
                    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
                    
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "html.parser")

                        # 1. Ambil URL Gambar
                        poster_elem = soup.select_one("div.summary_image img") 
                        if poster_elem and poster_elem.get("src"):
                            image_url = poster_elem["src"]
                            st.session_state[img_cache_key] = image_url 
                        
                        # 2. Ambil Rating (Menggunakan selector yang lebih umum)
                        # Ganti selector ini jika tidak cocok dengan situs sumber Anda
                        rating_elem = soup.select_one("div.post-total-rating")
                        # st.write(rating_elem.text)
                        if rating_elem:
                            rating_text = rating_elem.text.strip().replace(" / 5", "")
                            rating = rating_text 
                            st.session_state[rating_cache_key] = rating
                        
                    else:
                        print(f"DEBUG: Gagal akses URL {url}. Status: {resp.status_code}")
                            
                except Exception as e:
                    print(f"Error saat scraping halaman detail untuk {title}: {e}")

        displayed_rating = float(rating)

        with cols[i % 4]:
            with st.container(border=True):
                
                # poster
                if image_url:
                    try:
                        # Fetch gambar menggunakan URL gambar yang sudah di-scrape
                        img_resp = requests.get(image_url, headers=headers_for_image, timeout=30)
                        if img_resp.status_code == 200:
                            st.image(BytesIO(img_resp.content), use_container_width=True)
                        else:
                            st.warning(f"⚠️ Gagal memuat poster (Code {img_resp.status_code})")
                    except Exception as e:
                        print(f"Error fetching image: {e}")
                        st.markdown("<p style='text-align:center;'>[Gagal Muat Gambar]</p>", unsafe_allow_html=True)
                else:
                    # Placeholder "No Image"
                    st.markdown("<div style='height: 200px; background-color: #f0f2f6; text-align: center; line-height: 200px; border-radius: 5px;'>No Image</div>", unsafe_allow_html=True)

                st.markdown(f"**{title}**", unsafe_allow_html=True)

                # st.markdown(f"⭐ **Rating:** `{displayed_rating}`", unsafe_allow_html=True)
                # st.markdown("---") 
                full_stars = int(displayed_rating)
                empty_stars = 5 - full_stars
                stars_str = "⭐" * full_stars + "☆" * empty_stars
                st.markdown(f"<div style='text-align: center; color: orange;'>{stars_str} <small>({displayed_rating})</small></div>", unsafe_allow_html=True)
                if st.button("Baca Sekarang", key=f"read_bm_{i}", use_container_width=True):
                    st.session_state.selected_manga = {
                        "title": title,
                        "link": url, 
                        "image": image_url,
                        "slug": title.lower().replace(" ", "-"),
                        "rating": displayed_rating 
                    } 
                    st.session_state.chapterlist = []
                    st.session_state.chapters_limit = 10
                    st.session_state.is_reading = False 
                    st.session_state.showing_profile = False 
                    st.rerun()

                if st.button("❌ Hapus Bookmark", key=f"delete_bm_{i}", use_container_width=True):
                    user_id = st.session_state.get("user_id")
                    
                    if user_id:
                        if bk.delete_bookmark(user_id, url):
                            if img_cache_key in st.session_state:
                                del st.session_state[img_cache_key]
                            if rating_cache_key in st.session_state:
                                del st.session_state[rating_cache_key]
                                
                            st.success(f"Bookmark '{title}' berhasil dihapus.")
                        else:
                            st.info(f"Bookmark '{title}' tidak ditemukan atau gagal dihapus.")
                            
                        
                        st.session_state.show_bookmarks = False 
                        st.rerun()
                    else:
                        st.error("Gagal menghapus: User ID tidak ditemukan.")

def show_profile():
    if 'show_bookmarks' not in st.session_state:
        st.session_state.show_bookmarks = False

    username = st.session_state.get('username', 'Guest')
    user_id = st.session_state.get("user_id")

    st.markdown(f"### 👤 Profile — **{username}**")
    st.divider()
    st.subheader("Rekap bacaan komik")
    col_chart1, col_chart2 = st.columns([2, 1], gap="medium")

    #bar chart
    timeline_raw = db.bar_chart_data(user_id)
    # st.write(timeline_raw)

    with col_chart1:
        st.markdown("##### 📅 Timeline Aktivitas")

        if timeline_raw:
            df_timeline = pd.DataFrame(timeline_raw)
            # df_timeline["tanggal"] = pd.to_datetime(df_timeline["tanggal"])

            bar_chart = alt.Chart(df_timeline).mark_bar(
                cornerRadiusTopLeft=5,
                cornerRadiusTopRight=5
            ).encode(
                x=alt.X("tanggal", title="Tanggal"),
                y=alt.Y("total:Q", title="Komik Dibaca"),
            )


            st.altair_chart(bar_chart, use_container_width=True)
        else:
            # fallback ke dummy
            st.info("belum ada riwayat bacaan")

    genre_raw = db.genre_chart_data(user_id)

    with col_chart2:
        st.markdown("##### 🎭 Genre Favorit")

        if genre_raw:
            df_genre = pd.DataFrame(genre_raw)

            pie_chart = alt.Chart(df_genre).mark_arc(innerRadius=40).encode(
                theta=alt.Theta("total:Q"),
                color=alt.Color("genre:N"),
                tooltip=["genre", "total"]
            ).properties(height=250)

            st.altair_chart(pie_chart, use_container_width=True)
        else:
            st.info("belum ada genre favorit")

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn_layout = st.columns([1, 3])
    with col_btn_layout[0]:
        btn_label = "Sembunyikan Bookmark" if st.session_state.show_bookmarks else "⭐ Bookmark Kamu"
        if st.button(btn_label, type='primary', use_container_width=True):
            st.session_state.show_bookmarks = not st.session_state.show_bookmarks
            st.rerun()

    if st.session_state.show_bookmarks:
        display_bookmark_grid()
        st.divider()
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
                    db.update_profile(new_username,user_id, new_password)
                    st.success("Data berhasil diperbarui!")
                    time.sleep(3)
                    st.success("Data berhasil diperbarui!")
                    st.session_state.username = new_username 
                    st.rerun()

# so we can directly import
if __name__ == "__main__":
    # Setup dummy session state jika dijalankan mandiri
    if 'username' not in st.session_state:
        st.session_state.username = "Kiya"
    st.set_page_config(layout="wide")
    show_profile()