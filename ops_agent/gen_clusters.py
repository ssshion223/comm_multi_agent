from data_class import (
    Node,
    Link,
    NetworkTopology,
    Cluster,
    ClusterLink,
    ClusterGraph
)
import json
from pathlib import Path
json_path = Path(__file__).resolve().parent.parent
top_json = json_path + "/topology.json"
link_json = json_path + "/links.json"
class TopologyManager:
    def __init__(self):
        