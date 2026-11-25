"""Hierarchical simple-path label traversal with monotone QoS pruning."""
import math
from ops_agent.data_class import ClusterGraph, NetworkTopology, QoS
from .data_class import CandidatePath, CandidateResult, ServiceRequest
from .ops_input_adapter import OpsInputAdapter


class PathFinder:
    """Generate QoS-feasible paths using the supplied cluster topology."""

    def __init__(self, topology: NetworkTopology, clusters: ClusterGraph,
                 weights: dict[str, float] | None = None,
                 backbone_types=frozenset({"fiber", "satcom"})):
        self.topology, self.clusters = topology, clusters
        self.backbone_types = frozenset(backbone_types)
        names = ("delay_ms", "jitter_ms", "bandwidth_bps", "ber", "packet_loss_rate")
        self.weights = dict.fromkeys(names, 1.0)
        if weights is not None:
            if set(weights) - set(names):
                raise ValueError("Unknown QoS weight")
            self.weights.update(weights)
        if any(not math.isfinite(w) or w < 0 for w in self.weights.values()):
            raise ValueError("Weights must be finite and nonnegative")
        for link in topology.links.values():
            OpsInputAdapter.normalize_link_qos(link.link_qos)
        # These graphs are immutable for this private routing snapshot.
        self._local_cache = {}
        self._backbone_cache = None

    def _memberships(self, node):
        return {cid for cid, c in self.clusters.clusters.items()
                if node == c.gateway_node or node in (c.gnd_ids or set())
                or cid in self.clusters.uav2clusters.get(node, set())}

    def _local_edges(self, cid):
        if cid in self._local_cache:
            return self._local_cache[cid]
        c = self.clusters.clusters[cid]
        edges = {}
        # Cluster UAV adjacency is stored in only one direction by TopologyManager.
        for adjacency in (c.gnd_adjacency or {}, c.uav_adjacency or {}):
            for src, neighbors in adjacency.items():
                for dst, ids in neighbors.items():
                    for lid in ids:
                        if self.topology.links[lid].link_type not in self.backbone_types:
                            edges.setdefault(src, {}).setdefault(dst, set()).add(lid)
                            edges.setdefault(dst, {}).setdefault(src, set()).add(lid)
        self._local_cache[cid] = edges
        return edges

    def _backbone_edges(self):
        if self._backbone_cache is not None:
            return self._backbone_cache
        edges = {}
        for cid, neighbors in self.clusters.cluster_adjacency.items():
            src = self.clusters.clusters[cid].gateway_node
            for other, ids in neighbors.items():
                dst = self.clusters.clusters[other].gateway_node
                for lid in ids:
                    if self.topology.links[lid].link_type in self.backbone_types:
                        edges.setdefault(src, {}).setdefault(dst, set()).add(lid)
        self._backbone_cache = edges
        return edges

    @staticmethod
    def _extend(q, edge):
        # Jitter is a standard deviation (ms). For uncorrelated per-hop
        # delay fluctuations, variances add: sigma_path = sqrt(sum(sigma_hop**2)).
        return QoS(q.delay_ms + edge.delay_ms, math.hypot(q.jitter_ms, edge.jitter_ms),
                   min(q.bandwidth_bps, max(0, edge.bandwidth_bps)),
                   q.ber + (1 - q.ber) * edge.ber,
                   q.packet_loss_rate + (1 - q.packet_loss_rate) * edge.packet_loss_rate)

    @staticmethod
    def _feasible(q, target):
        return (q.delay_ms <= target.delay_ms and q.jitter_ms <= target.jitter_ms
                and q.bandwidth_bps >= target.bandwidth_bps and q.ber <= target.ber
                and q.packet_loss_rate <= target.packet_loss_rate)

    def _score(self, q, target):
        # Normalized headroom; higher is better. Zero bounds contribute zero.
        result = 0.0
        for name, weight in self.weights.items():
            value, bound = getattr(q, name), getattr(target, name)
            if name == "bandwidth_bps":
                headroom = 0 if value == 0 else 1 - bound / value
            else:
                headroom = 0 if bound == 0 else 1 - value / bound
            result += weight * headroom
        return result

    def compute(self, service: ServiceRequest) -> CandidateResult:
        t = self.topology
        for node in (service.src_node_id, service.dst_node_id):
            if node not in t.nodes:
                raise ValueError(f"Unknown endpoint: {node}")
            if not t.nodes[node].online:
                return CandidateResult(service, [])
        found = {}
        backbone = self._backbone_edges()
        for src_cluster in sorted(self._memberships(service.src_node_id)):
            for dst_cluster in sorted(self._memberships(service.dst_node_id)):
                if src_cluster == dst_cluster:
                    stages = [(service.dst_node_id, self._local_edges(src_cluster))]
                else:
                    stages = [
                        (self.clusters.clusters[src_cluster].gateway_node, self._local_edges(src_cluster)),
                        (self.clusters.clusters[dst_cluster].gateway_node, backbone),
                        (service.dst_node_id, self._local_edges(dst_cluster)),
                    ]
                # Label includes visited nodes: prevents cycles across stage boundaries too.
                stack = [(0, (service.src_node_id,), (), QoS(0, 0, math.inf, 0, 0))]
                while stack:
                    phase, nodes, links, q = stack.pop()
                    current = nodes[-1]
                    if phase == len(stages):
                        found[links] = CandidatePath(nodes, links, q, self._score(q, service.qos),
                                                     service.qos.bandwidth_bps * len(links))
                        continue
                    target, edges = stages[phase]
                    if current == target:
                        stack.append((phase + 1, nodes, links, q))
                        continue
                    for neighbor, ids in edges.get(current, {}).items():
                        if neighbor in nodes or not t.nodes[neighbor].online:
                            continue
                        for lid in ids:
                            edge = t.links[lid]
                            if not edge.up or {edge.src_node_id, edge.dst_node_id} != {current, neighbor}:
                                continue
                            extended = self._extend(q, edge.link_qos)
                            if self._feasible(extended, service.qos):
                                stack.append((phase, nodes + (neighbor,), links + (lid,), extended))
        paths = sorted(found.values(), key=lambda p: (-p.score, p.resource_cost, p.link_ids))
        return CandidateResult(service, paths)
