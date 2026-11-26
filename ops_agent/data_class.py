from dataclasses import dataclass
from typing import Literal

@dataclass
class Node:
    node_id: str
    kind: Literal["uav", "ground"]
    online: bool

@dataclass
class QoS:
    delay_ms: float
    jitter_ms: float
    bandwidth_bps: int
    ber: float
    packet_loss_rate: float
@dataclass
class Link:
    link_id: str
    link_type: Literal["fiber", "satcom", "vhf", "uhf", "microwave", "5g"]
    src_node_id: str
    dst_node_id: str
    up: bool
    link_qos: QoS

@dataclass
class NetworkTopology:
    nodes: dict[str, Node]
    links: dict[str, Link]
    adjacency: dict[str, dict[str, set[str]]]

@dataclass
class Cluster:
    Cluster_id: str
    gateway_node: str
    # uav_ids: set[str] | None = None
    gnd_ids: set[str] | None = None
    gnd_adjacency: dict[str, dict[str, set[str]]] | None = None
    uav_adjacency: dict[str, dict[str, set[str]]] | None = None


@dataclass
class ClusterGraph:
    clusters: dict[str, Cluster]
    cluster_adjacency: dict[str, dict[str, set[str]]]
    uav2clusters: dict[str, set[str]]

@dataclass
class ServiceResult:
    service_id: str
    paths: list[str]

@dataclass
class Service:
    service_id: str
    category: Literal["background", "test"]
    service_type: Literal["data", "image", "video", "voice"]
    src_node_id: str
    dst_node_id: str
    priority: int
    requirement: QoS
    paths: list[str]
