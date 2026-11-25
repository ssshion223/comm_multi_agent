"""Maximize admitted priority sum, then minimize cost and maximize QoS headroom.

Link bandwidth is the residual capacity available before this planning batch.
"""
from uuid import uuid4
from itertools import combinations
from math import fsum, prod

from requests import HTTPError

from http_utility.sim_client import SimClient
from ops_agent.data_class import NetworkTopology
from .path_finder import PathFinder
from .data_class import CandidatePath, CandidateResult, PlanningResult, ServiceRequest
from .ops_input_adapter import OpsInputAdapter


class RoutePlanner:
    """Validate candidates, select routes adaptively and submit the decisions."""

    def __init__(self, topology: NetworkTopology):
        self.receipts: dict[str, dict] = {}
        self.request_ids: dict[str, str] = {}
        self.result: PlanningResult | None = None
        self.topology = topology
        for link in topology.links.values():
            OpsInputAdapter.normalize_link_qos(link.link_qos)

    def run(self, candidates: list[CandidateResult], client: SimClient) -> PlanningResult:
        """Finish the entire planning batch, then submit all accepted routes.

        On failure, result and successful receipts remain available for inspection.
        Earlier accepted simulator submissions are not rolled back.
        """
        self.result = None
        self.receipts = {}
        self.request_ids = {}
        self.result = self.plan(candidates)
        services = {candidate.service.service_id: candidate.service for candidate in candidates}
        for sid, path in self.result.accepted.items():
            self.receipts[sid] = self.submit(client, services[sid], path)
        return self.result

    def plan(self, candidates: list[CandidateResult]) -> PlanningResult:
        ids = [c.service.service_id for c in candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate service_id")
        for c in candidates:
            if type(c.service.priority) is not int or c.service.priority < 0:
                raise ValueError("priority must be a nonnegative integer")
            for path in c.paths:
                self._validate(c, path)
        best, info = self._select_routes(candidates)
        result = PlanningResult(accepted=best, solver_info=info)
        for c in candidates:
            sid = c.service.service_id
            if sid not in best:
                result.rejected[sid] = "no_qos_feasible_path" if not c.paths else "resource_conflict"
            else:
                for lid in best[sid].link_ids:
                    result.link_load_bps[lid] = result.link_load_bps.get(lid, 0) + c.service.qos.bandwidth_bps
        return result

    def _select_routes(self, candidates):
        topology = self.topology
        active = {c.service.service_id: c for c in candidates if c.paths}
        capacity = {lid: max(0, l.link_qos.bandwidth_bps) for lid, l in topology.links.items()}
        users = {}
        for sid, c in active.items():
            for lid in set().union(*(set(p.link_ids) for p in c.paths)):
                users.setdefault(lid, set()).add(sid)
        pressure = {lid: sum(active[s].service.qos.bandwidth_bps for s in ids) / capacity[lid]
                    if capacity[lid] else float('inf') for lid, ids in users.items()}
        contested = {lid for lid, p in pressure.items() if p > 1}

        def objective(chosen):
            return (sum(active[s].service.priority for s in chosen),
                    -fsum(p.resource_cost for p in chosen.values()),
                    fsum(p.score for p in chosen.values()))

        def loads_of(chosen):
            loads = {}
            for sid, path in chosen.items():
                for lid in path.link_ids:
                    loads[lid] = loads.get(lid, 0) + active[sid].service.qos.bandwidth_bps
            return loads

        path_orders = {}
        for sid, c in active.items():
            path_orders[sid] = (
                sorted(c.paths, key=lambda p: (p.resource_cost, -p.score, p.link_ids)),
                sorted(c.paths, key=lambda p: (
                    sum(pressure[lid] for lid in p.link_ids if lid in contested),
                    p.resource_cost, -p.score, p.link_ids)),
            )

        def add(chosen, sid, mode=0):
            loads = loads_of(chosen)
            c = active[sid]
            for path in path_orders[sid][mode]:
                if all(loads.get(lid, 0) + c.service.qos.bandwidth_bps <= capacity[lid]
                       for lid in path.link_ids):
                    trial = {**chosen, sid: path}
                    if objective(trial) > objective(chosen):
                        return trial
            return chosen

        def demand(sid):
            return active[sid].service.qos.bandwidth_bps

        def density(sid):
            d = demand(sid)
            return active[sid].service.priority / d if d else float('inf')

        if not contested:
            # No link can overload even if every possible user selects it. The
            # lexicographic optimum separates into independent per-service choices.
            best = {}
            for sid in sorted(active):
                best = add(best, sid)
            return best, {'method': 'independent_capacity_safe_optimum',
                          'status': 'optimal_within_candidate_set',
                          'candidate_count': sum(len(c.paths) for c in candidates),
                          'contested_link_count': 0, 'priority_sum': objective(best)[0],
                          'priority_upper_bound': objective(best)[0], 'priority_optimal': True,
                          'secondary_objectives_optimal': True}

        orders = [
            sorted(active, key=lambda s: (-active[s].service.priority, len(active[s].paths), demand(s), s)),
            sorted(active, key=lambda s: (-density(s), len(active[s].paths), s)),
            sorted(active, key=lambda s: (len(active[s].paths), -active[s].service.priority, s)),
            sorted(active, key=lambda s: (demand(s), -active[s].service.priority, s)),
        ]
        best = {}
        for order in orders:
            for mode in range(len(next(iter(path_orders.values()), ()))):
                chosen = {}
                for sid in order:
                    chosen = add(chosen, sid, mode)
                if objective(chosen) > objective(best):
                    best = chosen

        # Compare work estimates derived entirely from this input. Small search spaces
        # are cheaper to solve exactly than to inspect all local-exchange neighbours.
        candidate_count = sum(len(c.paths) for c in active.values())
        combinations_count = prod(len(c.paths) + 1 for c in active.values())
        local_work = candidate_count * len(active) * (len(active) + candidate_count)
        if combinations_count <= local_work or not active:
            order = orders[0]
            chosen, loads = {}, {}
            suffix = [0] * (len(order) + 1)
            for i in range(len(order)-1, -1, -1):
                suffix[i] = suffix[i+1] + active[order[i]].service.priority

            def search(i, priority):
                nonlocal best
                if priority + suffix[i] < objective(best)[0]:
                    return
                if i == len(order):
                    if objective(chosen) > objective(best):
                        best = dict(chosen)
                    return
                sid = order[i]
                for path in path_orders[sid][0]:
                    if any(loads.get(lid, 0) + demand(sid) > capacity[lid] for lid in path.link_ids):
                        continue
                    chosen[sid] = path
                    for lid in path.link_ids:
                        loads[lid] = loads.get(lid, 0) + demand(sid)
                    search(i+1, priority + active[sid].service.priority)
                    chosen.pop(sid)
                    for lid in path.link_ids:
                        loads[lid] -= demand(sid)
                search(i+1, priority)
            search(0, 0)
            return best, {'method': 'input_cost_selected_exact_search',
                          'status': 'optimal_within_candidate_set',
                          'candidate_count': candidate_count, 'estimated_combinations': combinations_count,
                          'estimated_local_work': local_work, 'priority_sum': objective(best)[0],
                          'priority_upper_bound': objective(best)[0], 'priority_optimal': True,
                          'secondary_objectives_optimal': True}

        # Strict objective improvement guarantees termination on the finite candidate set.
        moves = 0
        while True:
            improved = best
            # Re-route existing services and refill freed capacity; also try a single eviction.
            for removed in [None] + sorted(best):
                base = {s: p for s, p in best.items() if s != removed}
                pending = [s for s in active if s not in base]
                for order in orders:
                    for mode in range(len(next(iter(path_orders.values()), ()))):
                        trial = base
                        for sid in order:
                            if sid in pending:
                                  trial = add(trial, sid, mode)
                        if objective(trial) > objective(improved):
                            improved = trial
                # Explicit two-for-one exchanges avoid greedy density/priority traps.
                rejected = [s for s in pending if s != removed]
                for first, second in combinations(rejected, 2):
                    if removed is not None and (active[first].service.priority + active[second].service.priority
                                                < active[removed].service.priority):
                        continue
                    for p1 in path_orders[first][0]:
                        trial = {**base, first: p1}
                        if any(v > capacity[lid] for lid, v in loads_of(trial).items()):
                            continue
                        trial = add(trial, second)
                        if second not in trial:
                            continue
                        if removed is not None:
                            trial = add(trial, removed)
                        if objective(trial) > objective(improved):
                            improved = trial
            if objective(improved) <= objective(best):
                break
            best = improved
            moves += 1

        # A valid input-derived upper bound: compulsory link overload forces priority loss.
        upper = sum(c.service.priority for c in active.values())
        mandatory = {}
        for sid, c in active.items():
            for lid in set.intersection(*(set(p.link_ids) for p in c.paths)):
                mandatory.setdefault(lid, []).append(sid)
        for lid, ids in mandatory.items():
            if sum(demand(s) for s in ids) > capacity[lid]:
                upper = min(upper, sum(c.service.priority for c in active.values())
                            - min(active[s].service.priority for s in ids))
        return best, {
            'method': 'capacity_aware_multistart_with_local_exchanges',
            'status': 'heuristic_feasible',
            'candidate_count': sum(len(c.paths) for c in candidates),
            'estimated_combinations': combinations_count, 'estimated_local_work': local_work,
            'contested_link_count': len(contested), 'improvement_rounds': moves,
            'priority_sum': objective(best)[0], 'priority_upper_bound': upper,
            'priority_optimal': objective(best)[0] == upper,
            'secondary_objectives_optimal': False,
        }

    def _validate(self, candidate, path):
        s = candidate.service
        if (not path.node_ids or path.node_ids[0] != s.src_node_id
                or path.node_ids[-1] != s.dst_node_id
                or len(path.node_ids) != len(path.link_ids) + 1
                or len(set(path.node_ids)) != len(path.node_ids)):
            raise ValueError("Invalid candidate path")
        from ops_agent.data_class import QoS
        q = QoS(0, 0, float("inf"), 0, 0)
        for node in path.node_ids:
            if node not in self.topology.nodes or not self.topology.nodes[node].online:
                raise ValueError("Candidate contains unavailable node")
        for a, b, lid in zip(path.node_ids, path.node_ids[1:], path.link_ids):
            link = self.topology.links[lid]
            if not link.up or {a, b} != {link.src_node_id, link.dst_node_id}:
                raise ValueError("Candidate contains unavailable link")
            q = PathFinder._extend(q, link.link_qos)
        if not PathFinder._feasible(q, s.qos):
            raise ValueError("Candidate violates QoS")

    def submit(self, client: SimClient, service: ServiceRequest,
               path: CandidatePath, request_id: str | None = None) -> dict:
        """Push one ordered link path; return the receipt or raise on rejection.

        Retain request_id when explicitly retrying the same submission.
        This function does not change any local input files.
        """
        if (not path.node_ids or path.node_ids[0] != service.src_node_id
                or path.node_ids[-1] != service.dst_node_id
                or len(path.link_ids) + 1 != len(path.node_ids)):
            raise ValueError("Path endpoints or segment count do not match service")
        request_id = request_id or f"route-{uuid4().hex}"
        self.request_ids[service.service_id] = request_id
        try:
            response = client.post_json(
                f"/services/{service.service_id}/path",
                {
                    "requestId": request_id,
                    "srcNodeId": service.src_node_id,
                    "dstNodeId": service.dst_node_id,
                    "segments": [{"type": "link", "id": lid} for lid in path.link_ids],
                },
            )
        except HTTPError as error:
            detail = error.response.text if error.response is not None else str(error)
            raise RuntimeError(f"Path submission failed for {service.service_id}: {detail}") from error
        if (response.get("code") != 0
                or response.get("data", {}).get("result") != "accepted"):
            raise RuntimeError(f"Path submission failed for {service.service_id}: {response}")
        return response
