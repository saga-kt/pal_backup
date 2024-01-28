# 概要
パルワールドサーバーの起動とバックアップ作成用プログラム。  
サーバが起動できない時のDiscord通知とGドライブへのバックアップ自動アップロード機能付き。

## 実行準備
- pythonをインストールし、`pip install -r requirements.txt`コマンドを実行する。
- パルワールドのサーバーをインストールし、起動できる状態にする。
- `PalWorldSettings.ini`の`RCONEnabled`を`True`に設定する。
- `PalWorldSettings.ini`の`AdminPassword`と`RCONPort`の設定値を確認する。
- `config.ini`を作成する。
  ```
  [DEFAULT]
  host = 127.0.0.1
  port = RCONPortの値
  password = AdminPasswordの値
  pal_dir = パルサーバーの起動ファイルPalServer.exeが入ってるフォルダー（例: C:/Steam/steamapps/common/PalServer）
  ```

## 実行
コマンドラインで実行
```cmd
python main.py
```
パルサーバーが起動されていない場合、自動で起動されます。  
毎時、接続中のユーザーがいなければ、`backup`フォルダ配下にダンプが生成されます。
