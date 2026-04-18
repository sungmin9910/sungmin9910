from pynput import keyboard
from datetime import datetime
import pymysql
import serial
import pynmea2
from urllib.parse import urlparse, parse_qs

DB_HOST = '203.254.153.113'
DB_USER = 'root'
DB_PASSWORD = 'Lab22512251!'
DB_NAME = 'lab225'
TABLE_NAME = 'qr'
DB_PORT = 3307

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )

# ? FmID 占쏙옙占쏙옙占쏙옙占쏙옙 占쌍쏙옙 APC_AD占쏙옙 占쏙옙회
def get_existing_apc_ad(fm_id):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = f"""
            SELECT APC_AD 
            FROM {TABLE_NAME} 
            WHERE FmID = %s AND APC_AD IS NOT NULL 
            ORDER BY APC_AD DESC 
            LIMIT 1
        """
        cursor.execute(query, (fm_id,))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        
        if result and result[0]:  
            return result[0]
        return None  
    except Exception as e:
        print(f"Error retrieving APC_AD from the database: {e}")
        return None

def save_to_db(data_dict):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # GPS 占쏙옙占쏙옙占쏙옙 占싻깍옙
        lat, lon = read_gps_data()
        data_dict['Lat'] = lat
        data_dict['lon'] = lon

        # A11 占쌤계에占쏙옙 占쏙옙占쏙옙占쏙옙 占시뤄옙占썽만 占쏙옙占쏙옙占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙
        query = f"""
            INSERT INTO {TABLE_NAME}
            (Lo, AC, FmID, FrT, Vt, Ct, HD, DD, Qt, Mt, HN, StD, Rp, 
             APC_AD, APC_WD, Lat, lon)
            VALUES
            (%(Lo)s, %(AC)s, %(FmID)s, %(FrT)s, %(Vt)s, %(Ct)s, %(HD)s, %(DD)s, %(Qt)s, 
             %(Mt)s, %(HN)s, %(StD)s, %(Rp)s, 
             %(APC_AD)s, %(APC_WD)s, %(Lat)s, %(lon)s)
        """
        
        # 占쏙옙占쏙옙 占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙 占쏙옙占쏙옙占쏙옙 占십울옙占쏙옙 占쏙옙占쏙옙占싶몌옙 占쏙옙占싶몌옙
        required_keys = ['Lo', 'AC', 'FmID', 'FrT', 'Vt', 'Ct', 'HD', 'DD', 'Qt', 'Mt', 'HN', 'StD', 'Rp', 'APC_AD', 'APC_WD', 'Lat', 'lon']
        filtered_data = {key: data_dict.get(key) for key in required_keys}

        cursor.execute(query, filtered_data)
        connection.commit()
        print("? A11 占쏙옙占쏙옙占싶곤옙 占쏙옙占쏙옙占싶븝옙占싱쏙옙占쏙옙 占쏙옙占쏙옙占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙퓸占쏙옙占쏙옙求占?")
    except Exception as e:
        print(f"Error saving data to the database: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()

def parse_qr_data(scanned_url):
    try:
        parsed_url = urlparse(scanned_url)
        query_params = parse_qs(parsed_url.query)

        fm_id = parsed_url.path.split('/')[-1]

        # URL占쏙옙占쏙옙 QR占쏙옙 占쏙옙占쏙옙獵占?占쏙옙占쏙옙 占쏙옙占쏙옙占싶몌옙 占쏙옙占쏙옙
        parsed_data = {
            'Lo': 'A11', # 占쏙옙 占쏙옙크占쏙옙트占쏙옙 A11 占쌤계를 占쏙옙占?            'FmID': fm_id,
            'AC': query_params.get('AC', [None])[0],
            'FrT': query_params.get('FrT', [None])[0],
            'Vt': query_params.get('Vt', [None])[0],
            'Ct': query_params.get('Ct', [None])[0],
            'HD': query_params.get('HD', [None])[0],
            'DD': query_params.get('DD', [None])[0],
            'Qt': query_params.get('Qt', [None])[0],
            'Mt': query_params.get('Mt', [None])[0],
            'HN': query_params.get('HN', [None])[0],
            'StD': query_params.get('StD', [None])[0],
            'Rp': query_params.get('Rp', [None])[0]
        }
        
        # A11占쏙옙 占쏙옙占쏙옙 占쏙옙占쏙옙: 占쏙옙占쏙옙 占쌤곤옙(A10)占쏙옙 APC_AD 占쏙옙占쏙옙 占쏙옙占쏙옙占싶쇽옙 채占쏙옙
        existing_apc_ad = get_existing_apc_ad(fm_id)
        parsed_data['APC_AD'] = existing_apc_ad
        
        # A11占쏙옙 占쏙옙占쏙옙 占쏙옙占쏙옙: 占쏙옙占쏙옙 占시곤옙占쏙옙 APC_WD (占쏙옙척占시곤옙)占쏙옙占쏙옙 占쏙옙占?        parsed_data['APC_WD'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return parsed_data
    except Exception as e:
        print(f"Error parsing QR data: {e}")
        return None

def on_key_press(key):
    try:
        if key == keyboard.Key.enter:
            global buffer
            scanned_data = ''.join(buffer).strip()
            print(f"Scanned data: {scanned_data}")

            parsed_data = parse_qr_data(scanned_data)
            if parsed_data:
                save_to_db(parsed_data)
            else:
                print("Failed to parse QR data.")
            
            buffer.clear()
        else:
            if hasattr(key, 'char') and key.char is not None:
                buffer.append(key.char)
    except Exception as e:
        print(f"Error handling key press: {e}")

def read_gps_data(port='/dev/ttyACM1', baudrate=9600):
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        while True:
            line = ser.readline().decode('utf-8', errors='ignore')
            if line.startswith('$GPGGA'):
                msg = pynmea2.parse(line)
                if msg.latitude and msg.longitude:
                    return msg.latitude, msg.longitude
    except Exception as e:
        print(f"Error reading GPS data: {e}")
        return None, None

buffer = []

if __name__ == "__main__":
    print("Waiting for QR code scan...")
    with keyboard.Listener(on_press=on_key_press) as listener:
        listener.join()