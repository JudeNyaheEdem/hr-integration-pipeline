import logging
from config import CONFIG


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(messages)s",
    handlers=[
        logging.FileHandler(CONFIG["log_dir"] /
                            "pipeline.log", encoding="utf-8"),
        logging.StreamHandler()
    ])


logger = logging.getLogger(__name__)
