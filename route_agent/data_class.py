"""Routing contracts supplementing ops_agent.data_class without modifying it."""
from dataclasses import dataclass, field
import math
from ops_agent.data_class import QoS, ServiceResult


def validate_qos(q: QoS) -> None:
    if not all(math.isfinite(v) and v >= 0 for v in
               (q.delay_ms, q.jitter_ms, q.bandwidth_bps, q.ber, q.packet_loss_rate)):
        raise ValueError("QoS values must be finite and nonnegative")
    if q.ber > 1 or q.packet_loss_rate > 1:
        raise ValueError("Probability must be in [0, 1]")


@dataclass(frozen=True)
class ServiceRequest:
    service_id: str
    src_node_id: str
    dst_node_id: str
    qos: QoS
    priority: int = 0

    def __post_init__(self):
        validate_qos(self.qos)
        if type(self.priority) is not int or self.priority < 0:
            raise ValueError("priority must be a nonnegative integer")


@dataclass(frozen=True)
class CandidatePath:
    node_ids: tuple[str, ...]
    link_ids: tuple[str, ...]
    qos: QoS
    score: float
    resource_cost: float  # requested bandwidth * hops, in bit/s-link


@dataclass
class CandidateResult:
    service: ServiceRequest
    paths: list[CandidatePath]


@dataclass
class PlanningResult:
    accepted: dict[str, CandidatePath] = field(default_factory=dict)
    rejected: dict[str, str] = field(default_factory=dict)
    link_load_bps: dict[str, float] = field(default_factory=dict)
    solver_info: dict = field(default_factory=dict)

    def to_service_results(self) -> list[ServiceResult]:
        return [ServiceResult(service_id=sid, paths=list(path.link_ids))
                for sid, path in self.accepted.items()]
