import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import xml.etree.ElementTree as ET
from tkcalendar import DateEntry
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from PIL import Image, ImageTk
import datetime
import mysql.connector
from urllib.parse import urlencode
import re
import os

# --- [추가] 무결성 검증을 위한 라이브러리 ---
import hashlib
import json

# --- DB 연결 정보 (기존 유지) ---
DB_HOST = "203.254.153.113"
DB_USER = "root"
DB_PASSWORD = "Lab22512251!"
DB_NAME = "lab225"
DB_PORT = 3307

# --- [추가] 블록체인 시뮬레이션 파일 ---
BLOCKCHAIN_FILE = r"Z:\docker\smartfarm_app\blockchain_ledger.json"

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
        database=DB_NAME, charset="utf8mb4",
        collation="utf8mb4_general_ci", port=DB_PORT
    )

# 변수들
zip_codes = ["55630", "55631", "55632", "55633", "55634", "55635"]
fruit_types = ["Apples", "Pears", "Peaches", "Tangerines", "Melons"]
farming_methods = ["Organic", "Conventional"]

fruit_images = {
    "Apples": "apple.png", "Pears": "pear.png", "Peaches": "peach.png",
    "Tangerines": "tangerine.png", "Melons": "koreanmelon.png"
}

font_size = 15
uniform_combobox_width = 25

# --- [추가] 해시 생성 및 블록체인 저장 함수 ---
def calculate_hash(data_dict):
    """데이터 딕셔너리를 SHA-256 해시값으로 변환"""
    # 딕셔너리 정렬 후 문자열 변환 (순서가 바뀌면 해시가 달라지므로 정렬 필수)
    data_str = json.dumps(data_dict, sort_keys=True, default=str).encode()
    return hashlib.sha256(data_str).hexdigest()

def save_to_blockchain(data_hash, metadata):
    """해시값을 로컬 JSON 파일에 저장 (블록체인 기록 시뮬레이션)"""
    entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hash": data_hash,
        "metadata": metadata  # 어떤 데이터의 해시인지 식별용
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
    
    print(f"🔒 [Blockchain] Block Recorded: {data_hash}")

# --- 기존 헬퍼 함수들 ---
def format_phone_number(entry):
    current_text = entry.get()
    formatted_text = re.sub(r'\D', '', current_text)
    entry.delete(0, tk.END)
    entry.insert(0, formatted_text)

def get_selected_harvest_date(): return harvest_date_picker.get_date()
def get_selected_deliver_date(): return deliver_date_picker.get_date()
def get_selected_storage_date(): return storage_date_picker.get_date()

def generate_filename(area_code, farmer_id, harvest_date):
    formatted_date = harvest_date.strftime('%y%m%d')
    return f"{area_code}{farmer_id}{formatted_date}"

