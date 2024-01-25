from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os


class GDrive:
    """
    バックアップをアップロードするGドライブ
    """
    def __init__(self):
        self.refresh_token()

        # バックアップフォルダ作成
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

    def refresh_token(self):
        cred_file = "credentials.txt"
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

