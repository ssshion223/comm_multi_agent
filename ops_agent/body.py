from .link_budget_analyzer import LinkBudgetAnalyzer
from .topology_manager import TopologyManager
from .network_sensor import NetworkSensor

class OpsAgent:
    def __init__(self):
        self.topology_manager = TopologyManager()
        self.link_budget_analyzer = LinkBudgetAnalyzer()
        self.network_sensor = NetworkSensor()
        self.initial_allready: bool = False

    def start(self):
        self.network_sensor.start_initial_thread()
        self.network_sensor.wait_initial_data()
        self.topology_manager.load()
        self.link_budget_analyzer.compute_initial_residual_bandwidth(self.topology_manager.topology)
        self.initial_allready = True
        
    def close(self):
        self.network_sensor.close()