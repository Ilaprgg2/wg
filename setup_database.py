import sqlite3
from sqlite3 import Error

def create_connection():
    conn = None
    try:
        conn = sqlite3.connect('db.db')
        print(f"Successfully connected to SQLite database")
        return conn
    except Error as e:
        print(f"Error connecting to SQLite database: {e}")
    return conn

def create_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                private_key TEXT UNIQUE NOT NULL,
                public_key TEXT UNIQUE NOT NULL,
                allowed_ips TEXT UNIQUE NOT NULL,
                date TEXT,
                usage REAL,
                used REAL,
                last_used REAL,
                status INTEGER,
                percent_push TEXT, 
                days_left_push TEXT
            )
        ''')
        print("Table 'users' created successfully")
    except Error as e:
        print(f"Error creating table: {e}")

def main():
    conn = create_connection()
    if conn is not None:
        create_table(conn)
        conn.close()
    else:
        print("Error! Cannot create the database connection.")

if __name__ == '__main__':
    main()
