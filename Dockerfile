FROM python:3.10-slim

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    libreoffice \
    poppler-utils \
    fontconfig \
    unzip \
    fonts-noto-cjk \
    fonts-nanum \
    && apt-get clean

# PPT에서 추출한 폰트를 저장할 디렉토리 미리 생성
RUN mkdir -p /usr/share/fonts/truetype/ppt-embedded

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
