# import streamlit as st
# import pandas as pd
# import altair as alt
# from script import script as db          
# import script.bookmark as bk
# import requests
# from io import BytesIO
# import datetime
# from bs4 import BeautifulSoup
# import scrape as sc          

# def display_bookmark_grid():
#     st.markdown("## ⭐ Daftar Bookmark Kamu")

#     user_id = st.session_state.get("user_id")
#     if not user_id:
#         st.error("User ID tidak ditemukan.")
#         return

#     bookmarks = bk.get_bookmark(user_id)
#     if not bookmarks:
#         st.warning("Belum ada bookmark.")
#         return

#     cols = st.columns(4)

#     for i, (title, url) in enumerate(bookmarks):
#         detail = sc.get_comic_detail(url)

#         with cols[i % 4]:
#             with st.container(border=True):

#                 # Poster
#                 if detail["image"]:
#                     st.image(detail["image"], use_container_width=True)
#                 else:
#                     st.markdown(
#                         "<div style='height:200px;background:#eee;text-align:center;line-height:200px;'>No Image</div>",
#                         unsafe_allow_html=True
#                     )

#                 st.markdown(f"**{title}**")
#                 st.markdown(f"⭐ Rating: `{detail['rating']}`")
#                 st.divider()

#                 if st.button("Baca Sekarang", key=f"read_{i}", use_container_width=True):
#                     st.session_state.selected_manga = {
#                         "title": title,
#                         "link": url,
#                         "image": detail["image"],
#                         "slug": title.lower().replace(" ", "-"),
#                         "rating": detail["rating"]
#                     }
#                     st.session_state.chapterlist = []
#                     st.rerun()

#                 if st.button("❌ Hapus Bookmark", key=f"del_{i}", use_container_width=True):
#                     if bk.delete_bookmark(user_id, url):
#                         st.success(f"{title} dihapus")
#                         st.rerun()


# def show_profile():
#     # --- HEADER SECTION ---
#     if 'show_bookmarks' not in st.session_state:
#         st.session_state.show_bookmarks = False

#     username = st.session_state.get('username', 'Guest')
#     user_id = st.session_state.get("user_id")

#     st.markdown(f"### 👤 Profile — **{username}**")
#     st.divider()

#     # --- REKAP BACAAN SECTION ---
#     st.subheader("Rekap bacaan komik")

#     col_chart1, col_chart2 = st.columns([2, 1], gap="medium")

#     # =========================
#     # BAR CHART (TIMELINE)
#     # =========================
#     timeline_raw = db.bar_chart_data(user_id)

#     with col_chart1:
#         st.markdown("##### 📅 Timeline Aktivitas")

#         if timeline_raw:
#             df_timeline = pd.DataFrame(timeline_raw)
#             df_timeline["tanggal"] = pd.to_datetime(df_timeline["tanggal"])

#             bar_chart = alt.Chart(df_timeline).mark_bar(
#                 cornerRadiusTopLeft=5,
#                 cornerRadiusTopRight=5
#             ).encode(
#                 x=alt.X("tanggal:T", title="Tanggal"),
#                 y=alt.Y("total:Q", title="Komik Dibaca"),
#                 tooltip=["tanggal:T", "total:Q"]
#             ).properties(height=250)

#             st.altair_chart(bar_chart, use_container_width=True)
#         else:
#             # fallback ke dummy
#             st.info("belum ada riwayat bacaan")

#     genre_raw = db.genre_chart_data(user_id)

#     with col_chart2:
#         st.markdown("##### 🎭 Genre Favorit")

#         if genre_raw:
#             df_genre = pd.DataFrame(genre_raw)

#             pie_chart = alt.Chart(df_genre).mark_arc(innerRadius=40).encode(
#                 theta=alt.Theta("total:Q"),
#                 color=alt.Color("genre:N"),
#                 tooltip=["genre", "total"]
#             ).properties(height=250)

#             st.altair_chart(pie_chart, use_container_width=True)
#         else:
#             st.info("belum ada genre favorit")

#     st.markdown("<br>", unsafe_allow_html=True)

#     # --- BOOKMARK SECTION ---
#     col_btn_layout = st.columns([1, 3])
#     with col_btn_layout[0]:
#         btn_label = "Sembunyikan Bookmark" if st.session_state.show_bookmarks else "⭐ Bookmark Kamu"
#         if st.button(btn_label, use_container_width=True):
#             st.session_state.show_bookmarks = not st.session_state.show_bookmarks
#             st.rerun()

#     if st.session_state.show_bookmarks:
#         display_bookmark_grid()
#         st.divider()


# if __name__ == "__main__":
#     st.set_page_config(layout="wide")
#     show_profile()


a = []
b = []
for i in a:
    b.append(i)
print(b)