from .link_budget_analyzer import LinkBudgetAnalyzer
from .topology_manager import TopologyManager


class OpsAgent:
    def __init__(self):
        self.topology_manager = TopologyManager()
        self.link_budget_analyzer = LinkBudgetAnalyzer()
        