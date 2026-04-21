import pyrealsense2 as rs
import numpy as np
import cv2
from ultralytics import YOLO

def main():
    # 1. RealSense 파이프라인 설정
    pipeline = rs.pipeline()
    config = rs.config()

    # 컬러와 깊이 스트림 활성화 (640x480, 30fps)
    config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
    config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)

    # 2. 파이프라인 시작
    try:
        profile = pipeline.start(config)
    except Exception as e:
        print(f"카메라를 시작할 수 없습니다: {e}")
        return

    # 거리 척도(Depth scale)와 카메라 내부 파라미터(Intrinsics) 가져오기
    depth_sensor = profile.get_device().first_depth_sensor()
    depth_scale = depth_sensor.get_depth_scale()
    intrinsics = profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()

    # 정렬 객체 생성 (깊이 영상을 컬러 영상 기준에 맞춤)
    align_to = rs.stream.color
    align = rs.align(align_to)

    # 3. YOLOv8 모델 로드 (가장 가벼운 Nano 모델 사용)
    print("AI 모델(YOLOv8n) 로딩 중...")
    model = YOLO('yolov8n.pt') 

    try:
        print("--- [SpatialTwin-Orin] 실시간 3D 좌표 추출 시작 ---")
        print("종료하려면 Ctrl+C를 누르세요.")
        
        while True:
            # 프레임 대기
            frames = pipeline.wait_for_frames()
            aligned_frames = align.process(frames)
            
            depth_frame = aligned_frames.get_depth_frame()
            color_frame = aligned_frames.get_color_frame()
            
            if not depth_frame or not color_frame:
                continue
            
            # 이미지를 numpy 배열로 변환
            color_image = np.asanyarray(color_frame.get_data())
            
            # YOLOv8 추론 시작 (GPU 가속 활용)
            results = model(color_image, stream=True, verbose=False)
            
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    # 바운딩 박스 정보
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = box.conf[0].item()
                    cls = int(box.cls[0].item())
                    label = model.names[cls]
                    
                    # 물체의 중심점 계산
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    
                    # 중심점의 깊이 값(m) 가져오기
                    dist = depth_frame.get_distance(cx, cy)
                    
                    if dist > 0:
                        # 2D 픽셀 좌표(cx, cy)를 실제 3D 좌표(X, Y, Z)로 변환
                        point = rs.rs2_deproject_pixel_to_point(intrinsics, [cx, cy], dist)
                        # point[0]: X(좌우), point[1]: Y(상하), point[2]: Z(전후/거리)
                        
                        # 터미널에 실시간 출력
                        print(f"Object: {label:10} | Dist: {dist:.2f}m | 3D(m): X={point[0]:.2f}, Y={point[1]:.2f}, Z={point[2]:.2f} | Conf: {conf:.2f}")

    except KeyboardInterrupt:
        print("\n사용자에 의해 종료되었습니다.")
    finally:
        pipeline.stop()

if __name__ == "__main__":
    main()
