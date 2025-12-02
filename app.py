import streamlit as st
import os
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
# Hapus get_image_proxy dari import karena tidak dipakai
from scrape import getComicList, scrape_img, searchComic
from gemini import geminiSearch
from ADT import chapterStack
from ADT import chapterLinkedList as LL
from script import login as lg
from script import registration as rg
import profile as pr

st.set_page_config(page_title='Duta Comic', 
                   layout="wide", 
                   page_icon="assets/logo_duta_comic[1].png")

def jumpChapter(key_suffix="Top"):
    if st.session_state.current_chapter_title in st.session_state.chapterlist:
        idx = st.session_state.chapterlist.index(st.session_state.current_chapter_title)
    else:
        idx = 0

    selected = st.selectbox(
        st.session_state.current_chapter_title, 
        st.session_state.chapterlist,            
        index=idx, 
        label_visibility="collapsed",
        key=f"jump_{key_suffix}"
    )
    
    if selected != st.session_state.current_chapter_title:
        st.session_state.current_chapter_title = selected
        st.session_state.chapter_images = scrape_img(st.session_state.chapterlink[selected])
        st.session_state['read_history'].push(st.session_state.current_chapter_title) 
        st.rerun()

def display_reader_mode():
    with st.sidebar:
        st.header(f"📖 Membaca: {st.session_state['current_chapter_title']}")
        
        if st.button("⬅️ Kembali ke Daftar Chapter"):
            st.session_state.is_reading = False
            st.session_state.chapter_images = [] 
            st.rerun() 
            
        st.markdown("---")
    
    if st.session_state.selected_manga:
        st.markdown(f"<h1 style='text-align: center;'>{st.session_state.selected_manga['title']}</h1>", unsafe_allow_html=True)
    
    jumpChapter(key_suffix="Top")
    
    if not st.session_state.chapter_images:
        st.error("Gagal menampilkan konten. Daftar gambar kosong.")
    else:
        st.info(f"Memuat {len(st.session_state.chapter_images)} halaman.")
        for i, url in enumerate(st.session_state.chapter_images):
            # Kembali menggunakan URL langsung (tanpa proxy)
            st.image(url, caption=f"Halaman {i+1}", use_container_width=True)
            
    jumpChapter(key_suffix="Bottom")   
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Kembali ke Daftar Chapter (Bawah)"):
        st.session_state.is_reading = False
        st.session_state.chapter_images = [] 
        st.rerun()

