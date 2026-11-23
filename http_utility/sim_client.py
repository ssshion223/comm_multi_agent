import requests
from pathlib import Path
from config.configuration import (
    sim_base_url,
    sim_token,
    sim_agent_id
)


class SimClient:
    def __init__(
            self,
            base_url: str = sim_base_url,
            token: str = sim_token,
            agent_id: str = sim_agent_id,
            timeout: float = 5
            ):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "X-Open-Token": token,
            "X-Agent-Id": agent_id
        })
        self.timeout = timeout
        self.ws = Path(__file__).resolve().parent.parent

    def close(self):
        self.session.close()

    def get_json(self,
                 path: str,
                 params: dict | None = None
                 ):
        url = self.base_url + "/" + path.lstrip("/")
        response = self.session.get(
            url=url,
            params=params,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    
    def post_json(self,
                  path: str,
                  body: dict
                  ):
        url = self.base_url + "/" + path.lstrip("/")
        response = self.session.post(
            url=url,
            json=body,
            timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()
    # def get_topology(self):
    #     abs_url = self.base_url + "/topology"
    #     response = self.session.get(abs_url, timeout=self.timeout)
    #     response.raise_for_status()
    #     data = response.json()["data"]
    #     with open(f"{self.ws}/json/topology.json", "w", encoding="utf-8") as f:
    #         json.dump(data, f, ensure_ascii=False, indent=4)


    # def get_links(self):
    #     abs_url = self.base_url + "/links"
    #     response = self.session.get(abs_url, timeout=self.timeout)
    #     response.raise_for_status()
    #     data = response.json()["data"]
    #     with open(f"{self.ws}/json/links.json", "w", encoding="utf-8") as f:
    #         json.dump(data, f, ensure_ascii=False, indent=4)

    # def get_services(self):
    #     abs_url = self.base_url + "/services"
    #     response = self.session.get(abs_url, timeout=self.timeout)
    #     response.raise_for_status()
    #     data = response.json()["data"]
    #     with open(f"{self.ws}/json/services.json", "w", encoding="utf-8") as f:
    #         json.dump(data, f, ensure_ascii=False, indent=4)

    # def get_events(self, params: dict | None = None):
    #     abs_url = self.base_url + "/events"
    #     response = self.session.get(abs_url, params=params, timeout=self.timeout)
    #     response.raise_for_status()
    #     data = response.json()["data"]

    #     return data

# import time
