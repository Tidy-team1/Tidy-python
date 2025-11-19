# Tidy Python

## 🚀 빠른 시작

### 사전 요구사항

- Docker 설치
- 배포 전이라 공유 파일 디렉토리(output)의 위치를 야매로 정했습니다. 아래처럼 백, 프론트, 파이썬이 같은 디렉토리에 위치하게 해주세요.
```
root/
├── tidy/                 # 백엔드
├── Tidy-frontend/               # 프론트
├── tidy-python/            # 파이썬
├── temp/    # 임시 파일 저장 디렉토리
└── output/      # 출력물 저장 디렉토리
```

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

