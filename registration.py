import streamlit as st
import script as sc 
import login as lg
import resend, random #untuk emailnya

resend.api_key = "re_CiXbj6zf_AN5gCW7WVsatczXWt8NmAFKj"
def sendOTP(otp:str,email:str):
    params = {
    "from": "support@rosblok.shop",
    "to": [email],
    "subject": "Resending Email",
    "html": f"<strong>Your otp code is {otp}</strong>"
    }
    # Send the email if email exist
    email_response = resend.Emails.send(params)
    # Print response
    print(email_response)
    
# Initialize session variables
if "otp" not in st.session_state:
    st.session_state.otp = ""
if "isOtpSent" not in st.session_state:
    st.session_state.isOtpSent = False

def register(): 
    st.markdown("""
                <span>
                <h1>Make an account -- </h1>
                <p style=  color:grey>Join our comic geeks today</p>
                </span>""", unsafe_allow_html= True)
    st.markdown("", unsafe_allow_html= True)
    
    # Ambil input dari pengguna
    username = st.text_input("Username", key="reg_user")
    email = st.text_input("Email", key="reg_email")
    
    #ini mulai buat otp dl
    # --- Send OTP button ---
    if st.button("Send Email"):
        st.session_state.isOtpSent = True
        st.session_state.otp = "".join([str(random.randint(0, 9)) for _ in range(4)])  # fixed randint upper bound
        sendOTP(st.session_state.otp,email)
        st.success(f"OTP sent to your email!")

        st.write(f"Is OTP sent: {st.session_state.isOtpSent}")
        # st.write(f"Generated OTP (for debug): {st.session_state.otp}")

        otpInput = st.text_input("Enter OTP")
        if st.button("Check"):
            if otpInput == st.session_state.otp:
                st.success("✅ OTP verified successfully!")
            else:
                st.error("❌ Incorrect OTP.")
    password = st.text_input("Password", type="password", key="reg_pass")
    confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm")

    if st.button("Buat Akun", key="reg_button", type="primary"):
        # Validasi input
        if not username or not email or not password or not confirm_password:
            st.warning("Mohon isi semua kolom.")
        elif password != confirm_password:
            st.error("Password tidak cocok.")
        else:
            # Panggil fungsi new_user buat cek bolo ada ga di db
            success, message = sc.new_user(username, email, password)
            
            if success:
                st.success(message)
                st.info("Silakan kembali ke halaman Login.")
            else:
                st.error(message)
        st.rerun()

    if st.button("Login", type="secondary"):
        st.session_state['page'] = 'login'
        st.rerun()