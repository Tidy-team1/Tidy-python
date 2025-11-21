FROM python:3.10-slim

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    libreoffice \
    fontconfig \
    unzip \
    fonts-noto-cjk \
    fonts-nanum \
    && apt-get clean

# 타임존 설정 (여기에 넣으면 됨)
RUN ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime && \
    echo "Asia/Seoul" > /etc/timezone

# PPT에서 추출한 폰트를 저장할 디렉토리 미리 생성
RUN mkdir -p /usr/share/fonts/truetype/ppt-embedded

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
