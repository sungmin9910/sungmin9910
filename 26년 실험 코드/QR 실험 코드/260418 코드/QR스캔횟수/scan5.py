from pynput import keyboard
from datetime import datetime
import pymysql
import serial
import pynmea2
from urllib.parse import urlparse, parse_qs # URL 占식쏙옙占쏙옙 占쏙옙占쏙옙 占쏙옙占싱브러占쏙옙 占쌩곤옙

# DB 占쏙옙占쏙옙
DB_HOST = '203.254.153.113' # 占쏙옙占쏙옙 DB 占쏙옙占?DB_USER = 'root'
DB_PASSWORD = 'Lab22512251!'
DB_NAME = 'lab225'
TABLE_NAME = 'qr'
DB_PORT = 3307

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
        database=DB_NAME, port=DB_PORT
    )

def read_gps_data(port='/dev/ttyACM1', baudrate=9600):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        for _ in range(5): 
            line = ser.readline().decode('utf-8', errors='ignore')
            if line.startswith('$GPGGA'):
                msg = pynmea2.parse(line)
                if msg.latitude and msg.longitude:
                    ser.close(); return msg.latitude, msg.longitude
        ser.close(); return None, None
    except Exception as e:
        print(f"Error reading GPS data: {e}")
        return None, None

# === [占쏙옙占쏙옙占쏙옙 QR 占쏙옙占쏙옙占쏙옙 占식쏙옙 占쌉쇽옙] ===
def parse_qr_data(scanned_url):
    try:
        parsed_url = urlparse(scanned_url)
        fm_id = parsed_url.path.split('/')[-1]

        if not fm_id:
            print("FmID占쏙옙 QR 占쌘듸옙 URL占쏙옙 占쏙옙占쏙옙占싹댐옙.")
            return None

        # A15 占쌤계에占쏙옙占쏙옙 FmID占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙 占쏙옙占쏙옙占싶몌옙 占쏙옙회占싹몌옙 占쏙옙占쏙옙爛求占?
        parsed_data = {'Lo': 'A15', 'FmID': fm_id}

        connection = get_db_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        # [占쏙옙占쏙옙 占쏙옙占쏙옙] WHERE占쏙옙占쏙옙 FmID 占쏙옙占쏙옙占쏙옙 占쌩곤옙占싹울옙 占쏙옙확占쏙옙 占쏙옙占쏙옙占싶몌옙 占쏙옙占쏙옙占쏙옙
        query = f"SELECT * FROM {TABLE_NAME} WHERE Lo = 'A14' AND FmID = %s ORDER BY APC_StD DESC LIMIT 1"
        cursor.execute(query, (fm_id,))
        prev_record = cursor.fetchone()
        connection.close()

        if prev_record:
            parsed_data.update(prev_record)
        
        # 占쏙옙占쏙옙 占시곤옙(占쏙옙占?占시곤옙)占쏙옙 APC_OP占쏙옙 占쏙옙占?        parsed_data['APC_OP'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        parsed_data['Lo'] = 'A15' # Lo 占쏙옙占쏙옙 A15占쏙옙 占쌕쏙옙 확占쏙옙占싹곤옙 占쏙옙占쏙옙
        
        return parsed_data
    except Exception as e:
        print(f"Error parsing QR data: {e}")
        return None

# === [占쏙옙占쏙옙占쏙옙 DB 占쏙옙占쏙옙 占쌉쇽옙] ===
def save_to_db(data_dict):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        lat, lon = read_gps_data()
        data_dict['Lat'] = lat
        data_dict['lon'] = lon

        # DB占쏙옙 占쏙옙占쏙옙占싹댐옙 占시뤄옙占쏙옙 占쏙옙占쏙옙占싹깍옙 占쏙옙占쏙옙 占쏙옙占싶몌옙
        cursor.execute(f"SHOW COLUMNS FROM {TABLE_NAME}")
        db_columns = {col[0] for col in cursor.fetchall()}
        data_to_save = {k: v for k, v in data_dict.items() if k in db_columns}

        columns = ", ".join(data_to_save.keys())
        placeholders = ", ".join([f"%({key})s" for key in data_to_save.keys()])
        
        query = f"INSERT INTO {TABLE_NAME} ({columns}) VALUES ({placeholders})"
        cursor.execute(query, data_to_save)
        connection.commit()
        print("? A15 占쏙옙占쏙옙占싶곤옙 占쏙옙占쏙옙占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙퓸占쏙옙占쏙옙求占?")
    except Exception as e:
        print(f"? DB 占쏙옙占쏙옙 占쏙옙占쏙옙: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

buffer = []
def on_key_press(key):
    global buffer
    try:
        if key == keyboard.Key.enter:
            scanned_data = ''.join(buffer).strip()
            print(f"Scanned data: {scanned_data}")
            parsed_data = parse_qr_data(scanned_data)
            if parsed_data:
                save_to_db(parsed_data)
            else:
                print("? QR 占쏙옙占쏙옙占쏙옙 占식쏙옙 占쏙옙占쏙옙.")
            buffer.clear()
        elif hasattr(key, 'char') and key.char is not None:
            buffer.append(key.char)
    except Exception as e:
        print(f"Error handling key press: {e}")

if __name__ == "__main__":
    print("?? A15 占쏙옙占?占쏙옙캐占쏙옙 占쏙옙占?占쏙옙...")
    with keyboard.Listener(on_press=on_key_press) as listener:
        listener.join()