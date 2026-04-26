import airsim
import cv2
import numpy as np
import time

def main():
    # AirSim 연결
    client = airsim.CarClient()
    client.confirmConnection()
    client.enableApiControl(True)

    print("Camera Viewer Started. Press 'q' to quit.")

    while True:
        # 1. AirSim으로부터 이미지 가져오기 (전방 카메라, RGB 이미지)
        # '0'은 전방 카메라, ImageType.Scene은 일반 컬러 화면을 의미합니다.
        responses = client.simGetImages([
            airsim.ImageRequest("0", airsim.ImageType.Scene, False, False)
        ])
        
        response = responses[0]

        # 2. 이미지 데이터를 numpy 배열로 변환
        img1d = np.frombuffer(response.image_data_uint8, dtype=np.uint8)
        
        # 3. 데이터가 비어있지 않은지 확인 후 리쉐이프 (B, G, R, A 구조)
        if img1d.size > 0:
            img_rgba = img1d.reshape(response.height, response.width, 3)
            
            # 4. 화면에 출력 (OpenCV는 BGR 순서를 사용하므로 필요시 변환)
            # 여기서는 AirSim이 제공하는 기본 이미지를 그대로 출력합니다.
            cv2.imshow("AirSim Front Camera", img_rgba)

        # 5. 주행 조종 (간단한 직진 테스트)
        car_controls = airsim.CarControls()
        car_controls.throttle = 0.3
        client.setCarControls(car_controls)

        # 'q' 키를 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 종료 시 제어권 반납 및 창 닫기
    client.enableApiControl(False)
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
