import streamlit as st
import script as sc

if 'username' not in st.session_state:
    st.session_state['username'] = None
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'page' not in st.session_state:
    st.session_state['page'] = 'login' 
    
st.set_page_config(
    page_title="Duta Comic - Login",
    page_icon="Last-Semester-Project/assets/logo_duta_comic[1].png",
    layout="centered"
)

#login if no user 
def display_login_page():
    st.markdown(
        """
        <h2>Welcome to Duta Comic🖐️</h2>
        <p>Please Login before proceed any further</p>
        """,
        unsafe_allow_html=True
    )
    username_input = st.text_input("Username", key="username_login") 
    password_input = st.text_input("Password", type="password", key="password_login")

    login, register_col = st.columns([1, 0.4])
    with login:
        if st.button("Login", key="login_btn", type="primary"):
            if not username_input or not password_input:
                st.warning("Please enter your username and password first")
            else:
                is_correct = sc.check_user(username_input, password_input)
                if is_correct:
                    #change state
                    st.session_state['page'] = 'app'
                    st.success("Login Berhasil!")
                    st.session_state['logged_in'] = True
                    st.session_state['username'] = username_input
                
                    st.rerun() 
                else:
                    st.error("Username atau password salah.")
                    
    with register_col:
        st.markdown("Don't have an account?")
        if st.button("Register"):
            print(st.session_state['page'])
            st.session_state['page'] = 'register'
            print("setelah",st.session_state['page'])
            st.rerun()

sc.create_table() 