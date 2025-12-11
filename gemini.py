import streamlit as st
from google import genai
from google.genai import types
import script as sc
from scrape import searchComic
import time

try:
    # st.secrets to access secret.toml
    client = genai.Client(api_key=st.secrets["gemini"]["api_key"])
except Exception as e:
    st.error(f"Konfigurasi API Key gagal: {e}")
    client = None

def generate_content(prompt):
    if not client:
        raise Exception("Client Gemini belum terinisialisasi.")

    target_model = "gemini-2.5-flash"
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=target_model, 
                contents=prompt
            )
            return response 
            
        except Exception as e:
            error_msg = str(e)
            
            # Daftar error yang boleh di-retry (Transient Errors)
            retry_triggers = [
                "429", "503", "500",
                "RESOURCE_EXHAUSTED", 
                "Server disconnected",
                "Connection error",
                "internal_error"
            ]
            
            # Cek apakah error termasuk yang bisa dicoba lagi
            if any(code in error_msg for code in retry_triggers):
                if attempt < max_retries - 1:
                    time.sleep(2) # Jeda 2 detik sebelum coba lagi
                    continue
                else:
                    raise Exception(f"Gagal menghubungi {target_model} setelah {max_retries} kali percobaan. Server sibuk.")
            else:
                # Jika error lain (misal 404 Model Not Found atau API Key salah), langsung stop
                raise e

# --- MAIN FUNCTION ---
def geminiSearch(query):
    username = st.session_state.get('username')
    if not username:
        st.warning("Harap login terlebih dahulu.")
        return

    query = query.lower()

    if "rekomendasi" in query:
        handle_recommendation(username)
    
    elif "deskripsi" in query:
        user_description = query.replace("deskripsi", "").strip()
        
        if len(user_description) < 5:
            st.warning("Deskripsinya terlalu pendek. Ceritakan sedikit tentang plotnya. \nContoh: 'Deskripsi manhwa tentang anak sekolah yang diam-diam jago berantem'")
        else:
            handle_search_by_description(user_description)
    else:
        st.info("🤖 **Duta AI:** Ketik 'Rekomendasi' atau 'Deskripsi [cerita komik yg kamu cari]'")

# --- HANDLER 1: RECOMMENDATION ---
def handle_recommendation(username):
    st.markdown("### 🤖 AI Recommendation")
    
    if not client:
        return

    with st.spinner("Menganalisis selera bacamu..."):
        _, df_genres = sc.get_reading_stats(username)
        library = sc.get_user_library(username)
    
    top_genres = ", ".join(df_genres['Genre'].head(3).tolist()) if not df_genres.empty else "General Action"
    recent_titles = ", ".join([item['comic_title'] for item in library[:5]]) if library else "None"

    prompt = f"""
    You are an expert manga librarian for a site called Mangaread.org.
    User Profile:
    - Favorite Genres: {top_genres}
    - Recently Read: {recent_titles}

    Task: Recommend 4 manga/manhwa titles similar to user's taste.
    Output format: Just the titles separated by comma.
    Example: Solo Leveling, The Beginning After The End, Tower of God, One Piece
    """

    with st.spinner("Mencari rekomendasi..."):
        try:
            response = generate_content(prompt)
            suggested_titles = response.text.strip().split(',')
        except Exception as e:
            st.error(f"AI Error: {e}")
            return

    st.write(f"**Saran untukmu (Fans {top_genres}):**")
    
    found_count = 0
    cols = st.columns(4)
    
    for title in suggested_titles:
        clean_title = title.strip()
        results = searchComic(clean_title)
        
        if results:
            comic = results[0]
            found_count += 1
            col_idx = (found_count - 1) % 4
            with cols[col_idx]:
                with st.container(border=True):
                    st.image(comic['image'], use_container_width=True) 
                    st.markdown(f"**{comic['title']}**")
                    if st.button("Baca", key=f"rec_{comic['slug']}"):
                        st.session_state.selected_manga = comic
                        st.session_state.chapterlist = []
                        st.rerun()
    
    if found_count == 0:
        st.warning("Gemini menyarankan judul, tapi kami tidak menemukannya di database saat ini.")

# --- HANDLER 2: SEARCH BY DESCRIPTION ---
def handle_search_by_description(user_desc):
    st.markdown(f"### 🔍 Detektif Komik AI")
    st.info(f"**Clue dari kamu:** \"{user_desc}\"")

    if not client:
        return

    guessed_title = ""
    with st.spinner("AI sedang menebak judul dari ceritamu..."):
        prompt = f"""
        User Description: "{user_desc}"
        
        Task: Identify the ONE most likely manga/manhwa/manhua title that matches this plot description.
        Rules:
        1. Return ONLY the title. No explanation.
        2. If multiple match, pick the most famous one.
        3. If you really don't know, return "Unknown".
        """
        try:
            response = generate_content(prompt)
            guessed_title = response.text.strip()
        except Exception as e:
            st.error(f"Gagal menghubungi AI: {e}")
            return

    if "Unknown" in guessed_title or not guessed_title:
        st.error("Maaf, AI tidak bisa menebak judul dari deskripsi tersebut. Coba berikan detail nama karakter atau kekuatan uniknya.")
        return

    st.success(f"💡 Tebakan AI: **{guessed_title}**")

    with st.spinner(f"Mencari komik '{guessed_title}' di database..."):
        results = searchComic(guessed_title)
    
    if results:
        comic = results[0]
        
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(comic['image'], use_container_width=True)
        with col2:
            st.markdown(f"### {comic['title']}")
            st.write(f"Apakah ini komik yang kamu maksud?")
            
            if st.button("Ya, Baca Sekarang!", key="found_desc_read"):
                st.session_state.selected_manga = comic
                st.session_state.chapterlist = []
                st.rerun()
            
            if len(results) > 1:
                st.markdown("---")
                st.caption("Hasil pencarian lain yang mirip:")
                for alt_comic in results[1:4]:
                    if st.button(f"📖 {alt_comic['title']}", key=f"alt_{alt_comic['slug']}"):
                        st.session_state.selected_manga = alt_comic
                        st.session_state.chapterlist = []
                        st.rerun()
    else:
        st.warning(f"AI menebak judulnya adalah **'{guessed_title}'**, tapi sayang sekali judul itu tidak ditemukan di server Mangaread.")