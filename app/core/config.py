import os
from pathlib import Path
from typing import Iterable


class Settings:
    """
    애플리케이션 전역 설정.
    모든 경로는 환경변수로 오버라이드할 수 있고, 기본값은 프로젝트 루트를 기준으로 삼는다.
    """

    def __init__(self) -> None:
        self.base_dir = Path(
            os.getenv("BASE_DIR", Path(__file__).resolve().parents[2])
        )
        self.temp_dir = Path(
            os.getenv("TEMP_DIR", self.base_dir / "temp")
        )
        self.output_dir = Path(
            os.getenv("OUTPUT_DIR", self.base_dir / "output")
        )
        self.font_dir = Path(
            os.getenv("FONT_DIR", "/usr/share/fonts/truetype/ppt-embedded")
        )
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")

        self._ensure_directories(
            directory for directory in (self.temp_dir, self.output_dir, self.font_dir)
        )

    @staticmethod
    def _ensure_directories(directories: Iterable[Path]) -> None:
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                # Docker 이미지 빌드 단계 등에서 권한이 없는 경로일 수 있으므로 무시
                pass


settings = Settings()
