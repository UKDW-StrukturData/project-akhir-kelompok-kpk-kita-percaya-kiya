import sqlite3
import bcrypt

DATABASE_FILE = 'user.db'

def create_table():
    conn = sqlite3.connect(DATABASE_FILE)
    cur = conn.cursor()
    # Kita ganti 'password' menjadi 'password_hash' agar aman
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pengguna
    (user_id INTEGER PRIMARY KEY AUTOINCREMENT, 
     username TEXT UNIQUE NOT NULL, 
     email TEXT NOT NULL,
     password_hash TEXT NOT NULL)
    """)
    conn.commit()
    conn.close()

def new_user(username, email, password):
    """Mendaftarkan pengguna baru dengan password yang di-hash."""
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cur = conn.cursor()
        
        # 1. HASH password menggunakan bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # 2. Gunakan placeholders (?) untuk keamanan (mencegah SQL Injection)
        sql_command = "INSERT INTO pengguna (username, email, password_hash) VALUES (?, ?, ?)"
        # Simpan hash-nya (sebagai string) ke database
        data_to_insert = (username, email, hashed_password.decode('utf-8'))
        
        cur.execute(sql_command, data_to_insert)
        conn.commit()
        return True, "Registrasi berhasil!"
        
    except sqlite3.IntegrityError:
        return False, "Username sudah terdaftar."
    except Exception as e:
        return False, f"Terjadi error: {e}"
    finally:
        if 'conn' in locals():
            conn.close()

def check_user(username, password):
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cur = conn.cursor()
        
        # 1. Ambil HASH dari database berdasarkan username
        # Gunakan '?' untuk keamanan
        sql_command = "SELECT password_hash FROM pengguna WHERE username = ?"
        
        # Kirim username sebagai tuple (,)
        cur.execute(sql_command, (username,)) 
        
        user_record = cur.fetchone() # Ambil satu hasil
        
        if user_record:
            # 2. 'user_record' adalah tuple, ambil hash-nya (item pertama)
            stored_hash = user_record[0].encode('utf-8')
            
            # 3. Periksa apakah password input (plain text) cocok dengan hash
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                return True # Password benar
        
        # Jika username tidak ditemukan ATAU password salah
        return False 
        
    except Exception as e:
        print(f"Error saat check_user: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
