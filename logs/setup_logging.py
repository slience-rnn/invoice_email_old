from pathlib import Path
import logging
import logging.config

def setup_logging():
    BATH_PATH = Path(__file__).resolve().parent.parent
    config_path = Path.joinpath(BATH_PATH,'logs','logging.conf')
    Path("logs").mkdir(exist_ok=True)
    logging.config.fileConfig(config_path,disable_existing_loggers=False)
