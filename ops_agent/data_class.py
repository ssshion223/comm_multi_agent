from dataclasses import dataclass, field
from typing import Literal

@dataclass
class Node:
    node_id: str
    kind: Literal["uav", "ground"]
    online: bool

@dataclass
class Link:
    link_id: str
    link_type: Literal["fiber", "satcom", "vhf", "uhf", "microwave", "5g"]
    src_node_id: str
    dst_node_id: str
    up: bool
    delay_ms: float
    jitter_ms: float
    bandwidth_bps: int
    ber: float
    packet_loss_rate: float

@dataclass
class NetworkTopology:
    nodes: dict[str, Node]
    links: dict[str, Link]

@dataclass
class Cluster:
    Cluster_id: str
    uav_ids: set[str]
    gnd_ids: set[str]
    gnd_adjacency: dict[str, dict[str, set[str]]]
    uav_adjacency: dict[str, dict[str, set[str]]]
    gateway_node: str

@dataclass
class ClusterLink:
    clink_id: str
    link_fiber_id: str
    link_satcom_id: str
    src_cluster_id: str
    dst_cluster_id: str

@dataclass
class ClusterGraph:
    clusters: dict[str, Cluster]
    cluster_adjacency: dict[str, dict[str, ClusterLink]]
    uav2clusters: dict[str, set[str]]

@dataclass
class ServiceResult:
    service_id: str
    paths: list[str]

