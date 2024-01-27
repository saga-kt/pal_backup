from discord_webhook import DiscordWebhook
from requests.exceptions import Timeout


class DiscordManager:
    def __init__(self, webhook_url, notification_role_id=""):
        self.webhook_url = webhook_url
        self.notification_role_id = notification_role_id
        if self.notification_role_id:
            self.message_prefix = f"<@&{self.notification_role_id}> "
        else:
            self.message_prefix = ""

    def send_message(self, msg, timeout=3):
        webhook = DiscordWebhook(url=self.webhook_url, content=f"{self.message_prefix}{msg}", timeout=timeout)
        try:
            response = webhook.execute()
        except Timeout as err:
            raise Exception("Discordのメッセージを送信できませんでした。")
