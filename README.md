# Tidy Python

## 🚀 빠른 시작

### 사전 요구사항

- Docker

### Docker를 사용한 실행

**처음 실행 시 (빌드 포함)**
```bash
docker-compose up -d --build
```

**이후 실행 시**
```bash
docker-compose up -d
```

**서비스 확인**
- API 문서: http://localhost:8000/docs
- 서비스 상태: http://localhost:8000

## 🐳 Docker 명령어

**서비스 시작**
```bash
docker-compose up -d
```

**서비스 중지**
```bash
docker-compose down
```

**서비스 재빌드 및 시작**
```bash
docker-compose up -d --build
```

**로그 확인**
```bash
docker-compose logs -f
```

## 📁 볼륨 마운트

- `../temp:/app/temp`: 임시 파일 저장소
- `../output:/app/output`: 변환된 이미지 출력 디렉토리



