import pandas as pd
from sklearn.ensemble import RandomForestClassifier

# 1. 동기화된 기계 센서 데이터 (가상 데이터: 온도, 습도, 진동수)
data = {
    'temperature': [35, 40, 55, 75, 80, 95, 105],
    'humidity': [40, 45, 50, 60, 65, 80, 90],
    'vibration': [1.2, 1.5, 1.8, 4.5, 5.0, 7.2, 8.5],
    'state': [0, 0, 0, 1, 1, 1, 1] # 0: 정상 상태, 1: 비정상(점검) 상태
}
# 데이터를 표(DataFrame) 형태로 변환
df = pd.DataFrame(data)

# 2. 머신러닝 모델 준비 (다수의 결정 트리를 사용하는 랜덤 포레스트 알고리즘)
model = RandomForestClassifier(random_state=42)

# 3. 모델 학습 (데이터의 패턴을 스스로 파악하도록 지시)
X = df[['temperature', 'humidity', 'vibration']] # 원인(센서 값)
y = df['state'] # 결과(상태)
model.fit(X, y)

# 4. 실시간 데이터 유입 가정 및 현재 상태 분류 (예: 온도 82도, 습도 70%, 진동 6.0)
current_sensor_data = [input("온도를 입력하세요: "), input("습도를 입력하세요: "), input("진동을 입력하세요: ")]
current_sensor_data = [[float(current_sensor_data[0]), float(current_sensor_data[1]), float(current_sensor_data[2])]]   
classification_result = model.predict(current_sensor_data)

# 5. 결과 출력
print("--- 실시간 상태 분류 보고서 ---")
if classification_result[0] == 1:
    print("분류 결과: 비정상 상태 감지. 즉각적인 상태 확인이 필요합니다.")
else:
    print("분류 결과: 정상 상태입니다.")