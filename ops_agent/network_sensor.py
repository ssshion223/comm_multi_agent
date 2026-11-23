from http_utility import SimClient
from pathlib import Path
class NetworkSensor:
    def __init__(self):
        self.client = SimClient()
        self.ws = Path(__file__).resolve().parent.parent

    def _poll_topo_links():
        pass