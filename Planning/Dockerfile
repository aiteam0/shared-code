# Python 3.12 slim 이미지 사용
FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    fonts-dejavu-core \
    fonts-liberation \
    fontconfig \
    && fc-cache -fv \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 코드 복사
# .dockerignore에 의해 불필요한 파일들은 제외됨
COPY . .

# 로그 디렉토리 생성
RUN mkdir -p logs

# Streamlit 설정 디렉토리 확인
RUN mkdir -p .streamlit

# 환경 변수 설정
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_SERVER_ENABLE_STATIC_SERVING=true
ENV STREAMLIT_SERVER_ENABLE_CORS=false
ENV STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# 포트 노출
EXPOSE 8501

# 헬스체크 추가
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Streamlit 애플리케이션 실행
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"] 