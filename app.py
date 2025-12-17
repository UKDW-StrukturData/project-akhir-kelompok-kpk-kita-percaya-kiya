import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup
from scrape import getComicList, scrape_img, searchComic, get_comic_detail
from gemini import geminiSearch
from ADT import chapterStack
import script.login as lg
import script.registration as rg
import script.script as db
import profile as pr
from io import BytesIO 
import script.bookmark as bk
import profile as pr
from PIL import Image
import zipfile
import re

# print(True)
st.set_page_config(page_title='Duta Comic', 
                   layout="wide", 
                   page_icon="assets/logo_duta_comic[1].png")

HEADERS_DEFAULT = {
"User-Agent": "Mozilla/5.0",
"Referer": "https://www.mangaread.org/"
}

def fetch_image_bytes(url, headers=None, timeout=30):
    headers = headers or HEADERS_DEFAULT
    resp = requests.get(url, headers=headers, timeout=timeout)
    resp.raise_for_status()
    return resp.content

def images_urls_to_pdf_bytes(image_urls, dpi=150, headers=None):
    headers = headers or HEADERS_DEFAULT
    pil_images = []
    for i, url in enumerate(image_urls):
        try:
            img_bytes = fetch_image_bytes(url, headers=headers)
            img = Image.open(BytesIO(img_bytes))
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.thumbnail((1200, 1800))
            pil_images.append(img)
        except Exception as e:
            print(f"Warning: gagal ambil/parse image {i+1} ({url}): {e}")
    if not pil_images:
        raise ValueError("No valid images to convert to PDF")
    out = BytesIO()
    first, rest = pil_images[0], pil_images[1:]
    first.save(out, format="PDF", save_all=True, append_images=rest, resolution=dpi)
    out.seek(0)
    return out.read()

def download_chapter_as_pdf_stream(chapter_title, image_urls, dpi=150, headers=None):
    safe_name = re.sub(r"[^0-9A-Za-z._-]", "_", chapter_title) or "chapter"
    pdf_bytes = images_urls_to_pdf_bytes(image_urls, dpi=dpi, headers=headers)
    return f"{safe_name}.pdf", pdf_bytes

def make_zip_of_all_chapters(manga_title, chapterlink_dict, dpi=150, headers=None):
    buf = BytesIO()
    headers = headers or HEADERS_DEFAULT
    total_chapters = len(chapterlink_dict)
    progress_container = st.empty() 
    zip_bar = progress_container.progress(0, text=f"Chapter 0/{total_chapters}...")
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for i, (title, link) in enumerate(chapterlink_dict.items()):
            try:
                zip_bar.progress((i + 1) / total_chapters, text=f"Chapter {i+1}/{total_chapters} ({title})...")
                image_urls = scrape_img(link)
                fname, pdf_bytes = download_chapter_as_pdf_stream(
                    title, 
                    image_urls,
                    dpi=dpi,
                    headers=headers
                )
                zf.writestr(fname, pdf_bytes)
            except Exception as e:
                st.warning(f"Warning: Gagal generate PDF untuk '{title}'. Mungkin gambar tidak bisa diakses: {e}")
    zip_bar.empty()
    buf.seek(0)
    return buf.read()


def prev_chapter():
    if st.button("⬅️ Prev", use_container_width=True, key="btn_prev_chap"):
        if st.session_state.current_chapter_title in st.session_state.chapterlist:
            idx = st.session_state.chapterlist.index(st.session_state.current_chapter_title)
        else:
            idx = 0
        if idx + 1 < len(st.session_state.chapterlist):
            next_title = st.session_state.chapterlist[idx + 1]
            if next_title != st.session_state.current_chapter_title:
                st.session_state.current_chapter_title = next_title
                st.session_state.chapter_images = scrape_img(st.session_state.chapterlink[next_title])
                st.session_state['read_history'].push(st.session_state.current_chapter_title) 
                st.rerun()
        else:
            st.warning("Kamu sudah di chapter paling awal!")

