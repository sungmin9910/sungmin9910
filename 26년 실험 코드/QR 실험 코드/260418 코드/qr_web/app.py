from flask import Flask, render_template, request
from db import get_connection
import hashlib
import json
import os
import math

app = Flask(__name__)

# --- 과일 데이터 설정 ---
FRUIT_TYPES = ['사과', '샤인머스켓', '복숭아', '배', '포도']
FRUIT_IMAGES = {
    '사과': 'image/사과.png',
    '샤인머스켓': 'image/샤인머스켓.png',
    '복숭아': 'image/복숭아.png',
    '배': 'image/배.png',
    '포도': 'image/포도.png'
}
FRUIT_ENCYCLOPEDIA = {
    '사과': 'https://terms.naver.com/entry.naver?docId=1107936&cid=40942&categoryId=32711',
    '샤인머스켓': 'https://terms.naver.com/entry.naver?docId=5704403&cid=40942&categoryId=32711',
    '복숭아': 'https://terms.naver.com/entry.naver?docId=1103333&cid=40942&categoryId=32711',
    '배': 'https://terms.naver.com/entry.naver?docId=1099988&cid=40942&categoryId=32711',
    '포도': 'https://terms.naver.com/entry.naver?docId=1158525&cid=40942&categoryId=32711'
}

# --- 블록체인 설정 ---
BLOCKCHAIN_FILE = "blockchain_ledger.json"

def calculate_hash(data_dict):
    data_str = json.dumps(data_dict, sort_keys=True, default=str).encode()
    return hashlib.sha256(data_str).hexdigest()

# --- [1] 메인 페이지 (대시보드) 라우트 (이 부분이 없어서 404가 떴던 것입니다) ---
@app.route('/')
@app.route('/fruit/<fruit_type>')
def index(fruit_type=None):
    page = request.args.get('page', 1, type=int)
    per_page = 10
    fm_id_search = request.args.get('fm_id', '')

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 기본 쿼리 작성
            query = "SELECT * FROM qr WHERE 1=1"
            params = []

            # 2. 필터링 (과일 종류, 검색어)
            if fruit_type:
                query += " AND FrT = %s"
                params.append(fruit_type)
            
            if fm_id_search:
                query += " AND FmID LIKE %s"
                params.append(f"%{fm_id_search}%")

            # 3. 전체 개수 세기 (페이지네이션용)
            count_query = f"SELECT COUNT(*) as cnt FROM ({query}) as sub"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()['cnt']
            total_pages = math.ceil(total_count / per_page)

            # 4. 데이터 조회 (최신순)
            query += " ORDER BY APC_AD DESC LIMIT %s OFFSET %s"
            params.extend([per_page, (page - 1) * per_page])
            
            cursor.execute(query, params)
            records = cursor.fetchall()
    finally:
        conn.close()

    return render_template(
        'index.html',
        records=records,
        fruit_types=FRUIT_TYPES,
        selected_fruit=fruit_type,
        current_page=page,
        total_pages=total_pages,
        fm_id_search=fm_id_search
    )

# --- [2] 관리자용 상세 이력 라우트 ---
@app.route('/trace/<fmid>')
def trace(fmid):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM qr WHERE FmID = %s ORDER BY Lo ASC", (fmid,))
            records = cursor.fetchall()
    finally:
        conn.close()
    return render_template('trace.html', records=records, fmid=fmid)

# --- [3] 소비자용 QR 조회 라우트 ---
@app.route('/qr/<fmid>')
def qr_trace(fmid):
    grade = request.args.get('grade', None)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM qr WHERE FmID = %s ORDER BY Lo ASC, APC_AD ASC", (fmid,))
            records = cursor.fetchall()
    finally:
        conn.close()
    
    encyclopedia_link = None
    encyclopedia_image = None
    if records:
        fruit_name = records[0].get('FrT')
        encyclopedia_link = FRUIT_ENCYCLOPEDIA.get(fruit_name)
        encyclopedia_image = FRUIT_IMAGES.get(fruit_name)

    # 무결성 검증
    verification_status = "UNKNOWN"
    if records:
        latest_record = records[-1]
        current_hash = calculate_hash(latest_record)
        
        if os.path.exists(BLOCKCHAIN_FILE):
            try:
                with open(BLOCKCHAIN_FILE, "r", encoding="utf-8") as f:
                    chain_data = json.load(f)
                
                is_verified = False
                for block in chain_data:
                    if block.get('hash') == current_hash:
                        is_verified = True
                        break
                
                if is_verified:
                    verification_status = "VERIFIED"
                else:
                    verification_status = "TAMPERED"
            except:
                verification_status = "ERROR"
        else:
            verification_status = "NO_LEDGER"

    return render_template(
        'consumer_trace.html',  # HTML 파일 이름 확인 필요 (consumer_trace2.html 이면 수정)
        records=records, 
        fmid=fmid,
        encyclopedia_link=encyclopedia_link,
        encyclopedia_image=encyclopedia_image,
        single_grade=grade,
        verification_status=verification_status
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)