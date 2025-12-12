import streamlit as st
import mysql.connector
import bcrypt


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
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pengguna
    (user_id INT AUTO_INCREMENT PRIMARY KEY, 
      username VARCHAR(255) UNIQUE NOT NULL, 
      email VARCHAR(255) NOT NULL,
      password_hash VARCHAR(255) NOT NULL)
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookmark (
        bookmark_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        manga_title VARCHAR(255) NOT NULL,
        manga_url VARCHAR(512) NOT NULL,
        UNIQUE KEY unique_bookmark (user_id, manga_title),
        FOREIGN KEY (user_id) REFERENCES pengguna(user_id) ON DELETE CASCADE
    )
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
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        sql_command = "INSERT INTO pengguna (username, email, password_hash) VALUES (%s, %s, %s)"

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
    """Memverifikasi kredensial dan mengembalikan status, user_id, dan username."""
    try:
        conn = init_connection()
        if not conn.is_connected():
            conn.reconnect()
        cur = conn.cursor(dictionary=True) 
        
        sql_command = "SELECT user_id, password_hash FROM pengguna WHERE username = %s"
        
        cur.execute(sql_command, (username,)) 
        
        user_record = cur.fetchone()
        cur.close()
        
        if user_record:
            stored_hash = user_record['password_hash'].encode('utf-8')
            
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                user_id_dari_db = user_record['user_id']
                return True, user_id_dari_db, username 
        
        return False, None, None
        
    except Exception as e:
        print(f"Error saat check_user: {e}")
        return False, None, None

