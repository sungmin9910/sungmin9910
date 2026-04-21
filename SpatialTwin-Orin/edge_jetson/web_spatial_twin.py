import pyrealsense2 as rs
import numpy as np
import cv2
from ultralytics import YOLO
from flask import Flask, Response
import threading
import time

app = Flask(__name__)

# 전역 변수 및 락 설정
output_frame = None
lock = threading.Lock()
active_detections = []
PERSISTENCE_LIMIT = 5 # YOLO11s TensorRT는 정확도가 높아 잔상을 줄여도 안정적임

def start_sensing():
    global output_frame, active_detections
    
    # 1. RealSense 설정
    pipeline = rs.pipeline()
    config = rs.config()
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
    
    try:
        profile = pipeline.start(config)
    except Exception as e:
        print(f"카메라 시작 실패: {e}")
        return

    intrinsics = profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()
    align = rs.align(rs.stream.color)

    # 2. 최적화된 YOLO11s TensorRT 엔진 로드
    # 주의: 실행 전 'yolo11s.engine' 파일이 같은 폴더에 있어야 합니다.
    print("--- 🚀 SpatialTwin YOLO11s-TRT Engine Loading... ---")
    try:
        model = YOLO('yolo11s.engine', task='detect') 
    except:
        print("엔진 파일을 찾을 수 없습니다. .pt 모델로 대체합니다.")
        model = YOLO('yolo11s.pt')

    try:
        while True:
            frames = pipeline.wait_for_frames()
            aligned_frames = align.process(frames)
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()
            
            if not depth_frame or not color_frame:
                continue
            
            color_image = np.asanyarray(color_frame.get_data()).copy().astype(np.uint8)
            
            # AI 추론 (TensorRT 가속)
            results = model(color_image, conf=0.35, verbose=False)
            
            current_frame_detections = []
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    label = r.names[int(box.cls[0])].upper()
                    
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    dist = depth_frame.get_distance(cx, cy)
                    
                    point = None
                    if dist > 0:
                        point = rs.rs2_deproject_pixel_to_point(intrinsics, [cx, cy], dist)
                    
                    current_frame_detections.append([x1, y1, x2, y2, label, dist, point, PERSISTENCE_LIMIT])

            # 잔상 필터링 (Flicker 방지)
            for obj in active_detections:
                obj[7] -= 1 
            
            if len(current_frame_detections) > 0:
                active_detections = current_frame_detections
            else:
                active_detections = [obj for obj in active_detections if obj[7] > 0]

            # 3D 가시화 그리기
            for x1, y1, x2, y2, label, dist, point, count in active_detections:
                cv2.rectangle(color_image, (x1, y1), (x2, y2), (0, 255, 0), 1)
                text = f"{label} {dist:.2f}m" if dist > 0 else label
                text_y = y1 - 8 if y1 > 25 else y1 + 18
                (t_w, t_h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)
                cv2.rectangle(color_image, (x1, text_y - t_h - 4), (x1 + t_w + 2, text_y + 2), (0, 255, 0), -1)
                cv2.putText(color_image, text, (x1 + 1, text_y - 1), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)

            # 시스템 대시보드 오버레이
            cv2.putText(color_image, f"JETSON HYPER-VISION | {len(active_detections)} OBJ", (20, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

            with lock:
                output_frame = color_image
                
    finally:
        pipeline.stop()

def generate():
    global output_frame, lock
    while True:
        with lock:
            if output_frame is None:
                continue
            flag, encodedImage = cv2.imencode(".jpg", output_frame)
            if not flag:
                continue
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

@app.route("/")
def index():
    return """
    <html>
        <head>
            <title>SpatialTwin Pro Dashboard</title>
            <style>
                body { background-color: #000; color: #00e676; font-family: 'Courier New', monospace; text-align: center; margin: 0; padding: 20px; }
                .container { display: inline-block; padding: 15px; border: 1px solid #00e676; background: #050505; border-radius: 10px; box-shadow: 0 0 20px rgba(0,255,118,0.2); }
                img { width: 90vw; max-width: 1100px; height: auto; border: 1px solid #333; border-radius: 5px; }
                .info { margin-top: 15px; font-size: 0.8em; opacity: 0.7; }
                .header { font-size: 1.5em; margin-bottom: 10px; font-weight: bold; letter-spacing: 2px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">>>> SPATIAL_TWIN_HYPER_VISION_V1.5</div>
                <img src="/video_feed">
                <div class="info">AI CORE: YOLO11s-TENSORRT | SENSOR: RealSense D455 | HOST: Jetson Orin Nano</div>
            </div>
        </body>
    </html>
    """

@app.route("/video_feed")
def video_feed():
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    t = threading.Thread(target=start_sensing)
    t.start()
    app.run(host="0.0.0.0", port=5000)
