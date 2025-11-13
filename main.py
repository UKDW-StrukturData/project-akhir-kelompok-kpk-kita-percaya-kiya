import streamlit as st
import os
import re
import img2pdf
from bs4 import BeautifulSoup
from scrape import getComicList
from scrape import scrape_img
from scrape import searchComic
import requests
import pandas as pd
from gemini import geminiSearch
import chapterStack
import chapterLinkedList as LL

def display_reader_mode():
    with st.sidebar:
        st.header(f"📖 Membaca: {st.session_state['current_chapter_title']}")
        
        if st.button("⬅️ Kembali ke Daftar Chapter"):
            st.session_state.is_reading = False
            st.session_state.chapter_images = [] 
            st.rerun() 
            
        st.markdown("---")
    
    if not st.session_state.chapter_images:
        st.error("Gagal menampilkan konten. Daftar gambar kosong.")
    else:
        st.info(f"Memuat {len(st.session_state.chapter_images)} halaman.")
        
        for i, url in enumerate(st.session_state.chapter_images):
            # img = url # Variabel 'img' tidak digunakan, bisa dihapus
            st.image(url, caption=f"Halaman {i+1}")
    
    # Col1 dan Col2 tidak digunakan di sini, bisa dihapus atau diimplementasikan
    # col1, col2 = st.columns([1, 2])
    # di sini nanti buat next sama prev chapter malas
        
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Kembali ke Daftar Chapter (Bawah)"):
        st.session_state.is_reading = False
        st.session_state.chapter_images = [] 
        st.rerun()
        
def getChapters(manga):
    st.subheader(manga["title"])
    
    with st.sidebar:
        st.image(manga["image"], width=150)
        st.markdown(f"**{manga['title']}**")
        st.markdown("---")
        
        st.subheader("📖 Chapter Manager (Stack LIFO)")
        last_read = st.session_state['read_history'].peek() 
        st.caption(f"Terakhir Dibaca (PEEK): **{last_read if last_read else 'Belum Ada'}**")
        st.info(f"Riwayat Bacaan (Stack Size): {st.session_state['read_history'].sizeStack()}")

        if st.session_state['read_history'].sizeStack() > 0:
             if st.button("⬅️ Kembali ke Sebelumnya (POP)", key="btn_pop", use_container_width=True):
                 st.session_state['read_history'].pop()
                 st.warning("Chapter dihapus dari riwayat (POP).")
                 st.rerun()
                 
        st.markdown("---")
        if st.button("⬅️ Kembali ke Daftar Komik", use_container_width=True, type="primary"):
            st.session_state.selected_manga = None
            st.session_state.chapters_limit = 10 
            st.session_state['read_history'] = chapterStack.stack()
            st.rerun()
        
    try:
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
        
        col1, col2 = st.columns([1, 2])
        with col1:
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
                        # Panggil scrape_img
                        with st.spinner(f"Mengambil gambar untuk {ch['title']}..."):
                            image_urls = scrape_img(ch)
                        
                        if image_urls:
                            st.session_state['read_history'].push(ch['title'])
                            st.success("Ditambahkan ke riwayat (PUSH)!")
                            st.session_state.chapter_images = image_urls
                            st.session_state.current_chapter_title = ch['title']
                            st.session_state.is_reading = True
                            print(st.session_state.current_chapter_title)
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
        
def download_images(image_urls, manga_slug, ch_link, base_dir, st_status):
    pass
def convertPDF(mangaDirectory, st_status):
    pass

