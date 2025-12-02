import streamlit as st
import requests
from bs4 import BeautifulSoup

BASE_API = 'https://www.mangaread.org/'

if 'current_chapter_link' not in st.session_state:
    st.session_state['current_chapter_link'] = None

def getComicList(filter=None, page=1, order= None):
    try:
        if filter is not None:
            base_url = f"{BASE_API}genres/{filter}/"
        else:
            base_url = f"{BASE_API}"
        
        # print(filter)
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}page/{page}/"
        
        if order and filter:
            url = f"{url}?m_orderby={order}"    
        else:
            url = f"{url}"

        st.write(f"Mengambil data dari: {url}") # Debugging URL
        
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            comics = []
            
            for item in soup.select("div.page-item-detail"):
                title_link_elem = item.select_one("div.item-summary h3.h5 a")
                img_elem = item.select_one("div.item-thumb a img")
                print(img_elem, end="\n")
                if not (title_link_elem and img_elem):
                    continue

                link = title_link_elem["href"]
                
                try:
                    slug = link.split('/manga/')[1].strip('/')
                except IndexError:
                    continue 
                
                rating_elem = item.select_one("div.post-total-rating span")
                if not rating_elem:
                    rating_elem = "N/A"

                rating_text = float(rating_elem.get_text(strip=True) if rating_elem else "N/A")
                comics.append({
                    "title": title_link_elem.get_text(strip=True),
                    "link": link,
                    "image": img_elem.get("src"),
                    "slug": slug,
                    "rating": rating_text 
                })
                print(img_elem)
                # print(comics)

                
            if not comics:
                st.warning(f"Tidak ada komik ditemukan di halaman {page}. Mungkin ini halaman terakhir.")
                return []
                
            return comics
        else:
            st.warning(f"Gagal mengambil data (status {resp.status_code}). Diblokir?")
            return []
    except Exception as e:
        st.error(f"Terjadi kesalahan saat mengambil data: {e}")
        return []

def scrape_img(link, status = True):
    st.session_state['current_chapter_link'] = link
    ch_link = link
    
    try:
        resp = requests.get(ch_link, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        image_urls = []
        reading_content = soup.select_one('div.reading-content')
        
        if reading_content:
            img_tags = reading_content.find_all('img')
            # print(img_tags)
            for img in img_tags:
                url = img.get('data-src') or img.get('data-lazy-src') or img.get('src')
                if url and url.strip():
                    image_urls.append(url.strip())
        else:
            return None
        return image_urls
    except Exception as e:
        st.error(f"❌ Error saat scraping konten chapter: {e}")
        return []
def searchComic(keyword):
    try:
        url = f"{BASE_API}?s={keyword.replace(' ', '+')}&post_type=wp-manga"
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            st.warning("Gagal mengakses halaman search.")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        comics = []

        results = soup.select("div.c-tabs-item__content")
        if not results:
            return []
        
        for item in results:
            title_el = item.select_one("h3 a")
            img_el = item.select_one("img")

            if not title_el or not img_el:
                continue

            title_text = title_el.get_text(strip=True)

            if keyword.lower() not in title_text.lower():
                continue

            link = title_el["href"]
            slug = link.split("/manga/")[-1].strip("/")
            rating_elem = item.select_one("div.post-total-rating span")
            if not rating_elem:
                rating_elem = "N/A"
            
            rating_text = float(rating_elem.get_text(strip=True) if rating_elem else "N/A")
            comics.append({
                "title": title_text,
                "link": link,
                "image": img_el.get("data-src") or img_el.get("src"),
                "slug": slug,
                "rating": rating_text
            })
            print(rating_text)
        return comics

    except Exception as e:
        st.error(f"Error search: {e}")
        return []
def next_chapter():
    pass
def prev_chapter():
    cur_link = st.session_state['current_chapter_link']
    
    try:
        resp = requests.get(cur_link, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        image_urls = []
        reading_content = soup.select_one('div.nav-previous')
        print(reading_content)
        if reading_content:
            print(reading_content)
            # img_tags = reading_content.find_all('img')
            # # print(img_tags)
            # for img in img_tags:
            #     url = img.get('data-src') or img.get('data-lazy-src') or img.get('src')
            #     if url and url.strip():
            #         image_urls.append(url.strip())
        else:
            return None
        return image_urls
    except Exception as e:
        st.error(f"❌ Error saat scraping konten chapter: {e}")
        return []