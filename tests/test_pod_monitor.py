import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# console_handler = logging.StreamHandler()
# console_handler.setLevel(logging.INFO)

# formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
# console_handler.setFormatter(formatter)

# logger.addHandler(console_handler)

# LOG = Logger.get_logger(__name__)


def test_u():
    logger.info("testing>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")


if __name__ == "__main__":
    test_u()
