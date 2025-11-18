import logging

logger = logging.getLogger("tidy-python-service")

def setup_logger():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(asctime)s - %(message)s",
    )
