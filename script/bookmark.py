import streamlit as st
import mysql.connector
from script.db_connection import init_connection

def init_connection():
    return mysql.connector.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"],
        port=st.secrets["mysql"]["port"]
    )

def insert_bookmark(user_id, manga_title, manga_url):
    print(f"DEBUG: Menerima User ID: {user_id}, Tipe: {type(user_id)}") # <-- TAMBAH INI
    if user_id is None:
        print("ERROR: User ID is None!")
        return False
    try:
        conn = init_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT 1 FROM bookmark
            WHERE user_id = %s AND manga_title = %s
        """, (user_id, manga_title))

        if cur.fetchone() is None:

            cur.execute("""
                INSERT INTO bookmark (user_id, manga_title, manga_url)
                VALUES (%s, %s, %s)
            """, (user_id, manga_title, manga_url))
            conn.commit()
            cur.close()
            conn.close()
            return True

        cur.close()
        conn.close()
        return False

    except Exception as e:
        print(f"Error insert_bookmark (User ID: {user_id}): {e}")
        return False


def get_bookmark(user_id):
    """Ambil semua bookmark user berdasarkan user_id (INT)."""
    try:
        conn = init_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT manga_title, manga_url
            FROM bookmark
            WHERE user_id = %s 
        """, (user_id,)) 

        data = cur.fetchall()
        cur.close()
        conn.close()
        return data
        
    except Exception as e:
        print(f"Error get_bookmark (User ID: {user_id}): {e}")
        return []


def delete_bookmark(user_id, manga_url):
    conn = None
    try:
        conn = init_connection()
        cursor = conn.cursor()

        query = "DELETE FROM bookmark WHERE user_id = %s AND manga_url = %s" 
        cursor.execute(query, (user_id, manga_url))
        conn.commit()
        if cursor.rowcount > 0:
            return True
        else:
            return False 

    except Exception as e:
        print(f"Error menghapus bookmark dari MySQL: {e}")
        return False
        
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()