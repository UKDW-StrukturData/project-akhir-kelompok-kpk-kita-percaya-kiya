import streamlit as st
import mysql.connector
import bcrypt
from script.db_connection import init_connection

@st.cache_resource
def create_table():
    conn = init_connection()
    if not conn.is_connected():
        conn.reconnect()
    cur = conn.cursor()
    
    # Kita ganti 'password' menjadi 'password_hash' agar aman
    # user
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pengguna
    (user_id INT AUTO_INCREMENT PRIMARY KEY, 
     username VARCHAR(255) UNIQUE NOT NULL, 
     email VARCHAR(255) NOT NULL,
     password_hash VARCHAR(255) NOT NULL);
    """)
    
        # bookmark
    cur.execute("""
    CREATE TABLE IF NOT EXISTS bookmark (
        bookmark_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        manga_title VARCHAR(255) NOT NULL,
        manga_url VARCHAR(512) NOT NULL,
        UNIQUE KEY unique_bookmark (user_id, manga_title),
        FOREIGN KEY (user_id) REFERENCES pengguna(user_id) ON DELETE CASCADE
    );
    """)
    
        
    # i mean...... [split the genre ???? maybe] -> gonna look for it 
    cur.execute("""
    CREATE TABLE IF NOT EXISTS genres(
    genre_id INT PRIMARY KEY AUTO_INCREMENT,
    genre_name VARCHAR(50) UNIQUE DEFAULT 'unknown'
    )                
    """)
    
    #read history and preferences
    cur.execute("""
    CREATE TABLE IF NOT EXISTS read_history (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    manga_title TEXT NOT NULL,
    chapter_title TEXT NOT NULL,
    genre_id INT,
    read_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(genre_id)
    REFERENCES genres(genre_id) 
    ON UPDATE CASCADE 
    ON DELETE SET NULL, 
    FOREIGN KEY(user_id)
    REFERENCES pengguna(user_id)
    ON UPDATE CASCADE
    ON DELETE CASCADE
    );
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
        if err.errno == 1062: # Duplicate 
            return False, "Username sudah terdaftar."
        return False, f"Terjadi error database: {err}"
    except Exception as e:
        return False, f"Terjadi error: {e}"


def check_user(username, password):
    try:
        conn = init_connection()
        if not conn.is_connected():
            conn.reconnect()
        cur = conn.cursor(dictionary=True)
        
        # Fetch hash for username
        # Gunakan '%s' untuk keamanan
        sql_command = "SELECT * FROM pengguna WHERE username = %s"
        
        # Kirim username sebagai tuple (,)
        cur.execute(sql_command, (username,)) 
        
        user_record = cur.fetchone() # Ambil satu hasil
        cur.close()
        
        if user_record:
            stored_hash = user_record['password_hash'].encode('utf-8')
            
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                return True, user_record['user_id'], username
        
        return False, None, None 
        
    except Exception as e:
        print(f"Error saat check_user: {e}")
        return False, None, None


#add history
def history_insert(user_id, manga_title, chapter_title, genres: list):
    """
    Dipanggil saat user tekan tombol 'Baca'
    genres = ['Action','Fantasy']
    """
    try:
        conn = init_connection()
        cur = conn.cursor()

        for genre in genres:
            # pastikan genre ada
            genre = genre.strip().lower()
            cur.execute(
                """INSERT INTO genres (genre_name) VALUES (%s)
                ON DUPLICATE KEY UPDATE genre_id = LAST_INSERT_ID(genre_id);""",
                (genre,)
            )
            cur.execute(
                "SELECT genre_id FROM genres WHERE genre_name = %s",
                (genre,)
            )
            genre_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO read_history 
                (user_id, manga_title, chapter_title, genre_id)
                VALUES (%s,%s,%s,%s)
            """, (user_id, manga_title, chapter_title, genre_id))

        conn.commit()
        cur.close()
    except Exception as e:
        print("history_insert error:", e)

def select_history(user_id, title):
    conn = init_connection()
    if not conn.is_connected():
        conn.reconnect()
    cur = conn.cursor()
    cur.execute("""
    SELECT DISTINCT
    manga_title,
    chapter_title AS chapter_title
    FROM read_history  
    WHERE manga_title = %s    
    ORDER BY chapter_title DESC         
                """, (title,))
    
    history = cur.fetchall()
    conn.close()
    return history

def bar_chart_data(user_id):
    try:
        conn = init_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
        SELECT 
            CONCAT(DATE_FORMAT(tanggal, '%b'), ', ', DAY(tanggal), ' ', YEAR(tanggal)) AS tanggal,
            total
        FROM (
            SELECT DATE(read_at) AS tanggal, COUNT(*) AS total
            FROM read_history
            WHERE user_id = %s
            GROUP BY DATE(read_at)
        ) AS sub
        ORDER BY tanggal;
        """, (user_id,))
        data = cur.fetchall()
        cur.close()
        return data
    except Exception as e:
        print("bar_chart_data error:", e)
        return []


# =========================
# DATA UNTUK PIE CHART
# =========================
def genre_chart_data(user_id):
    try:
        conn = init_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("""
        SELECT g.genre_name AS genre, COUNT(*) AS total
        FROM read_history r
        JOIN genres g ON r.genre_id = g.genre_id
        WHERE r.user_id = %s
        GROUP BY g.genre_name
        ORDER BY total DESC
        """, (user_id,))
        data = cur.fetchall()
        cur.close()
        return data
    except Exception as e:
        print("genre_chart_data error:", e)
        return []
