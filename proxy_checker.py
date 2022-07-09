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

    def get_proxy_details(self, proxy_name: str) -> dict:
        """
        Returns proxy details.

        :param proxy_name: proxy name.
        :return: proxy details.
        """
        data: dict = requests.get(url=f"{self.api}proxies/{proxy_name}", headers=self.auth_headers).json()
        return data