def getChapters(manga):
    st.subheader(manga["title"])
    
    with st.sidebar:
        # Kembali menggunakan URL langsung
        st.image(manga["image"], width=150)
        st.markdown(f"**{manga['title']}**")
        st.markdown("---")
        
        st.subheader("📖 Chapter Manager")
        if 'read_history' in st.session_state and st.session_state['read_history']:
            last_read = st.session_state['read_history'].peek() 
            st.caption(f"Terakhir Dibaca: **{last_read if last_read else 'Belum Ada'}**")
            st.info(f"Riwayat Bacaan (Stack Size): {st.session_state['read_history'].sizeStack()}")

            if st.session_state['read_history'].sizeStack() > 0:
                 if st.button("⬅️ Kembali ke Sebelumnya (POP)", key="btn_pop", use_container_width=True):
                     st.session_state['read_history'].pop()
                     st.rerun()
                 
        st.markdown("---")
        if st.button("⬅️ Kembali ke Daftar Komik", use_container_width=True, type="primary"):
            st.session_state.selected_manga = None
            st.session_state.chapters_limit = 10 
            st.session_state['read_history'] = chapterStack.stack()
            st.rerun()
        
    try:
        if not st.session_state.chapterlist:
            resp = requests.get(manga["link"], headers={"User-Agent": "Mozilla/5.0"}, timeout=30) 
            if resp.status_code != 200:
                st.error("Gagal mengambil halaman detail komik.")
                return

            soup = BeautifulSoup(resp.text, "html.parser")
            desc_elem = soup.select_one("div.summary__content")
            description = desc_elem.get_text(strip=True) if desc_elem else "Deskripsi tidak ditemukan."
            chapters = []
            for ch in soup.select("ul.main.version-chap li.wp-manga-chapter"):
                ch_title = ch.select_one("a").get_text(strip=True)
                ch_link = ch.select_one("a")["href"]
                ch_date = ch.select_one("span.chapter-release-date i")
                ch_date = ch_date.get_text(strip=True) if ch_date else ""
                chapters.append({"title": ch_title, "link": ch_link, "date": ch_date}) 
                st.session_state.chapterlist.append(ch_title)
                st.session_state.chapterlink.update({ch_title:ch_link})
            
            st.session_state.temp_description = description
            st.session_state.temp_chapters = chapters
        else:
            description = st.session_state.get('temp_description', "")
            chapters = st.session_state.get('temp_chapters', [])

        col1, col2 = st.columns([1, 2])
        with col1:
            # Kembali menggunakan URL langsung
            st.image(manga["image"], width=300)
        with col2:
            st.markdown("### 🧾 Deskripsi")
            st.write(description)
            st.markdown(f"🔗 [Buka di Browser]({manga['link']})")

        st.markdown("---")
        st.markdown("<h2 style='text-align: center; color: red; padding-bottom: 2em;'>📜 Daftar Chapter</h2>", unsafe_allow_html= True)
        if not chapters:
            st.warning("Belum ada chapter yang ditemukan.")
        else:
            visible_chapters = chapters[:st.session_state.chapters_limit]
            
            for i, ch in enumerate(visible_chapters):
                col_title, col_read= st.columns([3, 1.5])
                
                with col_title:
                    st.markdown(
                        f"**{ch['title']}** <span style='color:gray; font-size:0.8em;'> ({ch['date']})</span>", 
                        unsafe_allow_html=True
                    )
                    
                with col_read:
                    if st.button("▶️ Baca", key=f"btn_read_{ch['link']}", use_container_width=True):
                        with st.spinner(f"Mengambil gambar untuk {ch['title']}..."):
                            image_urls = scrape_img(ch['link'])
                        
                        if image_urls:
                            st.session_state['read_history'].push(ch['title'])
                            st.success("Ditambahkan ke riwayat (PUSH)!")
                            st.session_state.chapter_images = image_urls
                            st.session_state.current_chapter_title = ch['title']
                            st.session_state.is_reading = True
                            st.rerun() 
                        else:
                            st.error("Gagal memuat gambar chapter.")

            if st.session_state.chapters_limit < len(chapters):
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("⬇️ Tampilkan Lebih Banyak Chapter", use_container_width=True):
                    # Set limit menjadi semua chapter yang tersedia
                    st.session_state.chapters_limit = len(chapters) 
                    st.rerun()
            else:
                st.info("✅ Semua chapter sudah ditampilkan.")

    except Exception as e:
        st.error(f"Terjadi kesalahan saat scraping detail: {e}")

