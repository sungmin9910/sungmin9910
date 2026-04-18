from datetime import datetime
import pymysql
import serial
import time
from urllib.parse import urlparse, parse_qs

# DB 占쏙옙占쏙옙
DB_HOST = '203.254.153.113'
DB_USER = 'root'
DB_PASSWORD = 'Lab22512251!'
DB_NAME = 'lab225'
TABLE_NAME = 'qr'
DB_PORT = 3307


# GPS 占쏙옙占쏙옙
GPS_PORT = "/dev/ttyACM0"
BAUD_RATE = 9600
ser = serial.Serial(GPS_PORT, BAUD_RATE, timeout=1)

# GPS 占쏙옙환
def convert_to_decimal(latitude, longitude):
    try:
        lat_deg = int(latitude[:2])
        lat_min = float(latitude[2:])
        decimal_lat = lat_deg + (lat_min / 60)

        lon_deg = int(longitude[:3])
        lon_min = float(longitude[3:])
        decimal_lon = lon_deg + (lon_min / 60)

        return decimal_lat, decimal_lon
    except Exception as e:
        print(f"[ERROR] GPS 占쏙옙환 占쏙옙占쏙옙: {e}")
        return None, None

# GPS 占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙
def get_gps_data(timeout=3):
    """GPS 占쏙옙藪∽옙占?{timeout}占쏙옙 占쏙옙占쏙옙 占쏙옙표占쏙옙 占싻억옙占쏙옙占쏙옙占?占시듸옙占쌌니댐옙."""
    try:
        ser = serial.Serial(GPS_PORT, BAUD_RATE, timeout=1)
        start_time = time.time() # 占시듸옙 占쏙옙占쏙옙 占시곤옙
        
        while time.time() - start_time < timeout: # 占쏙옙占쏙옙占쏙옙 占시곤옙(3占쏙옙) 占쏙옙占싫몌옙 占시듸옙
            data = ser.readline().decode("utf-8", errors="ignore").strip()
            if data.startswith('$GPGGA'):
                parts = data.split(',')
                if len(parts) > 9 and parts[2] and parts[4]:
                    latitude, longitude = parts[2], parts[4]
                    decimal_lat, decimal_lon = convert_to_decimal(latitude, longitude)
                    if decimal_lat and decimal_lon:
                        ser.close()
                        print(f"[INFO] GPS 占쏙옙占쏙옙 占쏙옙占쏙옙: {decimal_lat}, {decimal_lon}")
                        return decimal_lat, decimal_lon
            time.sleep(0.1) # CPU 占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙
        
        # 타占쌈아울옙 占시곤옙占쏙옙 占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙 占쏙옙占쏙옙
        ser.close()
        print("[INFO] GPS 타占쌈아울옙. 占쏙옙호占쏙옙 찾占쏙옙 占쏙옙 占쏙옙占쏙옙占싹댐옙 (占실놂옙?).")
        return None, None
        
    except serial.SerialException as e:
        print(f"[ERROR] GPS 占쏙옙트({GPS_PORT}) 占쏙옙占쏙옙 占쏙옙占쏙옙: {e}")
        return None, None
    except Exception as e:
        print(f"[ERROR] GPS 占쏙옙占쏙옙占쏙옙 占싻깍옙 占쏙옙占쏙옙: {e}")
        return None, None

