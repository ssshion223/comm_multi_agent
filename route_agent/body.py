"""Routing agent lifecycle and component orchestration."""
from http_utility.sim_client import SimClient
from .data_class import PlanningResult, ServiceRequest
from .ops_input_adapter import OpsInputAdapter
from .path_finder import PathFinder
from .route_planner import RoutePlanner


class RouteAgent:
    def __init__(self, client: SimClient | None = None):
        self.client = client
        self._owns_client = client is None
        self.path_finder: PathFinder | None = None
        self.route_planner: RoutePlanner | None = None
        self.services: list[ServiceRequest] = []
        self.result: PlanningResult | None = None

    def start(self, ops) -> PlanningResult:
        """Compute all test-service routes and submit accepted decisions."""
        topology, clusters, services = OpsInputAdapter.prepare(ops)
        path_finder = PathFinder(topology, clusters)
        route_planner = RoutePlanner(topology)
        self.path_finder = path_finder
        self.route_planner = route_planner
        self.services = services
        self.result = None
        self.result = route_planner.run(
            [path_finder.compute(s) for s in services], self._get_client())
        return self.result

    def _get_client(self) -> SimClient:
        if self.client is None:
            self.client = SimClient()
        return self.client

    def close(self):
        """Close only the simulator client created by this agent."""
        if self._owns_client and self.client is not None:
            self.client.close()
            self.client = None

