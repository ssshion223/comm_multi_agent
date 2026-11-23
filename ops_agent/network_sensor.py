import json
from http_utility import SimClient
from pathlib import Path
from threading import Event, Thread

class NetworkSensor:
    def __init__(self):
        self.client = SimClient()
        self.ws = Path(__file__).resolve().parent.parent
        self._thread: Thread | None = None
        self._stop_event = Event()
        self._initial_data_ready = Event()

    def start_initial_thread(self):
        self._thread = Thread(
            target=self._run,
            name="topo_link_sensor",
            daemon=True
        )
        self._thread.start()
    def _run(self):
        while not self._stop_event.is_set():
            try:
                topo_data, links_data = self._fetch_topo_links()
                self._save_topo_links(topo_data, links_data)
                self._initial_data_ready.set()
                return
            except Exception:
                self._stop_event.wait(2.0)
    def stop(self):
        self._stop_event.set()
    def _fetch_topo_links(self):
        topo_path = "/topology"
        links_path = "/links"
        topo_data = self.client.get_json(path=topo_path)["data"]
        link_data = self.client.get_json(path=links_path)["data"]
        return topo_data, link_data
    def _save_topo_links(self, topo_data, link_data):
        with open(f"{self.ws}/json/topology.json", "w", encoding="utf-8") as f:
            json.dump(topo_data, f, ensure_ascii=False, indent=4)
        with open(f"{self.ws}/json/links.json", "w", encoding="utf-8") as f:
            json.dump(link_data, f, ensure_ascii=False, indent=4)
    def wait_initial_data(self):
        self._initial_data_ready.wait()
    def close(self):
        self.stop()
        if self._thread is not None and self._thread.is_alive():
            self._thread.join()
        self.client.close()