# QR 코드 생성 함수 (기존 유지)
def generate_qr_code(data, filename):
    base_url = "http://iampm.synology.me:8000"
    key_map = {
        "Area Code": "AC", "Farmer ID": "FmID", "Contact Info": "Ct", "Fruit Type": "FrT",
        "Variety": "Vt", "Harvest Date": "HD", "Deliver Date": "DD", "Storage Date": "StD",
        "Farming Method": "Mt", "Harvesting Number": "HN", "Quantity": "Qt", "Ag Practice": "Rp"
    }
    params = {}
    for key, value in data.items():
        mapped_key = key_map.get(key)
        if mapped_key:
            params[mapped_key] = value

    farmer_id = params.pop('FmID', '')
    query_string = urlencode(params)
    qr_url = f"{base_url}/qr/{farmer_id}?{query_string}&source=A00"

    print(f"[INFO] QR URL: {qr_url}")

    qr = qrcode.QRCode(version=4, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
    qr.add_data(qr_url)
    qr.make(fit=True)
    qr_img = qr.make_image(image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer())

    fruit_type = data.get("Fruit Type")
    fruit_filename = fruit_images.get(fruit_type)
    
    # 이미지 경로 처리 개선
    if fruit_filename:
        if os.path.exists(fruit_filename):
            fruit_image_path = fruit_filename
        else:
            fruit_image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), fruit_filename)
    else:
        fruit_image_path = None

    if fruit_image_path and os.path.exists(fruit_image_path):
        try:
            logo = Image.open(fruit_image_path).convert("RGBA")
            logo = logo.resize((200, 200), Image.LANCZOS)
            qr_img = qr_img.convert("RGBA")
            pos = ((qr_img.size[0] - logo.size[0]) // 2, (qr_img.size[1] - logo.size[1]) // 2)
            qr_img.paste(logo, pos, mask=logo)
        except Exception as e:
            print(f"[ERROR] Logo insertion failed: {e}")

    file_path = f"{filename}_QR.png"
    qr_img.save(file_path)

    qr_img_resized = qr_img.resize((150, 150), Image.LANCZOS)
    qr_image = ImageTk.PhotoImage(qr_img_resized)
    qr_label.config(image=qr_image)
    qr_label.image = qr_image

# --- [핵심 수정] 저장 함수 ---
current_data_cache = {} # 검증 실험을 위해 마지막 저장 데이터를 임시 보관

def save_all_formats():
    global current_data_cache  # 검증을 위해 데이터를 잠시 기억하는 변수 사용
    
    # 1. GUI 입력창에서 값 가져오기
    area_code = area_code_combobox.get()
    farmer_id = farmer_id_entry.get()
    fruit_type = fruit_type_combobox.get()
    variety = variety_combobox.get()
    contact_info = contact_info_entry.get()
    harvest_date = get_selected_harvest_date()
    deliver_date = get_selected_deliver_date()
    storage_date = get_selected_storage_date()
    farming_method = farming_method_combobox.get()
    harvesting_number = harvesting_number_entry.get()
    quantity = quantity_entry.get()
    ag_practice = ag_practice_entry.get()

    # 2. 필수 입력값 확인
    if not all([area_code, farmer_id, fruit_type, variety, contact_info]):
        status_label_main_section.config(text="Please fill all required fields!", foreground="red")
        return

    # 3. 데이터 딕셔너리 생성 (DB 저장 및 QR 생성용)
    data = {
        "Area Code": area_code, "Farmer ID": farmer_id, "Contact Info": contact_info,
        "Fruit Type": fruit_type, "Variety": variety, "Harvest Date": harvest_date.strftime('%Y-%m-%d'),
        "Deliver Date": deliver_date.strftime('%Y-%m-%d'), "Storage Date": storage_date.strftime('%Y-%m-%d'),
        "Farming Method": farming_method, "Harvesting Number": harvesting_number,
        "Quantity": quantity, "Ag Practice": ag_practice
    }
    
    # --- [핵심] 무결성 보안 처리 구간 ---
    # 4. 입력된 데이터의 디지털 지문(Hash) 생성
    integrity_hash = calculate_hash(data)
    
    # 5. 생성된 해시를 '블록체인(시뮬레이션)' 파일에 영구 기록
    save_to_blockchain(integrity_hash, {"FarmerID": farmer_id, "Date": data["Harvest Date"]})

    # (검증 기능을 위해 현재 데이터를 메모리에 임시 저장)
    current_data_cache = data.copy()
    # ----------------------------------

    try:
        # 6. MariaDB 데이터베이스에 원본 데이터 저장
        db_connection = get_db_connection()
        cursor = db_connection.cursor()
        
        insert_query = """
        INSERT INTO qr (Lo, AC, FmID, FrT, Vt, Ct, HD, DD, Qt, Mt, HN, StD, Rp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        db_data = (
            "A00", area_code, farmer_id, fruit_type, variety, contact_info,
            harvest_date.strftime('%Y-%m-%d'), deliver_date.strftime('%Y-%m-%d'),
            quantity, farming_method, harvesting_number, 
            storage_date.strftime('%Y-%m-%d'), ag_practice
        )
        cursor.execute(insert_query, db_data)
        db_connection.commit()
        
        cursor.close()
        db_connection.close()
        
        # 7. 성공 메시지 업데이트 (해시값 일부를 보여주어 보안 처리됨을 명시)
        status_label_main_section.config(
            text=f"✅ 저장 및 보안처리 완료 (Hash: {integrity_hash[:10]}...)", 
            foreground="green"
        )
        
        # 8. QR 코드 이미지 생성 및 표시
        filename = generate_filename(area_code, farmer_id, harvest_date)
        generate_qr_code(data, filename)
        
        # (선택) 팝업창 띄우기
        messagebox.showinfo("성공", "데이터가 안전하게 저장되었습니다.\n(블록체인 무결성 등록 완료)")
        
    except mysql.connector.Error as err:
        status_label_main_section.config(text=f"Database error: {err}", foreground="red")

# --- [추가] 해킹 및 검증 시뮬레이션 함수 ---
def simulate_hack():
    """메모리에 있는 데이터를 강제로 조작"""
    if not current_data_cache:
        messagebox.showwarning("Warning", "No data saved yet to hack!")
        return
    
    # 데이터를 조작 (수량을 9999로 변경)
    current_data_cache["Quantity"] = "9999" 
    status_label_main_section.config(text="⚠️ Data Hacked! (Quantity -> 9999)", foreground="red")
    messagebox.showinfo("HACKED", "Data inside system has been tampered!\n(Quantity changed to 9999)")

def verify_data():
    """현재 데이터와 블록체인 기록을 대조하여 검증"""
    if not current_data_cache:
        messagebox.showwarning("Warning", "No data to verify!")
        return
    
    # 1. 현재 데이터의 해시 계산
    current_hash = calculate_hash(current_data_cache)
    
    # 2. 블록체인(파일)에서 최신 기록 로드
    stored_hash = None
    if os.path.exists(BLOCKCHAIN_FILE):
        with open(BLOCKCHAIN_FILE, "r", encoding="utf-8") as f:
            chain = json.load(f)
            if chain:
                stored_hash = chain[-1]["hash"] # 가장 최근 기록
    
    # 3. 비교
    if current_hash == stored_hash:
        status_label_main_section.config(text="✅ Verification Success: Data Integrity OK", foreground="blue")
        messagebox.showinfo("Verification", "✅ INTEGRITY VERIFIED\nData matches the blockchain record.")
    else:
        status_label_main_section.config(text="❌ Verification Failed: Data Modified!", foreground="red")
        messagebox.showerror("Verification", f"❌ ALERT: DATA TAMPERING DETECTED\n\nCurrent Hash: {current_hash[:10]}...\nStored Hash: {stored_hash[:10]}...")


# --- Validator Functions ---
def on_farmer_id_validate(char, entry_content): return char.isdigit() and len(entry_content) < 3
def validate_contact_info(char, current_text): return char.isdigit() or char == ""
def validate_numeric_input(char, current_text): return char.isdigit() or char == ""

def on_fruit_type_change(event):
    selected_fruit = fruit_type_combobox.get()
    variety_map = {
        "Apples": ["Hongro Apple", "Fuji Apple", "Gamhong Apple"],
        "Pears": ["Shingo Pear", "Wonhwang Pear", "Gamcheon Pear"],
        "Peaches": ["mibaegdo", "cheonjungdobaegdo", "yumyeongdo"],
        "Tangerines": ["eunju tangerine", "cheong tangerine", "mandarin"],
        "Melons": ["net melon", "baegja melon", "cham-oe"]
    }
    variety_combobox['values'] = variety_map.get(selected_fruit, [])

# --- GUI Setup ---
root = tk.Tk()
root.title("A00 Farm Data Collection (with Integrity Layer)")
root.geometry("1120x800")
root.resizable(True, True)

validate_numeric_cmd = root.register(validate_numeric_input)

notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

main_section_frame = ttk.Frame(notebook)
main_section_frame.pack(fill='both', expand=True)
notebook.add(main_section_frame, text="Main Section")

# Frame 배치 (기존과 동일)
frame1 = ttk.Frame(main_section_frame, borderwidth=2, relief="sunken", padding=10)
frame1.place(x=20, y=20, width=550, height=350)
frame2 = ttk.Frame(main_section_frame, borderwidth=2, relief="sunken", padding=10)
frame2.place(x=560, y=20, width=550, height=350)
frame3 = ttk.Frame(main_section_frame, borderwidth=2, relief="sunken", padding=10)
frame3.place(x=20, y=360, width=550, height=350)
frame4 = ttk.Frame(main_section_frame, borderwidth=2, relief="sunken", padding=10)
frame4.place(x=560, y=360, width=550, height=350)

# 타이틀
ttk.Label(frame1, text="FARM INFORMATION", font=("Helvetica", font_size, "bold"), anchor="center").place(x=0, y=0, width=530, height=30)
ttk.Label(frame2, text="HARVEST INFORMATION", font=("Helvetica", font_size, "bold"), anchor="center").place(x=0, y=0, width=530, height=30)
ttk.Label(frame3, text="CULTIVATION INFORMATION", font=("Helvetica", font_size, "bold"), anchor="center").place(x=0, y=0, width=530, height=30)
ttk.Label(frame4, text="RESULT & VERIFICATION", font=("Helvetica", font_size, "bold"), anchor="center").place(x=0, y=0, width=530, height=30)

# --- Frame 1~3 위젯들 (기존 코드와 동일하게 복원) ---
# Frame 1
ttk.Label(frame1, text="Farmer ID").place(x=10, y=40, width=130, height=30)
validate_id = root.register(on_farmer_id_validate)
farmer_id_entry = ttk.Entry(frame1, font=("Helvetica", font_size), width=uniform_combobox_width, justify='center', validate="key", validatecommand=(validate_id, "%S", "%P"))
farmer_id_entry.place(x=150, y=40, width=350, height=30)

ttk.Label(frame1, text="Area Code").place(x=10, y=80, width=130, height=30)
area_code_combobox = ttk.Combobox(frame1, values=zip_codes, state="readonly", font=("Helvetica", font_size), width=uniform_combobox_width, justify='center')
area_code_combobox.place(x=150, y=80, width=350, height=30)

ttk.Label(frame1, text="Contact Info").place(x=10, y=120, width=130, height=30)
validate_contact_info_cmd = root.register(validate_contact_info)
contact_info_entry = ttk.Entry(frame1, font=("Helvetica", font_size), justify='center', width=uniform_combobox_width, validate="key", validatecommand=(validate_contact_info_cmd, "%S", "%P"))
contact_info_entry.place(x=150, y=120, width=350, height=30)
contact_info_entry.bind("<KeyRelease>", lambda event: format_phone_number(contact_info_entry))

# Frame 2
ttk.Label(frame2, text="Harvest Date").place(x=10, y=40, width=130, height=30)
harvest_date_picker = DateEntry(frame2, font=("Helvetica", font_size), width=20, justify='center')
harvest_date_picker.place(x=150, y=40, width=350, height=30)

ttk.Label(frame2, text="Harvesting No.").place(x=10, y=80, width=130, height=30)
harvesting_number_entry = ttk.Entry(frame2, font=("Helvetica", font_size), justify='center', width=uniform_combobox_width, validate="key", validatecommand=(validate_numeric_cmd, "%S", "%P"))
harvesting_number_entry.place(x=150, y=80, width=350, height=30)

ttk.Label(frame2, text="Storage Date").place(x=10, y=120, width=130, height=30)
storage_date_picker = DateEntry(frame2, font=("Helvetica", font_size), width=20, justify='center')
storage_date_picker.place(x=150, y=120, width=350, height=30)

ttk.Label(frame2, text="Delivery Date").place(x=10, y=160, width=130, height=30)
deliver_date_picker = DateEntry(frame2, font=("Helvetica", font_size), width=20, justify='center')
deliver_date_picker.place(x=150, y=160, width=350, height=30)

ttk.Label(frame2, text="Quantity(box)").place(x=10, y=200, width=130, height=30)
quantity_entry = ttk.Entry(frame2, font=("Helvetica", font_size), justify='center', width=uniform_combobox_width, validate="key", validatecommand=(validate_numeric_cmd, "%S", "%P"))
quantity_entry.place(x=150, y=200, width=350, height=30)

# Frame 3
ttk.Label(frame3, text="Fruit Type").place(x=10, y=40, width=130, height=30)
fruit_type_combobox = ttk.Combobox(frame3, values=fruit_types, state="readonly", font=("Helvetica", font_size), width=uniform_combobox_width, justify='center')
fruit_type_combobox.place(x=150, y=40, width=350, height=30)
fruit_type_combobox.bind("<<ComboboxSelected>>", on_fruit_type_change)

ttk.Label(frame3, text="Variety").place(x=10, y=80, width=130, height=30)
variety_combobox = ttk.Combobox(frame3, state="readonly", font=("Helvetica", font_size), width=uniform_combobox_width, justify='center')
variety_combobox.place(x=150, y=80, width=350, height=30)

ttk.Label(frame3, text="Farming Method").place(x=10, y=120, width=130, height=30)
farming_method_combobox = ttk.Combobox(frame3, values=farming_methods, state="readonly", font=("Helvetica", font_size), width=uniform_combobox_width, justify='center')
farming_method_combobox.place(x=150, y=120, width=350, height=30)

ttk.Label(frame3, text="Ag Practice").place(x=10, y=160, width=130, height=30)
ag_practice_entry = ttk.Entry(frame3, font=("Helvetica", font_size), justify='center', width=uniform_combobox_width)
ag_practice_entry.place(x=150, y=160, width=350, height=30)

# --- [수정] Frame 4 (Result & Verification) ---
qr_label = ttk.Label(frame4)
# QR 코드도 중앙 정렬을 확실하게 하려면 아래와 같이 바꾸셔도 좋습니다 (선택 사항)
qr_label.place(relx=0.5, y=30, width=150, height=150, anchor="n")

# [수정] Save 버튼 중앙 정렬
# relx=0.5: 부모 프레임의 가로 50% 지점에 배치
# anchor="n": 버튼의 '북쪽(상단) 가운데'를 기준점으로 삼음 (즉, 정중앙 정렬됨)
save_button = ttk.Button(frame4, text="Save (DB + Hash)", command=save_all_formats)
save_button.place(relx=0.5, y=200, width=250, height=40, anchor="n")

# [추가] Hack 버튼
#hack_button = ttk.Button(frame4, text="😈 Hack Data", command=simulate_hack)
#hack_button.place(x=300, y=200, width=200, height=40)

# [추가] Verify 버튼
#verify_button = ttk.Button(frame4, text="🔍 Verify Integrity", command=verify_data)
#verify_button.place(x=50, y=250, width=450, height=40)

# 상태 메시지도 중앙 정렬 (기존 x=50, width=450도 중앙이긴 하지만, relx가 더 확실합니다)
status_label_main_section = ttk.Label(frame4, text="", anchor="center")
status_label_main_section.place(relx=0.5, y=300, width=450, height=30, anchor="n")

# XML Path Label (기존 유지)
def display_xml_path(file_path):
    xml_path_label = ttk.Label(frame4, text=f"Saved XML: {file_path}", font=("Helvetica", 10), foreground="blue", cursor="hand2")
    xml_path_label.place(x=100, y=190, width=350, height=30)
    xml_path_label.bind("<Button-1>", lambda e: os.startfile(os.path.abspath(file_path)))

root.mainloop()