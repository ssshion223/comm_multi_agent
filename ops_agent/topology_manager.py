import json
from pathlib import Path
from .data_class import (
    Node,
    QoS,
    Link,
    NetworkTopology,
    Cluster,
    ClusterGraph
)
from collections import deque
JSON_DIR = Path(__file__).resolve().parent.parent / "json"
DEFAULT_TOPOLOGY_PATH = JSON_DIR / "topology.json"
DEFAULT_LINKS_PATH = JSON_DIR / "links.json"

class TopologyManager:
    def __init__(self):
        self.topology: NetworkTopology | None = None
        self.cluster_graph: ClusterGraph | None = None

    def load(self, 
             topo_path: Path = DEFAULT_TOPOLOGY_PATH,
             link_path: Path = DEFAULT_LINKS_PATH):
        with open(topo_path, "r", encoding="utf-8") as f:
            topo_data = json.load(f)
        with open(link_path, "r", encoding="utf-8") as f:
            link_data = json.load(f)
        self.topology = self._build_global_topology(topo_data, link_data)
        self.cluster_graph = self._build_cluster_graph()
    def update(self):
        pass
        
    def _build_global_topology(self, topo_data, link_data) -> NetworkTopology:
        nodes: dict[str, Node] = {}
        for item in topo_data["nodes"]:
            node_type = item["nodeType"]
            node_id = item["nodeId"]
            if node_type not in {"uav", "ground"}:
                continue
            if node_id == "EXT001":
                continue
            nodes[node_id] = Node(
                node_id=node_id,
                kind=node_type,
                online=item["status"] == "online"
            )
        links: dict[str, Link] = {}
        for item in link_data["links"]:
            link_id = item["linkId"]
            src_node_id = item["srcNodeId"]
            dst_node_id = item["dstNodeId"]
            if src_node_id not in nodes or dst_node_id not in nodes:
                continue
            link_qos = QoS(
                delay_ms=item["params"]["delayMs"],
                jitter_ms=item["params"]["jitterMs"],
                bandwidth_bps=item["params"]["bandwidthBps"],
                ber=item["params"]["ber"],
                packet_loss_rate=item["params"]["packetLossRate"]
            )
            links[link_id] = Link(
                link_id=link_id,
                link_type=item["linkType"],
                src_node_id=src_node_id,
                dst_node_id=item["dstNodeId"],
                up=item["status"] == "up",
                link_qos=link_qos
            )
        adjacency = {node_id: {} for node_id in nodes}
        for link_id, link in links.items():
            adjacency[link.src_node_id].setdefault(link.dst_node_id, set()).add(link_id)
            adjacency[link.dst_node_id].setdefault(link.src_node_id, set()).add(link_id)
        return NetworkTopology(nodes, links, adjacency)

    def _build_cluster_graph(self):
        all_gnd_ids: set[str] = set()
        for node in self.topology.nodes.values():
            if node.kind == "ground":
                all_gnd_ids.add(node.node_id)
        gateway_ids: set[str] = set()
        # find gateways
        for link in self.topology.links.values():
            if link.link_type not in {"fiber", "satcom"}:
                continue
            if link.src_node_id not in all_gnd_ids:
                continue
            if link.dst_node_id not in all_gnd_ids:
                continue
            gateway_ids.add(link.src_node_id)
            gateway_ids.add(link.dst_node_id)

        # build clusters
        clusters: dict[str, Cluster] = {}
        gnd_to_cluster: dict[str, str] = {}
        visited_gnd: set[str] = set()
        for gateway_id in gateway_ids:
            cluster_id = f"CLU_{gateway_id}"
            cluster = Cluster(
                Cluster_id=cluster_id,
                gateway_node=gateway_id,
                gnd_ids={gateway_id},
                gnd_adjacency={},
                uav_adjacency={}
            )
            clusters[cluster_id] = cluster
            gnd_to_cluster[gateway_id] = cluster_id
            queue = deque([gateway_id])
            visited_gnd.add(gateway_id)
            while queue:
                current_gnd = queue.popleft()
                for neighbor_id, link_ids in self.topology.adjacency[current_gnd].items():
                    neighbor = self.topology.nodes[neighbor_id]
                    if neighbor.kind != "ground":
                        continue
                    local_link_ids = {link_id 
                                    for link_id in link_ids
                                    if self.topology.links[link_id].link_type 
                                    not in {"fiber", "satcom"}}
                    if not local_link_ids:
                        continue
                    cluster.gnd_ids.add(neighbor_id)
                    gnd_to_cluster[neighbor_id] = cluster_id
                    cluster.gnd_adjacency.setdefault(current_gnd, {}) \
                        .setdefault(neighbor_id, set()).update(local_link_ids)
                    cluster.gnd_adjacency.setdefault(neighbor_id, {}) \
                        .setdefault(current_gnd, set()).update(local_link_ids)
                    if neighbor_id not in visited_gnd:
                        visited_gnd.add(neighbor_id)
                        queue.append(neighbor_id)
        # build uav to clusters
        uav2clusters: dict[str, set[str]] = {}
        for link in self.topology.links.values():
            src_node = self.topology.nodes[link.src_node_id]
            dst_node = self.topology.nodes[link.dst_node_id]
            if src_node.kind == "uav" and dst_node.kind == "ground":
                uav_id = link.src_node_id
                gnd_id = link.dst_node_id
            elif src_node.kind == "ground" and dst_node.kind == "uav":
                uav_id = link.dst_node_id
                gnd_id = link.src_node_id
            else:
                continue
            cluster_id = gnd_to_cluster[gnd_id]
            cluster = clusters[cluster_id]
            cluster.uav_adjacency.setdefault(uav_id, {})  \
                .setdefault(gnd_id, set()) \
                .add(link.link_id)
            uav2clusters.setdefault(uav_id, set()).add(cluster_id)

        # build cluster adjacency
        cluster_adjacency: dict[str, dict[str, set[str]]] = {}
        for link in self.topology.links.values():
            if link.link_type not in {"fiber", "satcom"}:
                continue
            if link.src_node_id not in gateway_ids or link.dst_node_id not in gateway_ids:
                continue
            src_cluster_id = gnd_to_cluster[link.src_node_id]
            dst_cluster_id = gnd_to_cluster[link.dst_node_id]
            cluster_adjacency.setdefault(src_cluster_id, {}) \
                .setdefault(dst_cluster_id, set()) \
                .add(link.link_id) 
            cluster_adjacency.setdefault(dst_cluster_id, {}) \
                .setdefault(src_cluster_id, set()) \
                .add(link.link_id)
        
        return ClusterGraph(
            clusters=clusters,
            cluster_adjacency=cluster_adjacency,
            uav2clusters=uav2clusters
        )
