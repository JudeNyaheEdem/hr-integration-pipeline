import logging
from src.config import CONFIG


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(CONFIG["log_dir"] /
                            "pipeline.log", encoding="utf-8"),
        logging.StreamHandler()
    ])


logger = logging.getLogger(__name__)
