import streamlit as st
from script import script as sc 
from script import login as lg
import resend, random #for the email

resend.api_key = st.secrets["resend"]["api_key"]

def sendOTP(otp:str,email:str):
    params = {
    "from": "support@rosblok.shop",
    "to": email,
    "subject": "Resending Email",
    "html": f"<strong>Your otp code is {otp}</strong>"
    }
    # Send the email if email exist
    email_response = resend.Emails.send(params)
    # debug 🥹
    print(email_response)
    return True
    
# Initialize session variables
if "reg_step" not in st.session_state:
    st.session_state.reg_step = 1 
if "otp" not in st.session_state:
    st.session_state.otp = ""

def register(): 
    # Center the content using columns
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
                    <div style='text-align: center;'>
                    <h1>Make an account -- </h1>
                    <p style='color:grey'>Join our comic geeks today</p>
                    </div>""", unsafe_allow_html= True)
        st.markdown("", unsafe_allow_html= True)
        
        with st.container(border=True):
            # fetch the input
            username = st.text_input("Username", key="reg_user")
            
            email_disabled = st.session_state.reg_step > 1
            email = st.text_input("Email")
            
            # this is for otp code before proveed
            if st.session_state.reg_step == 1:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Send Email", type="primary", use_container_width=True):
                    if not username or not email:
                        st.warning("Mohon isi semua kolom.")
                    else:
                        st.session_state.otp = "".join([str(random.randint(0, 9)) for _ in range(4)])  # fixed randint upper bound
                        if sendOTP(st.session_state.otp, email):
                            st.session_state.reg_step = 2
                            st.success(f"OTP sent to your email!")
                            st.rerun()

            elif st.session_state.reg_step == 2:
                st.info(f"Kode dikirim ke: {email}")
                otpInput = st.text_input("Enter OTP")
                
                col_otp1, col_otp2 = st.columns([1, 1])
                with col_otp1:
                    if st.button("Check", type="primary", use_container_width=True):
                        if otpInput == st.session_state.otp:
                            st.success("✅ OTP verified successfully!")
                            st.session_state.reg_step = 3
                            st.rerun()
                        else:
                            st.error("❌ Incorrect OTP.")
                with col_otp2:
                    if st.button("Ubah Email", use_container_width=True):
                        st.session_state.reg_step = 1
                        st.rerun()

            elif st.session_state.reg_step == 3:
                password = st.text_input("Password", type="password", key="reg_pass")
                confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Buat Akun", key="reg_button", type="primary", use_container_width=True):
                    # Validation
                    if not username or not email or not password or not confirm_password:
                        st.warning("Mohon isi semua kolom.")
                    elif password != confirm_password:
                        st.error("Password tidak cocok.")
                    else:
                        # calling if it already exist
                        success, message = sc.new_user(username, email, password)
                        
                        if success:
                            st.success(message)
                            st.info("Silakan kembali ke halaman Login.")
                            st.session_state.reg_step = 1
                            st.session_state.otp = ""
                            st.session_state['page'] = 'login'
                            st.rerun()
                        else:
                            st.error(message)

        st.markdown("<div style='text-align: center; margin-top: 10px; color: gray;'>Sudah punya akun?</div>", unsafe_allow_html=True)
        if st.button("Login", type="secondary", use_container_width=True):
            st.session_state['page'] = 'login'
            st.rerun()