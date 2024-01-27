from discord_webhook import DiscordWebhook
from requests.exceptions import Timeout


class DiscordManager:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_message(self, msg, timeout=3):
        webhook = DiscordWebhook(url=self.webhook_url, content=msg, timeout=timeout)
        try:
            response = webhook.execute()
        except Timeout as err:
            raise Exception("Discordのメッセージを送信できませんでした。")
