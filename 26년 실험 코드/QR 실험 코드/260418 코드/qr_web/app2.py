# app.py
from flask import Flask, render_template, redirect, url_for
from db import get_connection
from flask import request

app = Flask(__name__)

# 과일 종류 하드코딩
FRUIT_TYPES = ["Apples", "Pears", "Peaches", "Tangerines", "Melons"]

# 과일 도감 링크
FRUIT_ENCYCLOPEDIA = {
    "Apples": "https://www.nongnet.or.kr/front/M000000224/picture/view.do?pictureSn=49&codeBuNo=&codeNo=&pageIndex=1",
    "Pears": "https://www.nongnet.or.kr/front/M000000224/picture/view.do?pictureSn=48&codeBuNo=&codeNo=&pageIndex=1",
    "Peaches": "https://www.nongnet.or.kr/front/M000000224/picture/view.do?pictureSn=47&codeBuNo=&codeNo=&pageIndex=1",
    "Tangerines": "https://www.nongnet.or.kr/front/M000000224/picture/view.do?pictureSn=45&codeBuNo=&codeNo=&pageIndex=1",
    "Melons": "https://www.nongnet.or.kr/front/M000000224/picture/view.do?pictureSn=28&codeBuNo=&codeNo=&pageIndex=2"
}

FRUIT_IMAGES = {
    "Apples": "Apple info.JPG",
    "Pears": "Pear info.JPG",
    "Peaches": "Peach info.JPG",
    "Tangerines": "Tangerine info.JPG",
    "Melons": "Melon info.JPG"
}

from flask import request

# app.py

# app.py

@app.route('/', methods=['GET', 'POST'])
@app.route('/fruit/<fruit_type>', methods=['GET', 'POST'])
def index(fruit_type=None):
    # 페이지네이션 설정
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    
    # FmID 검색 처리
    fm_id_search = request.args.get('fm_id', '', type=str)

    conn = get_connection()
    with conn.cursor() as cursor:
        # ✅ 각 FmID별로 가장 마지막(MAX) Lo 값을 가진 데이터만 선택하는 로직으로 변경
        
        # WHERE 조건절을 동적으로 구성하기 위한 준비
        conditions = []
        params = []

        if fruit_type:
            conditions.append("q1.FrT = %s")
            params.append(fruit_type)
        
        if fm_id_search:
            conditions.append("q1.FmID LIKE %s")
            params.append(f'%{fm_id_search}%')

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # ------------------------------------------------------------------
        # ❗ 핵심: 데이터 조회 쿼리 수정
        # 1. (서브쿼리 q2): FmID별로 가장 큰 Lo 값(max_lo)을 찾습니다.
        # 2. (메인쿼리 q1): qr 테이블(q1)과 서브쿼리(q2)를 FmID와 Lo 값으로 JOIN합니다.
        #    -> 이렇게 하면 각 FmID의 마지막 단계 데이터만 남게 됩니다.
        # ------------------------------------------------------------------
        
        # 데이터 레코드 조회 쿼리
        query = f"""
            SELECT q1.*
            FROM qr q1
            INNER JOIN (
                SELECT FmID, MAX(Lo) as max_lo
                FROM qr
                GROUP BY FmID
            ) q2 ON q1.FmID = q2.FmID AND q1.Lo = q2.max_lo
            {where_clause}
            ORDER BY q1.APC_AD DESC
            LIMIT %s OFFSET %s
        """
        
        # 데이터 조회 실행
        cursor.execute(query, tuple(params + [per_page, offset]))
        records = cursor.fetchall()

        # 전체 데이터 개수 조회 쿼리 (페이지네이션 계산용)
        count_query = f"""
            SELECT COUNT(*)
            FROM qr q1
            INNER JOIN (
                SELECT FmID, MAX(Lo) as max_lo
                FROM qr
                GROUP BY FmID
            ) q2 ON q1.FmID = q2.FmID AND q1.Lo = q2.max_lo
            {where_clause}
        """
        
        # 전체 개수 조회 실행
        cursor.execute(count_query, tuple(params))
        total_records = cursor.fetchone()['COUNT(*)']
    
    conn.close()

    total_pages = (total_records + per_page - 1) // per_page

    return render_template(
        'index.html',
        records=records,
        fruit_types=FRUIT_TYPES,
        selected_fruit=fruit_type,
        total_pages=total_pages,
        current_page=page,
        fm_id_search=fm_id_search
    )


@app.route('/fruit/encyclopedia/<fruit_name>')
def fruit_encyclopedia(fruit_name):
    # 과일에 대한 도감 링크가 존재하면 해당 링크로 리디렉션
    if fruit_name in FRUIT_ENCYCLOPEDIA:
        return redirect(FRUIT_ENCYCLOPEDIA[fruit_name])

    # 링크가 없다면, 기본 페이지로 리디렉션
    return redirect('/')

@app.route('/trace/<fmid>')
def trace(fmid):
    """특정 FmID를 받아 모든 공정 이력을 조회하는 함수"""
    conn = get_connection()
    with conn.cursor() as cursor:
        # WHERE 조건에서 Lo='A15'를 빼고, FmID를 기준으로 모든 데이터를 조회합니다.
        # Lo 순서대로 정렬하여 과정 순으로 보이게 합니다.
        cursor.execute("""
            SELECT * FROM qr 
            WHERE FmID = %s 
            ORDER BY Lo ASC, APC_AD ASC
        """, (fmid,))
        records = cursor.fetchall()
    conn.close()
    
    # 조회된 데이터를 새로운 템플릿 'trace.html'로 전달합니다.
    return render_template('trace.html', records=records, fmid=fmid)

@app.route('/qr/<fmid>')
def qr_trace(fmid):
    # URL의 'grade' 파라미터 값을 가져옵니다 (예: '상', '중', '하').
    # 만약 grade 파라미터가 없으면 None이 됩니다.
    grade = request.args.get('grade', None)

    conn = get_connection()
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT * FROM qr 
            WHERE FmID = %s 
            ORDER BY Lo ASC, APC_AD ASC
        """, (fmid,))
        records = cursor.fetchall()
    conn.close()
    
    encyclopedia_link = None
    encyclopedia_image = None
    if records:
        fruit_name = records[0].get('FrT')
        if fruit_name:
            encyclopedia_link = FRUIT_ENCYCLOPEDIA.get(fruit_name)
            encyclopedia_image = FRUIT_IMAGES.get(fruit_name)

    # 읽어온 등급 정보를 'single_grade'라는 변수 이름으로 html 파일에 전달합니다.
    return render_template(
        'consumer_trace.html', 
        records=records, 
        fmid=fmid,
        encyclopedia_link=encyclopedia_link,
        encyclopedia_image=encyclopedia_image,
        single_grade=grade
    )

if __name__ == '__main__':
    # 실제 서버에서는 Gunicorn 같은 전문 WAS가 앱을 실행하므로
    # 이 부분은 실행되지 않거나, 단순 실행용으로 둡니다.
    app.run()
