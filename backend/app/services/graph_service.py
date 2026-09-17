from sqlalchemy.orm import Session
from app.models.graph import HospitalGraph, Node
from app.models.schema import NodeDB, EdgeDB
import threading

_cached_graph = None
_graph_lock = threading.Lock()

def get_graph_from_db(db: Session, force_refresh: bool = False) -> HospitalGraph:
    global _cached_graph
    
    # Fast path: return cached graph if available
    if _cached_graph is not None and not force_refresh:
        return _cached_graph
        
    with _graph_lock:
        # Check again in case another thread populated it while waiting for the lock
        if _cached_graph is not None and not force_refresh:
            return _cached_graph
            
        nodes = db.query(NodeDB).all()
        edges = db.query(EdgeDB).all()
        
        graph = HospitalGraph()
        for n in nodes:
            node_obj = Node(
                id=n.id, 
                name=n.name,
                name_hi=n.name_hi,
                type="room" if n.is_room else "corridor", 
                floor=n.floor, 
                x=n.x, 
                y=n.y,
                is_room=n.is_room
            )
            graph.add_node(node_obj)
            
        for e in edges:
            graph.add_edge(
                source_id=e.from_id,
                target_id=e.to_id,
                weight=e.distance,
                direction_en=None,
                direction_hi=None,
                is_accessible=True, # Update later if stairs
                bidirectional=False # Edges are already two-way in the JSON/DB
            )
            
        _cached_graph = graph
        return _cached_graph
