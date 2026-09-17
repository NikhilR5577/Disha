
import sqlite3

conn = sqlite3.connect('navcare.db')
c = conn.cursor()

c.execute('SELECT id, name, x, y FROM nodes')
nodes = {row[0]: {'name': row[1], 'x': row[2], 'y': row[3]} for row in c.fetchall()}

c.execute('SELECT id, from_id, to_id, distance FROM edges')
edges = c.fetchall()

for edge in edges:
    e_id, f_id, t_id, dist = edge
    n1 = nodes.get(f_id)
    n2 = nodes.get(t_id)
    if not n1 or not n2: continue
    
    # We only care if BOTH are path/corridor nodes.
    # Usually they have names like 'corridor' or start with 'p' or have no name
    if (f_id.startswith('p') or f_id.startswith('c')) and (t_id.startswith('p') or t_id.startswith('c')):
        dx = abs(n1['x'] - n2['x'])
        dy = abs(n1['y'] - n2['y'])
        
        # A true orthogonal corridor edge should have dx ~0 or dy ~0
        # If both are > 10, it's a diagonal path!
        if dx > 10 and dy > 10:
            print(f'Corridor Diagonal Edge ID {e_id}: {f_id} -> {t_id} | dx={dx} dy={dy} dist={dist}')

