import json
import sqlite3
import math
import sys

def build_graph():
    # Load JSON from standard input or file
    with open('user_graph.json', 'r') as f:
        data = json.load(f)
        
    conn = sqlite3.connect('backend/navcare.db')
    c = conn.cursor()
    
    # 1. Back up existing metadata
    meta_map = {}
    rows = c.execute("SELECT name, name_hi, keywords FROM nodes WHERE is_room = 1").fetchall()
    for row in rows:
        meta_map[row[0]] = {"name_hi": row[1], "keywords": row[2]}
        
    # 2. Build nodes dictionary
    nodes = {}
    
    for i, r in enumerate(data['rooms']):
        nid = f"r{i}"
        eng_name = r["name"].strip()
        nodes[nid] = {
            "id": nid,
            "x": (r["x"] / 100.0) * 3071.0,
            "y": (r["y"] / 100.0) * 2340.0,
            "is_room": True,
            "name": eng_name,
            "name_hi": meta_map.get(eng_name, {}).get("name_hi"),
            "keywords": meta_map.get(eng_name, {}).get("keywords")
        }
        
    for i, p in enumerate(data['paths']):
        nid = f"p{i}"
        nodes[nid] = {
            "id": nid,
            "x": (p["x"] / 100.0) * 3071.0,
            "y": (p["y"] / 100.0) * 2340.0,
            "is_room": False,
            "name": None,
            "name_hi": None,
            "keywords": None
        }

    # 3. Build edges
    edges = set()
    path_nodes = [n for n in nodes.values() if not n["is_room"]]
    
    # Tolerance for alignment (user was very accurate, but small floats might differ)
    TOL = 5.0 # pixels
    
    # A. Path to Path (Horizontal & Vertical Lines)
    for i in range(len(path_nodes)):
        for j in range(i + 1, len(path_nodes)):
            n1 = path_nodes[i]
            n2 = path_nodes[j]
            
            # Vertical edge
            if abs(n1["x"] - n2["x"]) < TOL:
                min_y = min(n1["y"], n2["y"])
                max_y = max(n1["y"], n2["y"])
                mid_x = (n1["x"] + n2["x"]) / 2
                
                # Check for blocker
                blocker = False
                for n3 in path_nodes:
                    if n3["id"] in (n1["id"], n2["id"]): continue
                    if abs(n3["x"] - mid_x) < TOL and min_y + TOL < n3["y"] < max_y - TOL:
                        blocker = True
                        break
                
                if not blocker:
                    edges.add((n1["id"], n2["id"]))
                    
            # Horizontal edge
            elif abs(n1["y"] - n2["y"]) < TOL:
                min_x = min(n1["x"], n2["x"])
                max_x = max(n1["x"], n2["x"])
                mid_y = (n1["y"] + n2["y"]) / 2
                
                # Check for blocker
                blocker = False
                for n3 in path_nodes:
                    if n3["id"] in (n1["id"], n2["id"]): continue
                    if abs(n3["y"] - mid_y) < TOL and min_x + TOL < n3["x"] < max_x - TOL:
                        blocker = True
                        break
                
                if not blocker:
                    edges.add((n1["id"], n2["id"]))
                    
    # B. Room to Path (Snap to closest)
    room_nodes = [n for n in nodes.values() if n["is_room"]]
    for r in room_nodes:
        closest = None
        min_dist = float('inf')
        for p in path_nodes:
            dist = math.hypot(r["x"] - p["x"], r["y"] - p["y"])
            if dist < min_dist:
                min_dist = dist
                closest = p
        
        if closest:
            edges.add((r["id"], closest["id"]))
            
    # 4. Save to Database
    c.execute("DELETE FROM edges")
    c.execute("DELETE FROM nodes")
    
    for n in nodes.values():
        c.execute("INSERT INTO nodes (id, x, y, floor, is_room, name, name_hi, keywords) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (n["id"], n["x"], n["y"], 0, 1 if n["is_room"] else 0, n["name"], n["name_hi"], n["keywords"]))
                  
    for e in edges:
        n1 = nodes[e[0]]
        n2 = nodes[e[1]]
        dist = math.hypot(n1["x"] - n2["x"], n1["y"] - n2["y"])
        
        c.execute("INSERT INTO edges (from_id, to_id, distance) VALUES (?, ?, ?)", (n1["id"], n2["id"], dist))
        c.execute("INSERT INTO edges (from_id, to_id, distance) VALUES (?, ?, ?)", (n2["id"], n1["id"], dist))
        
    conn.commit()
    print(f"Successfully built graph! Nodes: {len(nodes)}, Edges (bidirectional): {len(edges) * 2}")
    
if __name__ == '__main__':
    build_graph()
