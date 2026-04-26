import airsim
import numpy as np
import time

def parse_lidarData(data):
    # LiDAR 데이터를 (N, 3) 형태의 numpy 배열로 변환
    points = np.array(data.point_cloud, dtype=np.float32)
    points = np.reshape(points, (int(points.shape[0]/3), 3))
    return points

def main():
    client = airsim.CarClient()
    client.confirmConnection()
    client.enableApiControl(True)
    
    print("LiDAR Avoidance System Started...")

    car_controls = airsim.CarControls()

    while True:
        # 1. LiDAR 데이터 가져오기
        lidar_data = client.getLidarData()
        
        if len(lidar_data.point_cloud) < 3:
            print("No LiDAR data received. Check your settings.json")
            time.sleep(1)
            continue

        # 2. 포인트 클라우드 파싱
        points = parse_lidarData(lidar_data)
        
        # 3. 전방 장애물 감지 로직
        # 차량 기준 X축(정면) 거리가 10m 이내이고, 
        # Y축(좌우) 폭이 2m 이내인 포인트들이 있는지 확인
        front_points = points[(points[:, 0] > 0) & (points[:, 0] < 10) & (np.abs(points[:, 1]) < 2.0)]
        
        if len(front_points) > 5: # 일정 개수 이상의 포인트가 전방에 있으면 장애물로 간주
            min_dist = np.min(front_points[:, 0])
            print(f"⚠️ OBSTACLE DETECTED! Distance: {min_dist:.2f}m - BRAKING")
            
            # 급브레이크
            car_controls.throttle = 0
            car_controls.brake = 1
        else:
            # 장애물이 없으면 전진
            print("Safe - Driving Forward")
            car_controls.throttle = 0.4
            car_controls.brake = 0
            
        client.setCarControls(car_controls)
        time.sleep(0.1)

    client.enableApiControl(False)

if __name__ == "__main__":
    main()