def next_chapter():
    if st.button("Next ➡️", use_container_width=True, key="btn_next_chap"):
        if st.session_state.current_chapter_title in st.session_state.chapterlist:
            idx = st.session_state.chapterlist.index(st.session_state.current_chapter_title)
        else:
            idx = 0
        if idx - 1 >= 0:
            next_title = st.session_state.chapterlist[idx - 1]
            if next_title != st.session_state.current_chapter_title:
                st.session_state.current_chapter_title = next_title
                st.session_state.chapter_images = scrape_img(st.session_state.chapterlink[next_title])
                st.session_state['read_history'].push(st.session_state.current_chapter_title) 
                st.rerun()
        else:
            st.warning("Anda sudah berada di chapter terakhir!")


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
    chapter_to_load = st.session_state.current_chapter_title
    link_to_load = st.session_state.chapterlink[chapter_to_load]
    if not st.session_state.chapter_images: 
        if link_to_load:
            with st.spinner(f"Memuat chapter baru: **{chapter_to_load}**..."):
                try:
                    image_urls = scrape_img(link_to_load) 
                    
                    if image_urls:
                        st.session_state.chapter_images = image_urls
                    else:
                        st.error("Gagal mendapatkan daftar gambar untuk chapter ini.")
                        st.session_state.chapter_images = []
                except Exception as e:
                    st.error(f"Gagal saat scraping gambar untuk {chapter_to_load}: {e}")
                    st.session_state.chapter_images = []
        else:
            st.error("Link chapter tidak ditemukan di session state. Silakan kembali ke daftar chapter.")

    with st.sidebar:
        st.header(f"📖 Membaca: {st.session_state['current_chapter_title']}")
        
        if st.button("⬅️ Kembali ke Daftar Chapter"):
            st.session_state.is_reading = False
            st.session_state.chapter_images = [] 
            st.rerun() 
            
        st.markdown("---")
    
    if st.session_state.selected_manga:
        st.markdown(f"<h1 style='text-align: center;'>{st.session_state.selected_manga['title']}</h1>", unsafe_allow_html=True)
    
    try:
        pdf_bytes = images_urls_to_pdf_bytes(st.session_state.chapter_images)
        st.download_button(
            label="Download Chapter ini (PDF)",
            data=pdf_bytes,
            file_name=f"{st.session_state.current_chapter_title}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    except Exception as e:
        st.error("Gagal membuat PDF")

    jumpChapter(key_suffix="Top")
    
    if not st.session_state.chapter_images:
        st.error("Gagal menampilkan konten. Daftar gambar kosong.")
    else:
        st.info(f"Memuat {len(st.session_state.chapter_images)} halaman.")
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.mangaread.org/"
        }

        for i, url in enumerate(st.session_state.chapter_images):
            try:
                img_resp = requests.get(url, headers=headers, timeout=30)

                if img_resp.status_code != 200:
                    st.warning(f"⚠️ Cloudflare blocked image {i+1}")
                    continue

                st.image(BytesIO(img_resp.content), caption=f"Halaman {i+1}", use_container_width=True)

            except Exception as e:
                st.error(f"Gagal memuat gambar {i+1}: {e}")
            
    col1,col2 = st.columns(2)
    with col1:
        prev_chapter()
            
    with col2:
        next_chapter()
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⬅️ Kembali ke Daftar Chapter (Bawah)"):
        st.session_state.is_reading = False
        st.session_state.chapter_images = [] 
        st.rerun()
        
def display_bookmarks():
    st.header("⭐ Bookmark Kamu")

    # if lpgin fetch db
    if st.session_state.get("logged_in", False):
        user_id = st.session_state.get("user_id") 
        bookmarks = bk.get_bookmark(user_id)
        if not bookmarks:
            st.write("Belum ada bookmark.")
            return

        for bm in bookmarks:
            # bm adalah tuple (manga_title, manga_url) dari script.py
            title = bm[0] # Ambil Judul
            url = bm[1]   # Ambil URL
            st.write(f"📘 [{title}]({url})")

    else:
        # guest bookmark
        if not st.session_state.guest_bookmark:
            st.write("Belum ada bookmark.")
            return
        
        # title and url
        for title, url in st.session_state.guest_bookmark: 
            st.write(f"📘 [{title}]({url})") # Menampilkan judul sebagai link
def add_bookmark(title, manga_url):
    if st.session_state.get("logged_in", False):
        user_id = st.session_state.get("user_id") 
        
        if not user_id:
            st.error("Error: ID Pengguna tidak ditemukan. Silakan login ulang.")
            return
        ok = bk.insert_bookmark(user_id, title, manga_url) 
        if ok:
            st.success("Bookmark berhasil disimpan ⭐")
        else:
            st.info("ℹ️ Komik ini sudah ada di daftar Bookmark Anda.") 
    else:
        existing_urls = [bm[1] for bm in st.session_state.guest_bookmark] 
        
        if manga_url not in existing_urls:
            st.session_state.guest_bookmark.append((title, manga_url)) 
            st.success("Bookmark disimpan sementara ⭐")
        else:
            st.info("ℹ️ Komik ini sudah ada di daftar Bookmark sementara Anda.")

