from colorama import init, Fore
from datetime import datetime
import requests
import yaml
import os

init()


class Config:
    def __init__(self, config_path: str):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"{config_path} not found.")
        if not os.path.isfile(config_path):
            raise FileNotFoundError(f"{config_path} is not a file.")

        with open(config_path, encoding="utf-8") as file:
            config = file.read()
            self.data: dict = yaml.safe_load(config)

    def add_proxy(self, proxy_name: str):
        if not hasattr(self, "healthy_proxies"):
            self.healthy_proxies: list[dict] = []

        proxy: dict = self.fetch_proxy(proxy_name=proxy_name)
        self.healthy_proxies.append(proxy)

    def fetch_proxy(self, proxy_name: str) -> dict:
        """
        Fetches a proxy from configuration file.

        :param proxy_name: proxy name
        :return: Proxy
        """
        proxies: list[dict] = self.data["proxies"]
        # FIXME: If the proxy with the given name isn't in the configuration file,
        #  the next function will raise StopIteration.
        proxy: dict = next(proxy for proxy in proxies if proxy["name"] == proxy_name)
        return proxy

    def save(self):
        """
        Creates a configuration file and saves healthy proxies to it.
        """
        self.data["proxies"] = self.healthy_proxies
        file_name = str(datetime.now()).replace("-", "_").replace(":", "_").replace(".", "_")
        with open(f"{file_name}.yml", "w") as file:
            yaml.safe_dump(self.data, file)
            print(f"{Fore.GREEN}Healthy proxies saved to {file_name}.yml{Fore.RESET}")


class ProxyChecker:
    def __init__(
            self,
            config_path: str,
            external_controller: str = "127.0.0.1:61168",
            secret: str = "",
            timeout: int = 1500
    ):
        """
        :param config_path: Clash configuration file path.
        :param external_controller: External controller
        :param secret: Secret.
        :param timeout: Timeout in milliseconds.
        """
        self.config = Config(config_path=config_path)
        self.api: str = f"http://{external_controller}/"
        self.timeout: int = timeout
        self.auth_headers: dict = {
            "Authorization": f"Bearer {secret}"
        }

        self.exec()

    def exec(self):
        for proxy in self.get_proxies():
            delay: int | str = self.get_proxy_delay(proxy_name=proxy)
            if type(delay) == int:
                if delay < 500:
                    color = Fore.GREEN
                elif delay < 900:
                    color = Fore.YELLOW
                else:
                    color = Fore.RED
            else:
                color = Fore.RED
            print(f"{proxy}\t{color}{delay}{Fore.RESET}")

    def get_proxies(self) -> list[str]:
        """
        Returns a list of proxy names.
        """
        data: dict = requests.get(url=f"{self.api}proxies", headers=self.auth_headers).json()
        proxies: list[str] = data["proxies"]["GLOBAL"]["all"]
        # 'proxies' contains both proxies and proxy groups.
        # So we need to validate them and only return proxies.
        return list(filter(self._validate_proxy, proxies))

    def get_proxy_details(self, proxy_name: str) -> dict:
        """
        Returns proxy details.

        :param proxy_name: proxy name.
        :return: proxy details.
        """
        data: dict = requests.get(url=f"{self.api}proxies/{proxy_name}", headers=self.auth_headers).json()
        return data

    def get_proxy_delay(self, proxy_name: str) -> int | str:
        """
        Returns proxy delay.

        :param proxy_name: proxy name.
        :return: proxy delay in milliseconds or timeout message.
        """
        data: dict = requests.get(
            url=f"{self.api}proxies/{proxy_name}/delay",
            params={"url": "http://www.gstatic.com/generate_204", "timeout": self.timeout},
            headers=self.auth_headers
        ).json()

        return data.get("delay") or data["message"]

    def _validate_proxy(self, proxy_name: str) -> bool:
        """
        Validates that the proxy is not a proxy group.

        Returns True if the proxy is not a proxy group, False otherwise.

        :param proxy_name: proxy name.
        :return: bool
        """
        proxy: dict = self.get_proxy_details(proxy_name=proxy_name)
        return proxy["type"] not in ("Direct", "Reject", "select", "url-test", "relay", "fallback")
