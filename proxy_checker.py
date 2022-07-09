import requests


class ProxyChecker:
    def __init__(
            self,
            external_controller: str = "127.0.0.1:61168",
            secret: str = "",
            timeout: int = 1500
    ):
        """
        :param external_controller: External controller
        :param secret: Secret.
        :param timeout: Timeout in milliseconds.
        """
        self.api: str = f"http://{external_controller}/"
        self.timeout: int = timeout
        self.auth_headers: dict = {
            "Authorization": f"Bearer {secret}"
        }

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
