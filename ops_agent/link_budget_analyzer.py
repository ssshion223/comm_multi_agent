import json
from pathlib import Path

from .data_class import QoS, Service, NetworkTopology

BG_SERVICE_PATH = Path(__file__).resolve().parent.parent / "bg-service.json"
PATHS_JSON_PATH = Path(__file__).resolve().parent.parent / "json" / "paths.json"

class LinkBudgetAnalyzer:
    def __init__(self):
        self.services: dict[str, Service] = {}
        self.residual_bw: dict[str, int] = {}
        self._get_all_services()
    def _get_all_services(self): # 兼容性接口
        with open(BG_SERVICE_PATH, "r", encoding="utf-8") as f:
            service_data = json.load(f)
        with open(PATHS_JSON_PATH, "r", encoding="utf-8") as f:
            path_data = json.load(f)

        services: dict[str, Service] = {}
        for item in service_data:
            requirement = item["requirement"]
            service_id = item["serviceId"]
            service_path = path_data.get(service_id)
            paths = [
                segment["id"]
                for segment in service_path["segments"]
                if segment["type"] == "link"
            ] if service_path else []

            service = Service(
                service_id=service_id,
                category=item["category"],
                service_type=item["serviceType"],
                src_node_id=item["srcNodeId"],
                dst_node_id=item["dstNodeId"],
                priority=item["priority"],
                requirement=QoS(
                    delay_ms=requirement["delayMs"],
                    jitter_ms=requirement["jitterMs"],
                    bandwidth_bps=int(requirement["bandwidthBps"]),
                    ber=requirement["ber"],
                    packet_loss_rate=requirement["packetLossRate"],
                ),
                paths=paths,
            )
            services[service.service_id] = service

        self.services = services
        return self.services

    def compute_initial_residual_bandwidth(self, topology: NetworkTopology):
        self.residual_bw = {
            link_id: link.link_qos.bandwidth_bps
            for link_id, link in topology.links.items()
        }
        for service in self.services.values():
            if service.category == "test":
                continue
            for link_id in service.paths:
                self.residual_bw[link_id] -= service.requirement.bandwidth_bps

    def res_bw_update(self):
        pass