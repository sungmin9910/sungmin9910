# Dockerfile

# 1. 베이스 이미지 선택 (파이썬 3.9 버전)
FROM python:3.9-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. 필요한 라이브러리 설치를 위해 requirements.txt 파일 먼저 복사
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 나머지 프로젝트 파일 전체 복사
COPY . .

# 5. Gunicorn 설치 (실 서비스용 웹 서버)
RUN pip install gunicorn

# 6. 컨테이너가 시작될 때 실행할 명령어
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app2:app"]