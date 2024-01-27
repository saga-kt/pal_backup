from lib.server import Server
from lib.gdrive import GDrive
from rcon.source import proto
import configparser
import time, datetime
import os
import psutil
import subprocess
import logging


for logger_name in logging.Logger.manager.loggerDict.keys():
    logging.getLogger(logger_name).setLevel(logging.FATAL)
    logging.getLogger(logger_name).propagate = False


if __name__ == "__main__":
    # ログ設定
    logFormatter = logging.Formatter("[%(asctime)s][%(levelname)-5.5s] %(message)s", datefmt="%Y/%m/%d %H:%M:%S")
    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)

    os.makedirs("log", exist_ok=True)
    fileHandler = logging.FileHandler(f"log/app_{datetime.datetime.now().strftime('%Y%m%d')}.log", encoding="utf-8")
    fileHandler.setLevel(logging.INFO)
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setLevel(logging.DEBUG)
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)

    # サーバ情報の読み込み
    config = configparser.ConfigParser()
    config.read("config.ini")

    host = config["DEFAULT"]["host"]
    port = int(config["DEFAULT"]["port"])
    password = config["DEFAULT"]["password"]
    pal_dir = config["DEFAULT"]["pal_dir"]
    data_dir = os.path.join(pal_dir, "Pal", "Saved")
    pal_process_name = "PalServer.exe"
    gdrive_flg = config["DEFAULT"].get("upload_gdrive", fallback="False") == "True"
    
    if not os.path.exists(pal_dir):
        logging.debug(f"パルサーバーのフォルダーが存在しません。{pal_dir}")
        exit(1)

    # バックアップファイルをアップロードするGドライブの設定
    if gdrive_flg:
        gdrive = GDrive()

    # サーバーの起動
    server_running_flg = False
    for attempt in range(3):
        if pal_process_name in [p.name() for p in psutil.process_iter()]:
            server_running_flg = True
            break
        else:
            logging.debug("パルサーバー起動中。")
            subprocess.Popen([os.path.join(pal_dir, pal_process_name)])
            time.sleep(15)

    if not server_running_flg:
        logging.error("パルサーバーが起動できません。")
        time.sleep(15)
        exit(1)

    # バックアップ実行
    sleep_time_sec = 60
    last_backup_dt = None
    last_backup_file = None
    last_cleanup_dt = None
    keep_days = 7  # 一週間ファイルを保持
    while True:
        try:
            with Server(host, port, password, data_dir) as server:
                while True:
                    player_cnt = server.count_players()
                    backup_flg = last_backup_dt is None or datetime.datetime.now() >= last_backup_dt + datetime.timedelta(hours=1)
                    cleanup_flg = last_cleanup_dt is None or datetime.datetime.now() >= last_backup_dt + datetime.timedelta(days=1)
                    if player_cnt <= 0 and backup_flg:
                        logging.debug("バックアップ生成中。")
                        try:
                            # ダンプ生成
                            last_backup_file = server.backup_data()
                            # Gドラに退避
                            if gdrive_flg:
                                try:
                                    gdrive.upload_backup_file(os.path.join(server.backup_dir, last_backup_file))
                                except Exception as e:
                                    logging.warn(f"Gドライブにアップロードできません。{e}")
                            last_backup_dt = datetime.datetime.now()
                            logging.info(f"バックアップ完了。{last_backup_file}")

                            if cleanup_flg:
                                # ローカルバックアップの削除
                                server.clean_backup_data(keep_days=keep_days)
                                # Gドライブのバックアップ削除
                                if gdrive_flg:
                                    try:
                                        del_count = gdrive.clean_backup_data(keep_days=keep_days)
                                        logging.debug(f"Gドライブの{del_count}件のバックアップが削除されました。")
                                    except:
                                        logging.warn(f"Gドライブのファイル削除が失敗しました。{e}")
                                last_cleanup_dt = datetime.datetime.now()
                        except Exception as e:
                            logging.error(f"バックアップ中にエラーが発生しました。 {e}")
                    elif backup_flg:
                        logging.debug(f"バックアップ保留中・接続ユーザー数: {player_cnt}")
                    else:
                        logging.debug(f"接続ユーザー数: {player_cnt}")
                    time.sleep(sleep_time_sec)
        except ConnectionAbortedError as e:
            pass
        except Exception as e:
            logging.error(e)


