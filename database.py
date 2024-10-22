import sqlite3

def connect_db():
    return sqlite3.connect('db.db')

def add_user(name, private_key, public_key, allowed_ips, date, usage):
        try:
            conn = connect_db()
            cursor = conn.cursor()
    
            cursor.execute('''  INSERT INTO users (name, private_key, public_key, allowed_ips, date, usage, used, last_used, status, percent_push, days_left_push)   VALUES (?, ?, ?, ?, ?, ?, 0, 0, 1, ?, ?)''', (name, private_key, public_key, allowed_ips, date, usage, "not sent", "not sent"))
    
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Database error: {str(e)}")
            return False



def remove_user(name):
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM users WHERE name = ?', (name,))
    
    conn.commit()
    conn.close()

def change_date(name, date):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET date = ? WHERE name = ?', (date, name))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error in change_date: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return None

def change_usage(name, usage):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET usage = ? WHERE name = ?', (usage, name))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error in change_usage: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return None

def get_user_by_name(name):
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE name = ?', (name,))
    user = cursor.fetchone()
    
    conn.close()
    
    return user


def get_user_by_pubkey(public_key):
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE public_key = ?', (public_key,))
    user = cursor.fetchone()
    
    conn.close()
    
    return user


def update_used(public_key, used):
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE users SET used = ? WHERE public_key = ?', (used, public_key))
    
    conn.commit()
    conn.close()


def update_last_used(public_key, last_used):
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE users SET last_used = ? WHERE public_key = ?', (last_used, public_key))
    
    conn.commit()
    conn.close()



def check_allowed_ips(ip_address):
    conn = connect_db()
    cursor = conn.cursor()
    
    query = "SELECT EXISTS(SELECT 1 FROM users WHERE allowed_ips = ? LIMIT 1)"
    cursor.execute(query, (ip_address,))
    
    result = cursor.fetchone()[0] == 1
    
    conn.close()
    return result


def get_all_users():
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users')

    # Fetch all the results
    users = cursor.fetchall()

    conn.commit()
    conn.close()

    return users

def change_status(name, status):
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE users SET status = ? WHERE name = ?', (status, name))
    
    conn.commit()
    conn.close()


def set_percent_push(name):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET percent_push = ? WHERE name = ?', ("sent", name))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error in change_date: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return None
    
def set_days_push(name):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute('UPDATE users SET days_left_push = ? WHERE name = ?', ("sent", name))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error in change_date: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return None
    
    
def reset_push(name):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET days_left_push = ?, percent_push = ? 
            WHERE name = ?
        ''', ("not sent", "not sent", name))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error in reset_push: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False