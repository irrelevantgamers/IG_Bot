import sys
import mariadb

from Modules.config import DB_name, DB_port, DB_host, DB_pass, DB_user


def connect_mariadb():
    global mariaCon
    global mariaCur
    try:
        mariaCon = mariadb.connect(
            user=DB_user,
            password=DB_pass,
            host=DB_host,
            port=DB_port,
            database=DB_name

        )
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)
    print("Connected to MariaDB Platform")
    mariaCur = mariaCon.cursor()
    mariaCur.execute("SET NAMES utf8mb4;")


def close_mariaDB():
    mariaCur.close()
    mariaCon.close()
