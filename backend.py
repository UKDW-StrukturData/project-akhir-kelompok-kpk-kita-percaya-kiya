import resend, random,streamlit as st
resend.api_key = "re_CiXbj6zf_AN5gCW7WVsatczXWt8NmAFKj"

def sendOTP(otp:str,email:str):
    params = {
    "from": "support@rosblok.shop",
    "to": [email],
    "subject": "Resending Email",
    "html": f"<strong>Your otp code is {otp}</strong>"
    }
    email_response = resend.Emails.send(params)
    print(email_response)
    
if "otp" not in st.session_state:
    st.session_state.otp = ""
if "isOtpSent" not in st.session_state:
    st.session_state.isOtpSent = False
    
emailInput = st.text_input("Email: ") 
if st.button("Send Email"):
    st.session_state.isOtpSent = True
    st.session_state.otp = "".join([str(random.randint(0, 9)) for _ in range(4)]) 
    sendOTP(st.session_state.otp,emailInput)
    st.success(f"OTP sent to your email!")

st.write(f"Is OTP sent: {st.session_state.isOtpSent}")
# st.write(f"Generated OTP (for debug): {st.session_state.otp}")

otpInput = st.text_input("Enter OTP")
if st.button("Check"):
    if otpInput == st.session_state.otp:
        st.success("✅ OTP verified successfully!")
    else:
        st.error("❌ Incorrect OTP.")
