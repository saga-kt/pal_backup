from rcon.source import Client
from rcon.source.proto import Packet
import os
import time, datetime
import zipfile
from pathlib import Path


class Server(Client):
    """
    パル鯖操作
    """
    def __init__(self, host, port, password, data_dir, backup_dir=os.path.join(os.path.abspath(""), "backup"), backup_dt_format="%Y%m%d_%H%M%S"):
        super().__init__(str(host), int(port), passwd=password)
        self.data_dir = data_dir
        self.backup_dir = backup_dir
        self.backup_dt_format = backup_dt_format
        self.backup_file_prefix = "pal_backup_"

        # サーバーデータの確認
        if not os.path.exists(self.data_dir):
            raise Exception(f"データフォルダが存在しません。{self.data_dir}")

        # バックアップフォルダの作成
        os.makedirs(self.backup_dir, exist_ok=True)
        pass
    
    def __enter__(self):
        super().__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)
        self.close()

    def show_players(self):
        players = [p for p in self.run("showplayers").replace("name,playeruid,steamid\n", "").split("/n") if p != ""]
        return players
    
    def count_players(self):
        return len(self.show_players())
    
    def save_data(self):
        return self.run("save")

    def backup_data(self):
        self.save_data()
        time.sleep(5)
        backup_filename = f"pal_backup_{datetime.datetime.now().strftime(self.backup_dt_format)}.zip"
        if os.path.exists(self.data_dir):
            # バックアップ作成
            backup_file = zipfile.ZipFile(os.path.join(self.backup_dir, backup_filename), "w", zipfile.ZIP_DEFLATED)
            backup_dir = Path(self.data_dir)
            for entry in backup_dir.rglob("*"):
                backup_file.write(entry, entry.relative_to(backup_dir))
            backup_file.close()
            return backup_filename
        else:
            raise(f"データフォルダが存在しません。{self.data_dir}")

    def clean_backup_data(self, keep_days=7):
        # 古いバックアップを削除
        if os.path.exists(self.backup_dir):
            clean_dt = (datetime.datetime.now() - datetime.timedelta(days=keep_days)).strftime("%Y%m%d")
            clean_file_name = f"{self.backup_file_prefix}{clean_dt}"
            prefix_len = len(clean_file_name)
            for file in os.listdir(self.backup_dir):
                cmp_file_name = file[:prefix_len]
                if len(cmp_file_name) == prefix_len and cmp_file_name <= clean_file_name:
                    os.remove(os.path.join(self.backup_dir, file))

    def shutdown(self, after_sec=180):
        return self.run("shutdown", str(after_sec), f"[お知らせ] {after_sec/60:.0f}分後にサーバーを停止します。")

    def broadcast_message(self, msg):
        return self.run("broadcast", f"[お知らせ] {msg}")

    def run(self, command, *args, encoding="utf-8"):
        request = Packet.make_command(command, *args, encoding=encoding)
        response = self.communicate(request)
        return response.payload.decode(encoding)

