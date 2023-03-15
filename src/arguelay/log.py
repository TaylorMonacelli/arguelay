import logging
import sys


def setup_logging():
    logging.basicConfig(
        level=logging.DEBUG,
        format="{%(filename)s:%(lineno)d} %(levelname)s - %(message)s",
        handlers=[
            #        logging.FileHandler(f"{pathlib.Path(__file__).stem}.log"),
            logging.StreamHandler(sys.stdout)
        ],
    )
