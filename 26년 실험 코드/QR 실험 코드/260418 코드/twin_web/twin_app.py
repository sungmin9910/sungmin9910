from flask import Flask, render_template, jsonify
from db import get_connection # 기존에 만든 db.py를 그대로 활용합니다.

app = Flask(__name__)

# 메인 3D 대시보드 화면
@app.route('/')
def index():
    return render_template('twin.html')

# 3D 화면이 1초마다 센서값을 물어볼 API 통로
@app.route('/api/sensor')
def get_sensor_data():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # A14(창고 입고) 단계의 가장 최신 온습도 데이터를 가져옵니다.
            cursor.execute("""
                SELECT Tp, Hm, APC_StD 
                FROM qr 
                WHERE Lo = 'A14' AND Tp IS NOT NULL 
                ORDER BY APC_StD DESC 
                LIMIT 1
            """)
            record = cursor.fetchone()
            
            if record:
                return jsonify({
                    "status": "success",
                    "temperature": float(record['Tp']),
                    "humidity": float(record['Hm']),
                    "timestamp": str(record['APC_StD'])
                })
            return jsonify({"status": "empty"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
    finally:
        conn.close()

if __name__ == '__main__':
    # 소비자용 8000번 포트와 겹치지 않도록 8001번 포트 사용
    app.run(host='0.0.0.0', port=8001)