from typing import Dict, List, Optional
from pydantic import BaseModel

class Node(BaseModel):
    id: str
    name: Optional[str] = None
    name_hi: Optional[str] = None
    type: str  # e.g., 'entrance', 'corridor', 'department', 'lift', 'stairs'
    floor: int
    x: float  # For calculating heuristic in A* or visual plotting
    y: float
    is_room: Optional[bool] = None

class Edge(BaseModel):
    source_id: str
    target_id: str
    weight: float
    direction_en: Optional[str] = None
    direction_hi: Optional[str] = None
    is_accessible: bool = True # False if stairs

class HospitalGraph(BaseModel):
    nodes: Dict[str, Node] = {}
    edges: Dict[str, List[Edge]] = {}

    def add_node(self, node: Node):
        self.nodes[node.id] = node
        if node.id not in self.edges:
            self.edges[node.id] = []

    def add_edge(self, source_id: str, target_id: str, weight: float, direction_en: str = None, direction_hi: str = None, is_accessible: bool = True, bidirectional: bool = True):
        edge1 = Edge(source_id=source_id, target_id=target_id, weight=weight, direction_en=direction_en, direction_hi=direction_hi, is_accessible=is_accessible)
        self.edges[source_id].append(edge1)
        if bidirectional:
            edge2 = Edge(source_id=target_id, target_id=source_id, weight=weight, direction_en=direction_en, direction_hi=direction_hi, is_accessible=is_accessible)
            self.edges[target_id].append(edge2)
