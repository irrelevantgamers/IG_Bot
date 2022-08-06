def connect_mariadb():
    try:
        global mariaCon
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
    global mariaCur
    mariaCur = mariaCon.cursor()

def close_mariaDB():
    mariaCur.close()
    mariaCon.close()