from lib.server import Server
from lib.gdrive import GDrive
from lib.discordmanager import DiscordManager
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


def start_palserver(attempt_num=3):
    server_running_flg = False
    for attempt in range(attempt_num):
        if pal_process_name in [p.name() for p in psutil.process_iter()]:
            server_running_flg = True
            break
        else:
            logging.debug(f"パルサーバー起動中。{attempt+1}/{attempt_num}")
            subprocess.Popen([os.path.join(pal_dir, pal_process_name)])
            time.sleep(15)

    if not server_running_flg:
        logging.error("パルサーバーが起動できません。")
        time.sleep(15)
    return server_running_flg


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
    # RCONの接続情報
    host = config["DEFAULT"]["host"]
    port = int(config["DEFAULT"]["port"])
    password = config["DEFAULT"]["password"]
    # パルサーバの情報
    pal_port = 8211
    pal_dir = config["DEFAULT"]["pal_dir"]
    if not os.path.exists(pal_dir):
        logging.debug(f"パルサーバーのフォルダーが存在しません。{pal_dir}")
        exit(1)
    data_dir = os.path.join(pal_dir, "Pal", "Saved")
    pal_process_name = "PalServer.exe"
    # バックアップ設定
    keep_days = int(config["DEFAULT"].get("backup_keep_days", fallback=7))
    # Gドライブのバックアップフラグ
    gdrive_flg = config["DEFAULT"].get("upload_gdrive", fallback="False") == "True"
    # バックアップファイルをアップロードするGドライブの設定
    if gdrive_flg:
        gdrive = GDrive()
    # Discordの通知
    discord_webhook_url = config["DEFAULT"].get("discord_webhook", fallback="")
    if discord_webhook_url:
        discord = DiscordManager(discord_webhook_url)
    else:
        discord = None

    # TODO: リファクタリングしたい
    sleep_time_sec = 60
    last_backup_dt = None
    last_backup_file = None
    last_cleanup_dt = None
    while True:
        # サーバーの起動
        server_running_flg = False
        try:
            server_running_flg = start_palserver()
        except:
            pass
        if not server_running_flg:
            if discord:
                port_process_name = ""
                for fd, family, type, laddr, raddr, status, pid in psutil.net_connections():
                    if laddr[1] == pal_port:
                        # 起動できていれば"PalServer-Win64-Test-Cmd.exe"が見つかるはず
                        port_process_name = psutil.Process(pid).name()
                        break
                try:
                    discord.send_message("パルサーバが起動できません。プロセス:{port_process_name} 使用ポート:{pal_port} ")
                except:
                    pass
            time.sleep(60 * 60)
            continue

        # バックアップ実行
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
                                # 古いローカルバックアップの削除
                                server.clean_backup_data(keep_days=keep_days)
                                # 古いGドライブバックアップの削除
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
        time.sleep(15)


