import tkinter as tk
from tkinter import ttk
from ttkbootstrap import Style
from PIL import Image, ImageTk
import qrcode
import pymysql # mysql.connector에서 pymysql로 통일
import os
import datetime as dt
from urllib.parse import urlparse
import hashlib
import json

# --- DB 연결 정보 ---
DB_HOST = "203.254.153.113"
DB_USER = "root"
DB_PASSWORD = "Lab22512251!"
DB_NAME = "lab225"
DB_PORT = 3307
TABLE_NAME = "qr"

# --- 블록체인 원장 파일 ---
BLOCKCHAIN_FILE = "blockchain_ledger.json"

def get_db_connection():
    return pymysql.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
        database=DB_NAME, port=DB_PORT, charset="utf8mb4"
    )

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

fruit_images = {
    "Apples": ["apple4.png", "apple3.png", "apple2.png"],
    "Pears": ["pear4.png", "pear3.png", "pear2.png"],
    "Peaches": ["peach4.png", "peach3.png", "peach2.png"],
    "Tangerines": ["tangerine4.png", "tangerine3.png", "tangerine2.png"],
    "Melons": ["koreanmelon4.png", "koreanmelon3.png", "koreanmelon2.png"]
}

# --- 해시 생성 및 블록체인 저장 ---
def calculate_hash(data_dict):
    data_str = json.dumps(data_dict, sort_keys=True, default=str).encode()
    return hashlib.sha256(data_str).hexdigest()

def save_to_blockchain(data_hash, metadata):
    entry = {
        "timestamp": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hash": data_hash,
        "metadata": metadata,
        "stage": "A12 (Sorting & Grading)"
    }
    
    chain_data = []
    if os.path.exists(BLOCKCHAIN_FILE):
        try:
            with open(BLOCKCHAIN_FILE, "r", encoding="utf-8") as f:
                chain_data = json.load(f)
        except:
            chain_data = []
    
    chain_data.append(entry)
    with open(BLOCKCHAIN_FILE, "w", encoding="utf-8") as f:
        json.dump(chain_data, f, indent=4, ensure_ascii=False)
    print(f"🔒 [Blockchain] A12 Block Recorded: {data_hash}")

# --- GUI 설정 ---
root = tk.Tk()
style = Style("flatly")
root.title("A12 자동 분류 및 무결성 검증 (PC 관리자용)")
root.geometry("1100x1200")

prev_data = {}

# 레이아웃 구성
for r in range(7): root.grid_rowconfigure(r, weight=1)
for c in range(2): root.grid_columnconfigure(c, weight=1)

scan_label = ttk.Label(root, text="A12 선별 및 등급 판정", font=("나눔고딕", 24, "bold"))
scan_label.grid(row=0, column=0, columnspan=2, pady=10)

# UX 개선: 스캔을 위한 명시적인 입력창 (포커스 분실 방지)
scan_frame = ttk.Frame(root)
scan_frame.grid(row=1, column=0, columnspan=2, pady=10)
ttk.Label(scan_frame, text="👉 이곳을 클릭하고 QR코드를 스캔하세요:", font=("나눔고딕", 12, "bold"), foreground="blue").pack(side="left", padx=10)
qr_entry = ttk.Entry(scan_frame, font=("나눔고딕", 12), width=50)
qr_entry.pack(side="left")
qr_entry.focus() # 프로그램 시작 시 포커스

frame1 = ttk.LabelFrame(root, text="기본 정보", padding="15"); frame1.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")
frame2 = ttk.LabelFrame(root, text="날짜/수량 정보", padding="15"); frame2.grid(row=2, column=1, padx=20, pady=10, sticky="nsew")
frame3 = ttk.LabelFrame(root, text="과일 정보", padding="15"); frame3.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
frame4 = ttk.LabelFrame(root, text="등급 입력", padding="15"); frame4.grid(row=3, column=1, padx=20, pady=10, sticky="nsew")

