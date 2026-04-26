import airsim
import numpy as np
import time

def parse_lidarData(data):
    if len(data.point_cloud) < 3:
        return None
    points = np.array(data.point_cloud, dtype=np.float32)
    points = np.reshape(points, (int(points.shape[0]/3), 3))
    return points

def main():
    client = airsim.CarClient()
    client.confirmConnection()
    client.enableApiControl(True)
    
    print("Intelligent Steering System Started...")

    car_controls = airsim.CarControls()

    while True:
        # 1. LiDAR 데이터 가져오기 (설정하신 이름 확인)
        lidar_data = client.getLidarData(lidar_name="LidarCustom")
        points = parse_lidarData(lidar_data)
        
        if points is None:
            time.sleep(0.1)
            continue

        # 2. 영역별 장애물 감지
        # 전방 (정면 5m, 폭 2m)
        front_zone = points[(points[:, 0] > 0) & (points[:, 0] < 6) & (np.abs(points[:, 1]) < 1.5)]
        
        # 왼쪽 영역 (각도상 왼쪽)
        left_zone = points[(points[:, 0] > 0) & (points[:, 0] < 8) & (points[:, 1] < -1.5) & (points[:, 1] > -5)]
        
        # 오른쪽 영역 (각도상 오른쪽)
        right_zone = points[(points[:, 0] > 0) & (points[:, 0] < 8) & (points[:, 1] > 1.5) & (points[:, 1] < 5)]

        if len(front_zone) > 5:
            # 장애물 발견! 어디가 더 비어있는지 판단
            print(f"Obstacle in front! Scanning sides...")
            
            # 왼쪽과 오른쪽의 장애물 밀도 비교
            if len(left_zone) < len(right_zone):
                print("Turning LEFT to avoid")
                car_controls.steering = -0.5 # 왼쪽으로 핸들 꺾기
            else:
                print("Turning RIGHT to avoid")
                car_controls.steering = 0.5  # 오른쪽으로 핸들 꺾기
            
            # 회피 중에는 속도 줄이기
            car_controls.throttle = 0.2
        else:
            # 전방이 깨끗하면 다시 정면 주행
            print("Path Clear - Cruising")
            car_controls.steering = 0
            car_controls.throttle = 0.5
            
        client.setCarControls(car_controls)
        time.sleep(0.05)

    client.enableApiControl(False)

if __name__ == "__main__":
    main()