def display_manga_grid():
    mangas = []
    
    with st.sidebar:
        if st.button("Logout", type="primary", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.page = 'login'
            st.session_state.selected_manga = None
            st.session_state.is_reading = False
            st.session_state.current_chapter_title = ""
            st.session_state.search_active = False
            st.session_state.chapterlist = []
            st.session_state.chapterlink = {}
            st.session_state.chapter_images = []
            st.session_state.read_history = chapterStack.stack()
            st.session_state.has_fetched_once = False
            st.session_state.showing_profile = False
            st.rerun()
        
        if st.button("Profile", use_container_width=True):
            st.session_state.showing_profile = True
            st.rerun()
    
    search = st.sidebar.text_input("Pencarian dan Gemini", placeholder="e.g: Beri Aku rekomendasi...")
    
    if search:
        if "rekomendasi" in search.lower() or "deskripsi" in search.lower():
            geminiSearch(search)
        else:
            with st.spinner(f"Mencari komik dengan kata kunci: '{search}'..."):
                mangas = searchComic(search)
    else:
        st.sidebar.header("Filter Komik")
        filter_type = st.sidebar.selectbox(
            "Pilih jenis komik:",
            ["Semua", "manga", "manhwa", "manhua"],
            key="selected_filter"
        )
        
        order_type = "latest" 
        if filter_type != 'Semua':
            order_type = st.sidebar.selectbox(
                "Order By:",
                ["latest", "alphabet", "rating", "trending", "views", "new-manga"],
                key="selected_order"
            )
        
        if 'has_fetched_once' not in st.session_state:
            st.session_state.has_fetched_once = False

        current_filter_val = None if filter_type == "Semua" else filter_type
        current_order_val = None if order_type == "latest" else order_type
        
        filters_changed = (
            st.session_state.get('current_filter') != current_filter_val or 
            st.session_state.get('order_by') != current_order_val
        )

        manual_fetch = st.sidebar.button("📥 Ambil Daftar Komik", type="primary")
        
        if not st.session_state.has_fetched_once or manual_fetch or filters_changed:
            st.session_state.current_page = 1 
            st.session_state.current_filter = current_filter_val
            
            if st.session_state.current_filter is not None:
                st.session_state.order_by = current_order_val
            else:
                st.session_state.order_by = None 

            st.session_state.search_active = True
            st.session_state.has_fetched_once = True
            st.rerun()

        if st.session_state.search_active and not search: 
            with st.spinner(f"Mengambil data halaman {st.session_state.current_page}..."):
                mangas = getComicList(st.session_state.current_filter, st.session_state.current_page, st.session_state.order_by)
    
    if mangas:
        st.success(f"Berhasil mengambil {len(mangas)} komik (Halaman {st.session_state.current_page})")
        cols = st.columns(4)
        for i, manga in enumerate(mangas):
            with cols[i % 4]:
                with st.container(border=True):
                    # Kembali menggunakan URL langsung
                    st.image(manga.get("image"), use_container_width=True)
                    st.markdown(
                        f"<p style='text-align: center; font-weight: bold; height: 3em; overflow: hidden;'>"
                        f"{manga['title']}"
                        f"</p>", 
                        unsafe_allow_html=True
                    )
                    
                    try:
                        rating_val = float(manga.get("rating", 0))
                    except (ValueError, TypeError):
                        rating_val = 0
                    
                    full_stars = int(rating_val)
                    empty_stars = 5 - full_stars
                    stars_str = "⭐" * full_stars + "☆" * empty_stars
                    st.markdown(f"<div style='text-align: center; color: orange;'>{stars_str} <small>({rating_val})</small></div>", unsafe_allow_html=True)

                    button_text = f"Pilih {st.session_state.current_filter.capitalize()}" if st.session_state.current_filter else "Pilih Komik Ini"
                    if st.button(button_text, key=manga['slug'], use_container_width=True):
                        st.session_state.selected_manga = manga
                        st.session_state.chapterlist = [] 
                        st.rerun() 
    else:
        if not ("rekomendasi" in search.lower() or "deskripsi" in search.lower()):
            if st.session_state.search_active:
                st.warning("Tidak ada komik ditemukan.")
        
    st.divider()
    
    if not search:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("⬅️ Halaman Sebelumnya", use_container_width=True, disabled=(st.session_state.current_page == 1)):
                st.session_state.current_page -= 1
                st.rerun()
        
        with col2:
            st.markdown(f"<h3 style='text-align: center;'>Halaman {st.session_state.current_page}</h3>", unsafe_allow_html=True)
        
        with col3:
            if st.button("Halaman Berikutnya ➡️", use_container_width=True, disabled=(not mangas)):
                st.session_state.current_page += 1
                st.rerun()

def main():
    if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
    if 'username' not in st.session_state: st.session_state['username'] = None
    if 'page' not in st.session_state: st.session_state['page'] = 'login'

    if not st.session_state['logged_in']:
        st.sidebar.empty()
        if st.session_state['page'] == 'register':
            rg.register()
        else:
            lg.display_login_page()
        return

    st.markdown("<h1 style='text-align: center; color: red;'>📚 Duta Comic Reader & Downloader</h1>", unsafe_allow_html=True)
    st.info("This is Only a testing APP. So, you don't need to login before head Happy reading lad")
    st.markdown(f"<h2>Hi, {st.session_state['username']}</h2>", unsafe_allow_html=True)
    
    if 'selected_manga' not in st.session_state: st.session_state.selected_manga = None
    if 'current_page' not in st.session_state: st.session_state.current_page = 1
    if 'current_filter' not in st.session_state: st.session_state.current_filter = None
    if 'order_by' not in st.session_state: st.session_state.order_by = None
    if 'chapterlist' not in st.session_state: st.session_state.chapterlist = []
    if 'chapterlink' not in st.session_state: st.session_state.chapterlink = {}
    if 'search_active' not in st.session_state: st.session_state.search_active = False 
    if 'keyword_search' not in st.session_state: st.session_state.keywoard_search = None
    if 'is_reading' not in st.session_state: st.session_state.is_reading = False
    if 'chapter_images' not in st.session_state: st.session_state.chapter_images = []
    if 'current_chapter_title' not in st.session_state: st.session_state.current_chapter_title = ""
    if 'chapters_limit' not in st.session_state: st.session_state.chapters_limit = 10
    if 'read_history' not in st.session_state: st.session_state['read_history'] = chapterStack.stack()
    if 'has_fetched_once' not in st.session_state: st.session_state.has_fetched_once = False
    if 'showing_profile' not in st.session_state: st.session_state.showing_profile = False
        
    if st.session_state.is_reading:
        display_reader_mode() 
    elif st.session_state.showing_profile:
        # LOGIKA TAMPILAN PROFILE
        if st.sidebar.button("Back to Home"):
            st.session_state.showing_profile = False
            st.rerun()
        pr.show_profile()
    elif st.session_state.selected_manga:
        getChapters(st.session_state.selected_manga)
    else:
        display_manga_grid()

if __name__ == "__main__":
    main()