import streamlit as st
from script import script as sc

try:
    st.set_page_config(page_title='Login to Duta Comic', 
                       layout="centered", 
                       page_icon="assets/logo_duta_comic[1].png"
                       )
except:
    pass

if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'page' not in st.session_state:
    st.session_state['page'] = 'login'    

def display_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
            <div style='text-align: center;'>
            <h1>Welcome to Duta Comic🖐️</h1>
            <p style='color:grey'>Please Login before proceeding</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("", unsafe_allow_html=True)

        with st.container(border=True):
            username_input = st.text_input("Username", key="username_login") 
            password_input = st.text_input("Password", type="password", key="password_login")
            
            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("Login", key="login_btn", type="primary", use_container_width=True):
                if not username_input or not password_input:
                    st.warning("Please enter your username and password first")
                else:
                    is_correct = sc.check_user(username_input, password_input)
                    if is_correct:
                        st.session_state['page'] = 'app'
                        st.success("Login Berhasil!")
                        st.session_state['logged_in'] = True
                        st.session_state['username'] = username_input
                        st.rerun() 
                    else:
                        st.error("Username atau password salah.")

        st.markdown("<div style='text-align: center; margin-top: 10px; color: gray;'>Don't have an account?</div>", unsafe_allow_html=True)
        if st.button("Register", use_container_width=True):
            st.session_state['page'] = 'register'
            st.rerun()

if __name__ == "__main__":
    sc.create_table() 
    display_login_page()
else:
    sc.create_table()