# DB 占쏙옙占쏙옙
def save_to_db(data_dict):
    try:
        connection = pymysql.connect(
            host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
            database=DB_NAME, port=DB_PORT
        )
        cursor = connection.cursor()

        # A10 占쌤계에占쏙옙 占쏙옙占쏙옙占쏙옙 占시뤄옙占썽만 占쏙옙占쏙옙占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙
        query = f"""
            INSERT INTO {TABLE_NAME}
            (Lo, AC, FmID, FrT, Vt, Ct, HD, DD, Qt, Mt, HN, StD, Rp, 
             APC_AD, Lat, lon)
            VALUES
            (%(Lo)s, %(AC)s, %(FmID)s, %(FrT)s, %(Vt)s, %(Ct)s, %(HD)s, %(DD)s, %(Qt)s, 
             %(Mt)s, %(HN)s, %(StD)s, %(Rp)s, 
             %(APC_AD)s, %(Lat)s, %(lon)s)
        """
        
        # data_dict占쏙옙占쏙옙 占쏙옙占쏙옙占쏙옙 占십울옙占쏙옙 키占쏙옙 占쏙옙占쌤쇽옙 占쏙옙占쏙옙 占쏙옙占쏙옙
        required_keys = ['Lo', 'AC', 'FmID', 'FrT', 'Vt', 'Ct', 'HD', 'DD', 'Qt', 'Mt', 'HN', 'StD', 'Rp', 'APC_AD', 'Lat', 'lon']
        filtered_data = {key: data_dict.get(key) for key in required_keys}

        cursor.execute(query, filtered_data)
        connection.commit()
        print("? A10 占쏙옙占쏙옙占싶곤옙 占쏙옙占쏙옙占싶븝옙占싱쏙옙占쏙옙 占쏙옙占쏙옙占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙퓸占쏙옙占쏙옙求占?")

    except Exception as e:
        print(f"[ERROR] DB 占쏙옙占쏙옙 占쏙옙占쏙옙: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            cursor.close()
            connection.close()

# QR 占쏙옙占쌘울옙 占식쏙옙
def parse_qr_data(scanned_url, latitude, longitude):
    try:
        parsed_url = urlparse(scanned_url)
        query_params = parse_qs(parsed_url.query)

        # FmID占쏙옙 URL 占쏙옙占쏙옙占?占쏙옙占쏙옙占쏙옙 占싸분울옙占쏙옙 占쏙옙占쏙옙 (占쏙옙: /qr/1 -> 1)
        fm_id = parsed_url.path.split('/')[-1]

        # 占쏙옙占쏙옙占쏙옙 占쏙옙占쏙옙占싶댐옙 URL 占식띰옙占쏙옙沽占쏙옙占?占쏙옙占쏙옙
        # .get(key, [None])[0]占쏙옙 占식띰옙占쏙옙叩占?占쏙옙占쏙옙 占쏙옙痢?占쏙옙占쏙옙占?占쏙옙占쏙옙占쏙옙치
        parsed_data = {
            'Lo': 'A10',  # 占쏙옙 占쏙옙크占쏙옙트占쏙옙 A10 占쌤계를 占쏙옙占?            'FmID': fm_id,
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
        
        # 占쏙옙占쏙옙 占시곤옙 占쏙옙 GPS 占쏙옙占쏙옙 占쌩곤옙
        parsed_data['APC_AD'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        parsed_data['Lat'] = latitude
        parsed_data['lon'] = longitude

        return parsed_data
    except Exception as e:
        print(f"[ERROR] QR 占식쏙옙 占쏙옙占쏙옙: {e}")
        return None

# 占쏙옙占쏙옙 占쏙옙占쏙옙
def main():
    """占쏙옙占쏙옙 占쏙옙占쏙옙 占쌉쇽옙"""
    print("?? A10 (APC 占쏙옙占쏙옙) 占쏙옙캐占쏙옙 占쏙옙占?占쏙옙 (占쏙옙캔 占쏙옙 Enter)...")
    while True:
        try:
            buffer = input().strip()
            if not buffer:
                continue

            print(f"?? 占쏙옙캔占쏙옙 占쏙옙占쏙옙占쏙옙: {buffer}")
            
            # 1. GPS占쏙옙 3占십곤옙 占시듸옙占싹곤옙, 占쏙옙호占쏙옙 占쏙옙占쏙옙占쏙옙 (None, None)占쏙옙 占쏙옙환占쏙옙占쏙옙
            latitude, longitude = get_gps_data(timeout=3) 

            # 2. GPS 占쏙옙占쏙옙 占쏙옙占싸울옙 占쏙옙占쏙옙占쏙옙占?(None占싱듸옙 占쏙옙占쏙옙 占쌍듸옙) 占식쏙옙 占쏙옙 占쏙옙占쏙옙 占쏙옙占쏙옙
            parsed_data = parse_qr_data(buffer, latitude, longitude)
            
            if parsed_data and parsed_data.get('AC'):
                save_to_db(parsed_data)
            else:
                print("?? QR 占식싱울옙 占쏙옙占쏙옙占쌩거놂옙 占십쇽옙 占쏙옙占쏙옙(AC)占쏙옙 占쏙옙占쏙옙占싹댐옙.")

        except KeyboardInterrupt:
            print("? 占쏙옙占쏙옙悶占?占쏙옙占쏙옙 占쏙옙占싸그뤄옙占쏙옙 占쏙옙占쏙옙퓸占쏙옙占쏙옙求占?")
            break
        except Exception as e:
            print(f"[ERROR] 占쏙옙占쏙옙 占쏙옙占쏙옙 占쏙옙占쏙옙 占쌩삼옙: {e}")

if __name__ == "__main__":
    main()