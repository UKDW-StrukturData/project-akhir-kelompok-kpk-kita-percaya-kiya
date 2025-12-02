import streamlit as st
import mysql.connector
import bcrypt

@st.cache_resource
def init_connection():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"]["port"]
    )

def create_table():
    conn = init_connection()
    if not conn.is_connected():
        conn.reconnect()
    cur = conn.cursor()
    
    # Kita ganti 'password' menjadi 'password_hash' agar aman
   
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pengguna
    (user_id INT AUTO_INCREMENT PRIMARY KEY, 
     username VARCHAR(255) UNIQUE NOT NULL, 
     email VARCHAR(255) NOT NULL,
     password_hash VARCHAR(255) NOT NULL)
    """)
    conn.commit()
    cur.close()

def new_user(username, email, password):
    """Mendaftarkan pengguna baru dengan password yang di-hash."""
    try:
        conn = init_connection()
        if not conn.is_connected():
            conn.reconnect()
        cur = conn.cursor()
        
        # HASH password using bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Prevent sqlk injection
        sql_command = "INSERT INTO pengguna (username, email, password_hash) VALUES (%s, %s, %s)"
        
        # Store hash as string 
        data_to_insert = (username, email, hashed_password.decode('utf-8'))
        
        cur.execute(sql_command, data_to_insert)
        conn.commit()
        cur.close()
        return True, "Registrasi berhasil!"
        
    except mysql.connector.Error as err:
        if err.errno == 1062: # Duplicate entry error code
            return False, "Username sudah terdaftar."
        return False, f"Terjadi error database: {err}"
    except Exception as e:
        return False, f"Terjadi error: {e}"

def check_user(username, password):
    try:
        conn = init_connection()
        if not conn.is_connected():
            conn.reconnect()
        cur = conn.cursor()
        
        # Fetch hash for username
        # Gunakan '%s' untuk keamanan
        sql_command = "SELECT password_hash FROM pengguna WHERE username = %s"
        
        # Kirim username sebagai tuple (,)
        cur.execute(sql_command, (username,)) 
        
        user_record = cur.fetchone() # Ambil satu hasil
        cur.close()
        
        if user_record:
            # 'user_record' is a hash, take the first
            stored_hash = user_record[0].encode('utf-8')
            
            # Periksa apakah password input (plain text) cocok dengan hash
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                return True # Password benar
        
        # Jika username tidak ditemukan ATAU password salah
        return False 
        
    except Exception as e:
        print(f"Error saat check_user: {e}")
        return False