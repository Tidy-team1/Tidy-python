# Tidy Python

## 🚀 실행 방법
### 사전 요구사항
- Docker

### Docker를 사용한 실행

**빌드(로컬)**
```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml build
```

**이후 백그라운드 실행 시**
```bash
docker-compose up -d
```

**빌드, 실행 한번에**
```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up --build
```

**서비스 중지**
```bash
docker-compose down
```

**로그 확인**
```bash
docker logs -f tidy-python
```

## 📁 프로젝트 구조
```bash
tidy-python/
│
├── docker-compose.yml            # 공통 설정
├── docker-compose.local.yml      # 로컬 개발용 override
├── docker-compose.dev.yml        # DEV 서버용 override
│
├── app/                          # FastAPI 소스코드
├── Dockerfile
└── README.md
```