# @st.cache_data           
def getChapters(manga):
    history = db.select_history(st.session_state['user_id'],manga['title'])
    st.session_state['read_history'] = chapterStack.stack()
    for i in history:
        st.session_state['read_history'].push(i)
    # st.write(manga)
    st.subheader(manga["title"])
    if not manga.get("image"):
        try:
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                poster_elem = soup.select_one("div.summary_image img") 
                if poster_elem and poster_elem.get("src"):
                    manga["image"] = poster_elem["src"] 
                else:
                    print("DEBUG: Poster element tidak ditemukan di halaman detail.")
            else:
                print(f"DEBUG: Gagal scrape halaman detail untuk gambar, Status: {resp.status_code}")
                
        except Exception as e:
            print(f"Error saat scraping gambar poster: {e}")
    headers = {
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.mangaread.org/"
    }
    with st.sidebar:
        # Kembali menggunakan URL langsung
        try:
            img_resp = requests.get(manga["image"], headers=headers, timeout=30)

            if img_resp.status_code != 200:
                st.warning(f"⚠️ Cloudflare blocked image")
                
            st.image(BytesIO(img_resp.content), width= 100 )

        except Exception as e:
                st.error(f"Gagal memuat poster komik karena {e}")
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
        st.sidebar.subheader("🔖 Bookmark Kamu")

        if not st.session_state.get("logged_in", False):
            # Tidak login → bookmark guest
            bookmarks = st.session_state.get("guest_bookmark", [])
        else:
            user_id = st.session_state.get("user_id") # Ambil ID
            if user_id is not None:
                #bookmark used_id based
                bookmarks = bk.get_bookmark(user_id) 
            else:
                bookmarks = [] # Jika user_id hilang, jangan crash

        # Tampilkan bookmark
        if not bookmarks:
            st.write("Belum ada bookmark.")
        else:
            for bm in bookmarks:
                # Kalau login → data dari DB biasanya tuple (id, title, url)
                if st.session_state.get("logged_in", False):
                    title = bm[0]
                    url = bm[1]
                else:
                    # Kalau guest → sekarang kita simpan (title, url)
                    if isinstance(bm, tuple) and len(bm) == 2:
                        title = bm[0] 
                        url = bm[1]
                    else:
                        # Fallback jika masih ada data lama yang hanya URL
                        title = bm
                        url = bm
                
                if st.sidebar.button(f"📘 {title}", key=f"bookmark_{title}"):
                    st.session_state.selected_manga = {
                        "title": title,
                        "link": url, 
                        "image": "",
                        "slug": title.lower().replace(" ", "-"),
                        "rating": "0"
                    } 
                    st.session_state.chapterlist = []
                    st.session_state.chapters_limit = 10
                    st.session_state.is_reading = False 
                    st.rerun()

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
            author = soup.select_one("div.author-content")
            genre = soup.select_one("div.genres-content") 
            if author and author.text:
                st.session_state.selected_manga['author'] = author.text
            else:
                st.session_state.selected_manga['author'] = 'unknown'
            if genre and genre.text:
                st.session_state.selected_manga['genre'] = genre.text
            else:
                st.session_state.selected_manga['author'] = 'unknown'   
            # st.session_state.selected_manga
            description = desc_elem.get_text(strip=True) if desc_elem else "Deskripsi tidak ditemukan."
            chapters = []
            for ch in soup.select("ul.main.version-chap li.wp-manga-chapter"):
                ch_title = ch.select_one("a").get_text(strip=True)
                ch_link = ch.select_one("a")["href"]
                ch_date = ch.select_one("span.chapter-release-date i")
                # author = ch.select_one("author-content a") 
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
            # durectly use urrlllll🥹🥹🥹🥹🥹🥹🥹🥹
            try:
                img_resp = requests.Session().get(manga["image"], headers=headers, timeout=30)

                if img_resp.status_code != 200:
                    st.warning(f"⚠️ Cloudflare blocked image")
                
                st.image(BytesIO(img_resp.content), width= 300)

            except Exception as e:
                    st.error(f"Gagal memuat poster komik karena {e}")
        with col2:
            st.markdown("### 🧾 Deskripsi")
            st.write(description)
            st.write("Author : ", st.session_state.selected_manga['author'])
            st.write("Genre : ",st.session_state.selected_manga['genre'])
            
            st.markdown(f"🔗 [Buka di Browser]({manga['link']})")
            
            if st.button("⭐ Tambah ke Bookmark", key="add_manga_bookmark_btn", use_container_width=True):
                add_bookmark(manga["title"], manga["link"])
                st.rerun() 
            
            with st.container():
                if st.button("⬇️ Buat ZIP Semua Chapter", type="primary", use_container_width=True):
                    with st.spinner(f"Membuat ZIP untuk **{manga['title']}** (Butuh waktu lama, sabar ya)..."):
                        try:
                            zip_bytes = make_zip_of_all_chapters(
                                manga['title'], 
                                st.session_state.chapterlink
                            )
                            st.session_state.zip_data = zip_bytes
                            st.success("ZIP berhasil dibuat!")
                            st.rerun() 
                        except Exception as e:
                            st.error(f"Gagal membuat ZIP: {e}")
                            st.session_state.zip_data = None
                if st.session_state.zip_data:
                    st.download_button(
                        label=f"Download {manga['title']}.zip 📦",
                        data=st.session_state.zip_data,
                        file_name=f"{manga['title']}-all-chapters.zip",
                        mime="application/zip",
                        use_container_width=True
                    )
                    if st.button("Hapus ZIP yang Dibuat", use_container_width=True):
                        st.session_state.zip_data = None
                        st.rerun()

        st.markdown("---")
        st.markdown("<h2 style='text-align: center; color: red; padding-bottom: 2em;'>📜 Daftar Chapter</h2>", unsafe_allow_html= True)
        if not chapters:
            st.warning("Belum ada chapter yang ditemukan.")
        else:
            visible_chapters = chapters[:st.session_state.chapters_limit]
            history = db.select_history(st.session_state['user_id'],manga['title'])
            # st.write(history)
            read_chapter = []
            for i in history:
                # st.write(i)
                read_chapter.append(i[1])
            # st.write(read_chapter)
            for i, ch in enumerate(visible_chapters):
                col_title, col_read= st.columns([3, 1.5])
                
                with col_title:
                    if ch['title'] in read_chapter:
                        st.markdown(
                            f"**{ch['title']}** <span style='color:green; font-size:0.9em;'>({ch['date']}) Chapter ini sudah dibaca</span>", 
                            unsafe_allow_html=True
                        )
                    else:                        
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
                            db.history_insert(
                                user_id=st.session_state.user_id,
                                manga_title=manga["title"],
                                chapter_title=ch["title"],
                                genres=st.session_state.selected_manga['genre'].strip().split(",")
                            )
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

