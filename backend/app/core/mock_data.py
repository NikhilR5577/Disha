from app.models.graph import HospitalGraph, Node

# A small mock graph representing a single floor MVP.
# Nodes
mock_nodes = [
    Node(id="entrance_1", name="Main Entrance", type="entrance", floor=1, x=0, y=0),
    Node(id="reception", name="Reception", type="department", floor=1, x=0, y=10),
    Node(id="corr_1", name="Corridor A", type="corridor", floor=1, x=10, y=10),
    Node(id="corr_2", name="Corridor B", type="corridor", floor=1, x=10, y=20),
    Node(id="opd_1", name="General OPD", type="department", floor=1, x=20, y=10),
    Node(id="pharmacy", name="Pharmacy", type="department", floor=1, x=20, y=20),
]

mock_graph = HospitalGraph()
for node in mock_nodes:
    mock_graph.add_node(node)

# Edges (distances/weights)
mock_graph.add_edge("entrance_1", "reception", weight=10.0)
mock_graph.add_edge("reception", "corr_1", weight=10.0)
mock_graph.add_edge("corr_1", "corr_2", weight=10.0)
mock_graph.add_edge("corr_1", "opd_1", weight=10.0)
mock_graph.add_edge("corr_2", "pharmacy", weight=10.0)