# 위젯 배치
ttk.Label(frame1, text="FmID").grid(row=0, column=0, sticky="e", pady=5, padx=5); fm_id_entry = ttk.Entry(frame1, width=20); fm_id_entry.grid(row=0, column=1)
ttk.Label(frame1, text="AC").grid(row=1, column=0, sticky="e", pady=5, padx=5); ac_entry = ttk.Entry(frame1, width=20); ac_entry.grid(row=1, column=1)
ttk.Label(frame1, text="Ct").grid(row=2, column=0, sticky="e", pady=5, padx=5); ct_entry = ttk.Entry(frame1, width=20); ct_entry.grid(row=2, column=1)

labels2 = ["HD", "DD", "HN", "Std", "Qt"]; entries2 = [ttk.Entry(frame2, width=20) for _ in labels2]; hd_entry, dd_entry, hn_entry, std_entry, qt_entry = entries2
for i, (t, e) in enumerate(zip(labels2, entries2)): ttk.Label(frame2, text=t).grid(row=i, column=0, sticky="e", pady=5, padx=5); e.grid(row=i, column=1, pady=5, padx=5)

labels3 = ["FrT", "Vt", "Mt"]; entries3 = [ttk.Entry(frame3, width=20) for _ in labels3]; fruit_type_entry, variety_entry, mt_entry = entries3
for i, (t, e) in enumerate(zip(labels3, entries3)): ttk.Label(frame3, text=t).grid(row=i, column=0, sticky="e", pady=5, padx=5); e.grid(row=i, column=1, pady=5, padx=5)

labels4 = ["A등급 수량", "B등급 수량", "C등급 수량", "결점률"]; entries4 = [ttk.Entry(frame4, width=20) for _ in labels4]; a_entry, b_entry, c_entry, defect_entry = entries4
for i, (t, e) in enumerate(zip(labels4, entries4)): ttk.Label(frame4, text=t).grid(row=i, column=0, sticky="e", pady=5, padx=5); e.grid(row=i, column=1, pady=5, padx=5)

# 저장 버튼
btn_save = ttk.Button(root, text="저장 및 등급별 QR 생성 (Block)", style="success.TButton", command=lambda: save_and_generate())
btn_save.grid(row=4, column=0, columnspan=2, pady=20, ipadx=30, ipady=10)

status_label = ttk.Label(root, text="스캐너 대기 중...", font=("나눔고딕", 12)); status_label.grid(row=5, column=0, columnspan=2, pady=10)

qr_frame = ttk.Frame(root, padding=20); qr_frame.grid(row=6, column=0, columnspan=2)
a_frame = ttk.Frame(qr_frame); a_frame.grid(row=0, column=0, padx=40); a_qr_label = ttk.Label(a_frame); a_qr_label.pack(); a_text_label = ttk.Label(a_frame, text="A등급 QR"); a_text_label.pack()
b_frame = ttk.Frame(qr_frame); b_frame.grid(row=0, column=1, padx=40); b_qr_label = ttk.Label(b_frame); b_qr_label.pack(); b_text_label = ttk.Label(b_frame, text="B등급 QR"); b_text_label.pack()
c_frame = ttk.Frame(qr_frame); c_frame.grid(row=0, column=2, padx=40); c_qr_label = ttk.Label(c_frame); c_qr_label.pack(); c_text_label = ttk.Label(c_frame, text="C등급 QR"); c_text_label.pack()

