from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os
import datetime

class GDrive:
    """
    バックアップをアップロードするGドライブ
    """
    def __init__(self, auth_type="service_account"):
        self.backup_file_prefix = "pal_backup_"
        self.auth_type = auth_type
        if auth_type == "service_account":
            self.login_with_service_account()
        else:
            self.refresh_token()

        # バックアップフォルダ作成
        # 事前にフォルダーを作成して、サービスアカウントと共有する
        folder_name = "pal_backup"
        folder_meta = {
            "title":  folder_name,
            "mimeType": "application/vnd.google-apps.folder",
        }
        folder_id = None
        for file in self.drive.ListFile().GetList():
            if file["title"] == folder_name:
                folder_id = file["id"]
                break
        if folder_id == None:
            folder = self.drive.CreateFile(folder_meta)
            folder.Upload()
            folder_id = folder.get("id")
        self.backup_folder_id = folder_id


    def upload_backup_file(self, backup_file):
        """
        パス込みのファイルを渡せばバックアップフォルダにアップロードする
        """
        file1 = self.drive.CreateFile({"parents": [{"id": self.backup_folder_id}], "title": os.path.basename(backup_file)})
        file1.SetContentFile(backup_file)
        file1.Upload()


    def clean_backup_data(self, keep_days=7):
        # 古いバックアップを削除
        clean_dt = (datetime.datetime.now() - datetime.timedelta(days=keep_days)).strftime("%Y%m%d")
        clean_file_name = f"{self.backup_file_prefix}{clean_dt}"
        prefix_len = len(clean_file_name)
        count = 0
        for f in self.drive.ListFile().GetList():
            cmp_file_name = f["title"][:prefix_len]
            if len(cmp_file_name) == prefix_len and cmp_file_name <= clean_file_name:
                f.Delete()
                count += 1
        return count


    def login_with_service_account(self):
        gauth = GoogleAuth(settings_file="settings.yaml")
        gauth.ServiceAuth()
        self.drive = GoogleDrive(gauth)


    def refresh_token(self):
        cred_file = "credentials.json"
        gauth = GoogleAuth()
        gauth.LoadCredentialsFile(cred_file)
        if gauth.credentials is None:
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            try:
                gauth.Refresh()
            except:
                gauth.LocalWebserverAuth()
        else:
            gauth.Authorize()
        gauth.SaveCredentialsFile(cred_file)
        self.drive = GoogleDrive(gauth)

