"""Adapt the four initialized OpsAgent attributes to the routing algorithms."""
from copy import deepcopy
from dataclasses import replace

import math

from ops_agent.data_class import QoS
from .data_class import ServiceRequest, validate_qos


class OpsInputAdapter:
    """Build an independent routing snapshot from initialized OpsAgent data."""

    @staticmethod
    def normalize_link_qos(qos: QoS) -> QoS:
        """Finite negative link bandwidth means zero remaining capacity, not an error.

        Business requirements still use validate_qos directly and cannot be negative.
        NaN/infinity and invalid delay/jitter/probability remain errors.
        """
        if not math.isfinite(qos.bandwidth_bps):
            raise ValueError("Link residual bandwidth must be finite")
        normalized = replace(qos, bandwidth_bps=max(0, qos.bandwidth_bps))
        validate_qos(normalized)
        return normalized

    @staticmethod
    def prepare(ops):
        """Return independent (residual topology, cluster graph, test requests).

        services is dict[str, ops_agent.data_class.Service]. Its requirement field
        maps to ServiceRequest.qos. Background load is already in residual_bw.
        No network calls, disk refresh, or upstream mutation are performed here.
        """
        topology = ops.topology_manager.topology
        graph = ops.topology_manager.cluster_graph
        if topology is None or graph is None:
            raise ValueError("Ops topology and cluster graph must be initialized")
        residual = ops.link_budget_analyzer.residual_bw
        missing = set(topology.links) - set(residual)
        if missing:
            raise ValueError(f"Missing residual bandwidth for links: {sorted(missing)[:10]}")
        # Deep-copy together to take a private calculation snapshot of all inputs.
        topology, graph, raw_services, residual = deepcopy((
            topology, graph, ops.link_budget_analyzer.services, residual))
        for lid, link in topology.links.items():
            link.link_qos = OpsInputAdapter.normalize_link_qos(replace(link.link_qos, bandwidth_bps=residual[lid]))
        services = [ServiceRequest(s.service_id, s.src_node_id, s.dst_node_id,
                                   s.requirement, s.priority)
                    for s in raw_services.values() if s.category == "test"]
        return topology, graph, services
