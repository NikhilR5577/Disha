from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.services.graph_service import get_graph_from_db
from app.services.routing.pathfinder import find_shortest_path, RouteResponse
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class NodeResponse(BaseModel):
    id: str
    name: Optional[str] = None
    name_hi: Optional[str] = None
    x: float
    y: float
    floor: int
    is_room: Optional[bool] = None

@router.get("/locations", response_model=List[NodeResponse])
def get_locations(db: Session = Depends(get_db)):
    """Return a list of all locations to populate frontend dropdowns."""
    graph = get_graph_from_db(db)
    return [{"id": n.id, "name": n.name, "name_hi": n.name_hi, "x": n.x, "y": n.y, "floor": n.floor, "is_room": getattr(n, 'is_room', None)} for n in graph.nodes.values()]

@router.get("/route", response_model=RouteResponse)
def get_route(
    start: str = Query(..., description="Starting location ID"),
    destination: str = Query(..., description="Destination location ID"),
    accessible: bool = Query(False, description="Whether to only use wheelchair accessible routes"),
    db: Session = Depends(get_db)
):
    """Calculate shortest path between start and destination."""
    graph = get_graph_from_db(db)
    if start not in graph.nodes:
        raise HTTPException(status_code=404, detail="Start node not found")
    if destination not in graph.nodes:
        raise HTTPException(status_code=404, detail="Destination node not found")
        
    route = find_shortest_path(graph, start, destination, accessible_only=accessible)
    if not route.path_found:
        raise HTTPException(status_code=404, detail="No path found between these locations")
        
    return route

from app.services.search import search_destination

@router.get("/search", response_model=Optional[NodeResponse])
def search(q: str = Query(..., description="The voice query text"), db: Session = Depends(get_db)):
    match = search_destination(q, db)
    if match:
        return {"id": match.id, "name": match.name, "name_hi": match.name_hi, "x": match.x, "y": match.y, "floor": match.floor, "is_room": match.is_room}
    return None

from app.models.schema import AnalyticsEventDB
from sqlalchemy import func
from datetime import datetime

class TrackEvent(BaseModel):
    event_type: str
    session_id: str

@router.post('/analytics/track')
def track_event(event: TrackEvent, db: Session = Depends(get_db)):
    db_event = AnalyticsEventDB(event_type=event.event_type, session_id=event.session_id)
    db.add(db_event)
    db.commit()
    return {'status': 'ok'}

@router.get('/analytics/stats')
def get_stats(db: Session = Depends(get_db)):
    total_users = db.query(func.count(func.distinct(AnalyticsEventDB.session_id))).scalar() or 0
    first_day_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_users = db.query(func.count(func.distinct(AnalyticsEventDB.session_id))).filter(AnalyticsEventDB.timestamp >= first_day_of_month).scalar() or 0
    first_event = db.query(func.min(AnalyticsEventDB.timestamp)).scalar()
    avg_per_month = total_users
    if first_event:
        delta = datetime.utcnow() - first_event
        months = max(1, delta.days / 30.44)
        avg_per_month = round(total_users / months)
    return {'total_unique_users': total_users, 'users_this_month': monthly_users, 'average_users_per_month': avg_per_month}

