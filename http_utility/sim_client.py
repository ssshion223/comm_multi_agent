import requests
import json
from pathlib import Path
from config import (
    base_url,
    token,
    agent_id
)


class SimClient:
    def __init__(
            self,
            base_url: str = base_url,
            token: str = token,
            agent_id: str = agent_id,
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

    def get_topology(self):
        abs_url = self.base_url + "/topology"
        response = self.session.get(abs_url, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()["data"]
        with open(f"{self.ws}/json/topology.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


    def get_links(self):
        abs_url = self.base_url + "/links"
        response = self.session.get(abs_url, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()["data"]
        with open(f"{self.ws}/json/links.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def get_services(self):
        abs_url = self.base_url + "/services"
        response = self.session.get(abs_url, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()["data"]
        with open(f"{self.ws}/json/services.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def get_events(self, params: dict | None = None):
        abs_url = self.base_url + "/events"
        response = self.session.get(abs_url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()["data"]

        return data

import time
if __name__ == "__main__":
    # current_dir = Path(__file__)
    # print(current_dir)
    client = SimClient()
    client.get_topology()
    client.get_links()
    # client.get_services()
    cursor = 0
    while True:
        data = client.get_events({
            "sinceTsUs": cursor,
            "limit": 1000
        })
        events = data["events"]
        cursor = int(data["nextSinceTsUs"])
        if len(events) < 1000:
            break
    time.sleep(1)
    while True:
        params = {"sinceTsUs": cursor}
        data = client.get_events(params=params)
        cursor = int(data["nextSinceTsUs"])
        print(data["events"])
        time.sleep(5)