def generate_qr_with_image(data, fruit, grade_idx):
    qr = qrcode.QRCode(version=4, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

    if fruit in fruit_images:
        overlay_path = os.path.join(BASE_DIR, fruit_images[fruit][grade_idx])
        if os.path.exists(overlay_path):
            logo_size = int(img.size[0] * 0.25)
            logo = Image.open(overlay_path).resize((logo_size, logo_size), Image.LANCZOS).convert("RGBA")
            pos = ((img.size[0] - logo.size[0]) // 2, (img.size[1] - logo.size[1]) // 2)
            img.paste(logo, pos, mask=logo)
    return img

def handle_qr_data(event=None):
    global prev_data
    qr_data = qr_entry.get().strip()
    qr_entry.delete(0, tk.END)
    
    try:
        parsed_url = urlparse(qr_data)
        fm_id = parsed_url.path.split('/')[-1]

        if not fm_id:
            status_label.config(text="QR에서 FmID를 찾을 수 없음", foreground="red"); return

        conn = get_db_connection()
        try:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            # A11의 세척시간(APC_WD)을 기준으로 최신 데이터를 가져오도록 수정
            cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE FmID=%s AND Lo='A11' ORDER BY APC_WD DESC LIMIT 1", (fm_id,))
            row = cursor.fetchone()
        finally:
            conn.close()

        if not row:
            status_label.config(text="DB에서 A11(세척 완료) 데이터를 찾을 수 없음", foreground="red"); return

        prev_data = dict(row)

        all_entries = {"FmID": fm_id_entry, "AC": ac_entry, "Ct": ct_entry, "FrT": fruit_type_entry,
                       "Vt": variety_entry, "Mt": mt_entry, "HD": hd_entry, "DD": dd_entry,
                       "HN": hn_entry, "Std": std_entry, "Qt": qt_entry}
        for key, entry in all_entries.items():
            entry.delete(0, tk.END); entry.insert(0, str(prev_data.get(key, "") or ""))
            
        a_entry.delete(0, tk.END); b_entry.delete(0, tk.END); c_entry.delete(0, tk.END); defect_entry.delete(0, tk.END)
        status_label.config(text="✅ QR 스캔 완료 - 수량을 입력해주세요.", foreground="green")
        
        # 스캔이 성공하면 바로 수량을 입력할 수 있도록 A등급 입력칸으로 커서 자동 이동
        a_entry.focus()
        
    except Exception as e:
        status_label.config(text=f"QR 처리 오류: {e}", foreground="red")

def save_and_generate():
    global prev_data
    if not prev_data:
        status_label.config(text="QR 스캔부터 진행하세요", foreground="red"); return

    now = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    a, b, c, defect = a_entry.get(), b_entry.get(), c_entry.get(), defect_entry.get()
    
    if not all([a, b, c, defect]):
        status_label.config(text="등급 및 결점률을 모두 입력하세요", foreground="red"); return

    try:
        data_dict = prev_data.copy()
        data_dict.update({
            "Lo": "A12", 
            "AGrade": a, "BGrade": b, "CGrade": c, 
            "DefectRate": defect, 
            "APC_RT": now
        })
        
        # 무결성 해시
        integrity_hash = calculate_hash(data_dict)
        save_to_blockchain(integrity_hash, {"FmID": prev_data['FmID'], "Type": "Grading Result"})

        # DB 저장 (pymysql 문법으로 수정)
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(f"SHOW COLUMNS FROM {TABLE_NAME}")
            db_columns = {col[0] for col in cursor.fetchall()}
            data_to_insert = {k: v for k, v in data_dict.items() if k in db_columns}
            
            columns = ", ".join(data_to_insert.keys())
            placeholders = ", ".join([f"%({key})s" for key in data_to_insert.keys()])
            insert_query = f"INSERT INTO {TABLE_NAME} ({columns}) VALUES ({placeholders})"
            
            cursor.execute(insert_query, data_to_insert)
            conn.commit()
        finally:
            conn.close()

        # QR 생성
        base_url = "http://iampm.synology.me:8000"
        for i, (grade_count, qr_label, text_label, grade_name_kr, grade_name_en) in enumerate(zip(
            [a, b, c], [a_qr_label, b_qr_label, c_qr_label],
            [a_text_label, b_text_label, c_text_label],
            ['상', '중', '하'], ['A', 'B', 'C'])):

            qr_url = f"{base_url}/qr/{prev_data['FmID']}?grade={grade_name_kr}&AC={prev_data.get('AC','')}&FrT={prev_data.get('FrT','')}"
            img = generate_qr_with_image(qr_url, prev_data["FrT"], i)
            qr_filename = f"{prev_data['FmID']}_{grade_name_en}_QR.png"
            img.save(qr_filename)
            
            img_tk = ImageTk.PhotoImage(img.resize((220, 220)))
            qr_label.config(image=img_tk); qr_label.image = img_tk
            text_label.config(text=f"{grade_name_en}등급 QR - {grade_count}개")

        status_label.config(text=f"✅ 저장 및 보안처리 완료 (Hash: {integrity_hash[:10]}...)", foreground="blue")
        
        # 다음 작업을 위해 다시 스캔 창으로 커서 이동
        qr_entry.focus()
        
    except Exception as e:
        status_label.config(text=f"저장 실패: {e}", foreground="red")

qr_entry.bind("<Return>", handle_qr_data)
root.mainloop()