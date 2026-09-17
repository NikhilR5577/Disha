import heapq
from typing import List, Dict, Optional
from pydantic import BaseModel
from app.models.graph import HospitalGraph, Node

class RouteStep(BaseModel):
    node_id: str
    node_name: Optional[str] = None
    instruction_en: str
    instruction_hi: str
    distance: float
    x: float
    y: float
    floor: int

class RouteResponse(BaseModel):
    path_found: bool
    total_distance: float
    steps: List[RouteStep]
    path_coords: List[Dict[str, float]] = []

def find_shortest_path(graph: HospitalGraph, start_id: str, dest_id: str, accessible_only: bool = False) -> RouteResponse:
    if start_id not in graph.nodes or dest_id not in graph.nodes:
        return RouteResponse(path_found=False, total_distance=0, steps=[], path_coords=[])

    # Priority queue for Dijkstra's: (distance, current_node_id)
    pq = [(0, start_id)]
    
    # Track the shortest distance to each node
    distances = {node_id: float('infinity') for node_id in graph.nodes}
    distances[start_id] = 0
    
    # Track the path
    previous_nodes = {node_id: None for node_id in graph.nodes}

    while pq:
        current_dist, current_node_id = heapq.heappop(pq)

        if current_node_id == dest_id:
            break

        if current_dist > distances[current_node_id]:
            continue

        for edge in graph.edges.get(current_node_id, []):
            if accessible_only and not edge.is_accessible:
                continue

            neighbor = edge.target_id
            new_dist = current_dist + edge.weight

            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous_nodes[neighbor] = current_node_id
                heapq.heappush(pq, (new_dist, neighbor))

    # Reconstruct path
    path_nodes = []
    current = dest_id
    if distances[dest_id] == float('infinity'):
        return RouteResponse(path_found=False, total_distance=0, steps=[], path_coords=[])

    while current is not None:
        path_nodes.insert(0, current)
        current = previous_nodes[current]

    raw_path_coords = [{"x": graph.nodes[nid].x, "y": graph.nodes[nid].y, "floor": graph.nodes[nid].floor} for nid in path_nodes]

    # Generate instructions
    steps = []
    for i in range(len(path_nodes)):
        node = graph.nodes[path_nodes[i]]
        
        # 1. Find the next landmark ahead in the path
        next_landmark_node = None
        for j in range(i + 1, len(path_nodes)):
            candidate = graph.nodes[path_nodes[j]]
            if candidate.type != "corridor" and candidate.name:
                next_landmark_node = candidate
                break
        
        if not next_landmark_node and i < len(path_nodes) - 1:
            next_landmark_node = graph.nodes[path_nodes[-1]]
            
        has_valid_landmark = next_landmark_node and next_landmark_node.name
        node_name_safe = next_landmark_node.name if has_valid_landmark else ""
        node_name_hi_safe = (next_landmark_node.name_hi if next_landmark_node.name_hi else node_name_safe) if has_valid_landmark else ""
        
        # 2. Find nearest landmark to the CURRENT node if it's a corridor
        current_landmark_en = ""
        current_landmark_hi = ""
        if node.type == "corridor" and i > 0:
            for edge in graph.edges.get(node.id, []):
                adj = graph.nodes.get(edge.target_id)
                if adj and adj.type != "corridor" and adj.name:
                    current_landmark_en = f"Near {adj.name}, "
                    current_landmark_hi = f"{adj.name_hi if adj.name_hi else adj.name} के पास, "
                    break
        elif node.type != "corridor" and node.name:
            current_landmark_en = f"At {node.name}, "
            current_landmark_hi = f"{node.name_hi if node.name_hi else node.name} पर, "
            
        # Default instructions
        if i == 0:
            if node.name:
                instruction_en = f"Start at {node.name}"
                instruction_hi = f"{node.name_hi if node.name_hi else node.name} से शुरू करें"
            else:
                instruction_en = "Start here"
                instruction_hi = "यहाँ से शुरू करें"
        else:
            if has_valid_landmark:
                instruction_en = f"{current_landmark_en}go towards {node_name_safe}"
                instruction_hi = f"{current_landmark_hi}{node_name_hi_safe} की ओर जाएँ"
            else:
                instruction_en = f"{current_landmark_en}continue forward"
                instruction_hi = f"{current_landmark_hi}आगे बढ़ें"
        
        step_dist = 0
        if i > 0:
            prev_id = path_nodes[i-1]
            n1 = graph.nodes[prev_id]
            n2 = node
            
            # 1. Fetch edge distance and check for hardcoded floor changes
            for edge in graph.edges.get(prev_id, []):
                if edge.target_id == node.id:
                    step_dist = edge.weight
                    if n1.floor != n2.floor:
                        if edge.direction_en: instruction_en = edge.direction_en
                        if edge.direction_hi: instruction_hi = edge.direction_hi
                    elif i == len(path_nodes) - 1 and edge.direction_en and ("Enter" in edge.direction_en or "प्रवेश" in edge.direction_hi):
                        instruction_en = edge.direction_en
                        if edge.direction_hi: instruction_hi = edge.direction_hi
                    break
            
            # 2. Calculate dynamic left/right turns if on the same floor and we have a prev_prev node
            if i > 1 and n1.floor == n2.floor and i < len(path_nodes) - 1:
                prev_prev_id = path_nodes[i-2]
                n0 = graph.nodes[prev_prev_id]
                
                if n0.floor == n1.floor:
                    # Vector 1: n0 to n1
                    v1_x, v1_y = n1.x - n0.x, n1.y - n0.y
                    # Vector 2: n1 to n2
                    v2_x, v2_y = n2.x - n1.x, n2.y - n1.y
                    
                    cross_product = (v1_x * v2_y) - (v1_y * v2_x)
                    dot_product = (v1_x * v2_x) + (v1_y * v2_y)
                    
                    turn_en, turn_hi = "Go straight", "सीधे चलें"
                    if cross_product > 0.1:
                        turn_en, turn_hi = "Turn left", "बाएँ मुड़ें"
                    elif cross_product < -0.1:
                        turn_en, turn_hi = "Turn right", "दाएँ मुड़ें"
                    elif dot_product < 0:
                        turn_en, turn_hi = "Turn around", "पीछे मुड़ें"
                    
                    # Generate Landmark text if turning
                    if turn_en != "Go straight":
                        if has_valid_landmark:
                            instruction_en = f"{current_landmark_en}{turn_en.lower()} towards {node_name_safe}"
                            instruction_hi = f"{current_landmark_hi}{node_name_hi_safe} की ओर {turn_hi}"
                        else:
                            instruction_en = f"{current_landmark_en}{turn_en.lower()}"
                            instruction_hi = f"{current_landmark_hi}{turn_hi}"
                    else:
                        if has_valid_landmark:
                            instruction_en = f"{current_landmark_en}continue straight towards {node_name_safe}"
                            instruction_hi = f"{current_landmark_hi}{node_name_hi_safe} की ओर सीधे चलें"
                        else:
                            instruction_en = f"{current_landmark_en}continue straight"
                            instruction_hi = f"{current_landmark_hi}सीधे चलें"

        if i == len(path_nodes) - 1:
            dest_name = node.name if node.name else "destination"
            dest_name_hi = node.name_hi if node.name_hi else "मंज़िल"
            instruction_en = f"Arrive at {dest_name}"
            instruction_hi = f"{dest_name_hi} पर पहुँचें"
            
        steps.append(RouteStep(
            node_id=node.id,
            node_name=node.name,
            instruction_en=instruction_en,
            instruction_hi=instruction_hi,
            distance=step_dist,
            x=node.x,
            y=node.y,
            floor=node.floor
        ))

    # --- STEP CONSOLIDATION (GOOGLE MAPS STYLE) ---
    consolidated_steps = []
    for step in steps:
        if not consolidated_steps:
            consolidated_steps.append(step)
            continue
            
        last_step = consolidated_steps[-1]
        
        # If this step is just continuing straight, merge its distance into the last step
        # and update the instruction to point to the further landmark.
        # But NEVER merge floor changes or the final arrival step.
        is_straight = "continue straight" in step.instruction_en
        is_last_straight = "continue straight" in last_step.instruction_en or "Start at" in last_step.instruction_en or "Start here" in last_step.instruction_en
        is_floor_change = last_step.floor != step.floor
        is_arrival = "Arrive at" in step.instruction_en
        is_identical = step.instruction_en == last_step.instruction_en or step.instruction_hi == last_step.instruction_hi
        
        if (is_identical or (is_straight and is_last_straight)) and not is_floor_change and not is_arrival:
            last_step.distance += step.distance
            # Update the instruction so it points to the new further landmark if they are not identical
            if not is_identical:
                last_step.instruction_en = step.instruction_en
                last_step.instruction_hi = step.instruction_hi
            last_step.node_id = step.node_id
            last_step.x = step.x
            last_step.y = step.y
        else:
            consolidated_steps.append(step)
            
    steps = consolidated_steps
    # ---------------------------------------------

    return RouteResponse(
        path_found=True,
        total_distance=distances[dest_id],
        steps=steps,
        path_coords=raw_path_coords
    )
