import requests
import time


class Webhook:
    def __init__(self, url: str):
        self.url = url

    def post_data(self, data: dict) -> requests.Response:
        print("Posting")
        r = requests.post(self.url, json=data)
        print(f"status: {r.status_code}\ntext:\n{r.text}")
        if r.status_code == 429:  # Rate limit
            print("Rate limit!")
            if "retry_after" in r.json():
                retry_time = r.json()["retry_after"]
                time.sleep(retry_time / 1000 + 0.1)
                r = self.post_data(data)
            else:
                time.sleep(10)
                r = self.post_data(data)
        return r


class DiscordWebhook(Webhook):
    def __init__(self, url: str, name: str = None, avatar_url: str = None):
        super().__init__(url)
        self.name = name
        self.avatar_url = avatar_url

    def webhook_post(self, data: dict) -> requests.Response:
        data["avatar_url"] = self.avatar_url
        if "username" not in data:
            data["username"] = self.name
        return self.post_data(data)

    def webhook_post_content(self, content: str) -> requests.Response:
        data = {
            "avatar_url": self.avatar_url,
            "username": self.name,
            "content": content
        }
        return self.post_data(data)

    def webhook_post_embed(self, title: str, description: str, url: str, footer: str = None) -> requests.Response:
        embed = {
            "title": title,
            "description": description,
            "url": url
        }
        if footer:
            embed["footer"] = {"text": footer}
        data = {
            "avatar_url": self.avatar_url,
            "username": self.name,
            "embeds": [embed]
        }
        return self.post_data(data)
