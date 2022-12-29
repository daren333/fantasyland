import argparse

from sqlalchemy import create_engine

from python_app import config
from python_app.writer import init_mysql_db


def main(args):
    engine = create_engine(
        "mysql+pymysql://" + config.mysql_user + ":" + config.mysql_pw + "@" + config.mysql_host)
    init_mysql_db(engine)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-t", "--test_mode",
                        action="store_true",
                        help="enable test mode")
    args = parser.parse_args()
    main(args)