def display_manga_grid():
    mangas = []
    current_page = st.session_state.current_page
    current_filter = st.session_state.current_filter
    order_by = st.session_state.order_by
    
    search = st.sidebar.text_input("Pencarian dan Gemini", placeholder="e.g: Beri Aku rekomendasi, deskripsi komik")
    
    if search:
        if "rekomendasi" in search.lower() or "deskripsi" in search.lower():
            geminiSearch(search)
            # Jika Gemini dipanggil, tidak ada komik yang diambil, jadi mangas tetap []
        else:
            with st.spinner(f"Mencari komik dengan kata kunci: '{search}'..."):
                mangas = searchComic(search)
            # Karena ini adalah halaman pencarian, kita tidak menampilkan navigasi halaman
            # current_page tetap, tapi navigasi dihilangkan
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

        manual_fetch = st.sidebar.button("📥 Ambil Daftar Komik", type="primary")
        
        if not st.session_state.has_fetched_once or manual_fetch:
            st.session_state.current_page = 1 
            st.session_state.current_filter = None if filter_type == "Semua" else filter_type
            
            if st.session_state.current_filter is not None:
                st.session_state.order_by = None if order_type == "latest" else order_type
            else:
                st.session_state.order_by = None 

            st.session_state.search_active = True
            st.session_state.has_fetched_once = True
            st.rerun()

        if st.session_state.search_active and not search: 
            current_page = st.session_state.current_page
            current_filter = st.session_state.current_filter
            order_by = st.session_state.order_by

            with st.spinner(f"Mengambil data halaman {current_page} untuk '{current_filter or 'Semua'}'..."):
                mangas = getComicList(current_filter, current_page, order_by)
    
    if mangas:
        st.success(f"Berhasil mengambil {len(mangas)} komik (Halaman {current_page})")
        cols = st.columns(4)
        for i, manga in enumerate(mangas):
            with cols[i % 4]:
                with st.container(border=True):
                    st.image(manga["image"], width= "stretch")
                    st.markdown(
                        f"<p style='text-align: center; font-weight: bold; height: 3em; overflow: hidden;'>"
                        f"{manga['title']}"
                        f"</p>", 
                        unsafe_allow_html=True
                    )
                    
                    button_text = f"Pilih {current_filter.capitalize()}" if current_filter else "Pilih Komik Ini"
                    if st.button(button_text, key=manga['slug'], use_container_width=True):
                        st.session_state.selected_manga = manga
                        st.rerun() 
    else:
        if not ("rekomendasi" in search.lower() or "deskripsi" in search.lower()):
            st.warning("Tidak ada komik ditemukan.")
        
    st.divider()
    
    if not search:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col1:
            if st.button("⬅️ Halaman Sebelumnya", use_container_width=True, disabled=(current_page == 1)):
                st.session_state.current_page -= 1
                st.rerun()
        
        with col2:
            st.markdown(f"<h3 style='text-align: center;'>Halaman {current_page}</h3>", unsafe_allow_html=True)
        
        with col3:
            if st.button("Halaman Berikutnya ➡️", use_container_width=True, disabled=(not mangas)):
                st.session_state.current_page += 1
                st.rerun()

def main():
    st.set_page_config(page_title="Duta Comic", layout="wide")
    st.markdown("<h1 style='text-align: center; color: red;'>📚 Duta Comic Reader & Downloader</h1>", unsafe_allow_html=True)
    # st.title("📚 Duta Comic Reader & Downloader", )

    if 'selected_manga' not in st.session_state:
        st.session_state.selected_manga = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
    if 'current_filter' not in st.session_state:
        st.session_state.current_filter = None
    if 'order_by' not in st.session_state:
        st.session_state.order_by = None
    if 'search_active' not in st.session_state:
        st.session_state.search_active = False 
    if 'keyword_search' not in st.session_state:
        st.session_state.keywoard_search = None
        
    if 'is_reading' not in st.session_state: 
        st.session_state.is_reading = False
    if 'chapter_images' not in st.session_state: 
        st.session_state.chapter_images = []
    if 'current_chapter_title' not in st.session_state: 
        st.session_state.current_chapter_title = ""
    if 'chapters_limit' not in st.session_state: 
        st.session_state.chapters_limit = 10
    if 'read_history' not in st.session_state: 
        st.session_state['read_history'] = chapterStack.stack()
        
    if st.session_state.is_reading:
        display_reader_mode() 
    elif st.session_state.selected_manga:
        getChapters(st.session_state.selected_manga)
    else:
        display_manga_grid()

if __name__ == "__main__":
    main()