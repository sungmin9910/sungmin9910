import airsim
import time
import os

def connect_to_airsim():
    """
    AirSim 시뮬레이터와의 연결을 테스트하는 기본 스크립트
    """
    # 자동차 클라이언트 생성
    client = airsim.CarClient()
    
    print("Connecting to AirSim...")
    client.confirmConnection()
    
    # API 제어권 획득
    client.enableApiControl(True)
    print("API Control Enabled")
    
    # 차량 상태 가져오기
    car_state = client.getCarState()
    print(f"Speed: {car_state.speed} m/s")
    print(f"Gear: {car_state.gear}")
    
    # 기본 제어 객체 생성
    car_controls = airsim.CarControls()
    
    try:
        print("Driving forward for 3 seconds...")
        car_controls.throttle = 0.5
        car_controls.steering = 0
        client.setCarControls(car_controls)
        
        time.sleep(3)
        
        # 멈춤
        print("Braking...")
        car_controls.throttle = 0
        car_controls.brake = 1
        client.setCarControls(car_controls)
        
    finally:
        # 제어권 반납
        client.enableApiControl(False)
        print("API Control Disabled")

if __name__ == "__main__":
    connect_to_airsim()