# @st.cache_data
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
            st.cache_data.clear
            st.rerun()
        
        if st.button("Profile", use_container_width=True):
            st.session_state.showing_profile = True
            st.rerun()
    
    search = st.sidebar.text_input("Pencarian dan Gemini", placeholder="e.g: Beri Aku deskripsi ....")
    
    if search:
        if "diskusi" in search.lower() or "deskripsi" in search.lower():
            geminiSearch(search)
        else:
            with st.spinner(f"Mencari komik dengan kata kunci: '{search}'..."):
                mangas = searchComic(search)
    else:
        st.sidebar.header("Filter Komik")
        filter_type = st.sidebar.multiselect(label="Pilih jenis komik:",
                                            options= ["Semua", "manga", "manhwa", "manhua", "fantasy",
                                            "isekai", "action", "adventure", "romance", "drama", 
                                            "comedy", "school-life","shoujo", "cooking",
                                            "harem", "historical", "horror", "martial-arts", 
                                            "mecha", "mystery", "slice-of-life", "sports",
                                            "tragedy", "supernatural", "webtoon"],
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
                    # uses direct url   
                    headers = {
                                "User-Agent": (
                                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                                    "Chrome/124.0.0.0 Safari/537.36"
                                ),
                                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp",
                                "Accept-Language": "en-US,en;q=0.9",
                                "Referer": "https://www.mangaread.org/",
                                "Connection": "keep-alive",
                            }
                    try:
                        img_resp = requests.Session().get(manga["image"], headers=headers, timeout=30)

                        if img_resp.status_code != 200:
                            st.warning(f"⚠️ Cloudflare blocked image")
                        st.image(BytesIO(img_resp.content), use_container_width=True )

                    except Exception as e:
                            st.error(f"Gagal memuat poster komik karena {e}")
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

                    button_text = f"Pilih" if st.session_state.current_filter else "Pilih Komik Ini"
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
    if 'keyword_search' not in st.session_state: st.session_state.keyword_search = None
    if 'is_reading' not in st.session_state: st.session_state.is_reading = False
    if 'chapter_images' not in st.session_state: st.session_state.chapter_images = []
    if 'current_chapter_title' not in st.session_state: st.session_state.current_chapter_title = ""
    if 'chapters_limit' not in st.session_state: st.session_state.chapters_limit = 10
    if 'read_history' not in st.session_state: st.session_state['read_history'] = chapterStack.stack()
    if 'has_fetched_once' not in st.session_state: st.session_state.has_fetched_once = False
    if 'showing_profile' not in st.session_state: st.session_state.showing_profile = False
    if 'guest_bookmark' not in st.session_state: st.session_state.guest_bookmark = []
    if 'zip_data' not in st.session_state: st.session_state.zip_data = None
    
    if st.session_state.is_reading:
        display_reader_mode() 
    elif st.session_state.showing_profile:
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