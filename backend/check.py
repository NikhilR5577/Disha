import sqlite3
conn = sqlite3.connect('navcare.db')
c = conn.cursor()
c.execute('SELECT id, name, x, y, is_room FROM nodes')
nodes = {row[0]: {'name': row[1], 'x': row[2], 'y': row[3], 'is_room': row[4]} for row in c.fetchall()}

c.execute('SELECT id, from_id, to_id, distance FROM edges')
edges = c.fetchall()

for edge in edges:
    e_id, f_id, t_id, dist = edge
    n1 = nodes.get(f_id)
    n2 = nodes.get(t_id)
    if not n1 or not n2: continue
    
    if n1['is_room'] == 0 and n2['is_room'] == 0:
        dx = abs(n1['x'] - n2['x'])
        dy = abs(n1['y'] - n2['y'])
        if dx > 10 and dy > 10:
            print(f'DIAGONAL CORRIDOR EDGE {e_id}: {f_id} -> {t_id} | dx={dx:.1f} dy={dy:.1f}')
