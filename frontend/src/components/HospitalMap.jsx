import React, { useState, useEffect } from 'react';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';

const SVG_W = 1024;
const SVG_H = 571;

const HospitalMap = ({ locations, route }) => {
  const [activeFloor, setActiveFloor] = useState(1);
  const viewBox = `0 0 ${SVG_W} ${SVG_H}`;
  const mapImage = activeFloor === 1 ? "/ground_floor.png" : "/first_floor.png";
  
  // Filter nodes/locations by floor
  const currentLocations = locations.filter(loc => loc.floor === activeFloor || loc.floor === undefined);

  // Filter route points to only show those on the currently active floor
  const allFloorSteps = route?.path_coords || route?.steps || [];
  const currentFloorSteps = allFloorSteps.filter(node => node.floor === activeFloor || node.floor === undefined);
  const routePoints = currentFloorSteps.map(node => `${node.x},${node.y}`).join(' ');

  // Switch to the floor of the start location when a new route is loaded
  useEffect(() => {
    if (allFloorSteps.length > 0) {
      const firstStep = allFloorSteps[0];
      if (firstStep.floor) {
        setActiveFloor(firstStep.floor);
      }
    }
  }, [route]);

  // Animation speed: dot completes the full route in T/4 time, where T is the estimated walking time
  // Walking time formula (same as App.jsx): T = total_distance * 0.063 / 84 minutes
  // For per-floor display, scale by the ratio of this floor's pixel distance to total pixel distance
  const allSteps = route?.path_coords || route?.steps || [];
  
  const calcPixelDist = (steps) => {
    let d = 0;
    for (let i = 1; i < steps.length; i++) {
      const dx = steps[i].x - steps[i-1].x;
      const dy = steps[i].y - steps[i-1].y;
      d += Math.sqrt(dx * dx + dy * dy);
    }
    return d;
  };
  
  const totalPixelDist = calcPixelDist(allSteps);
  const floorPixelDist = calcPixelDist(currentFloorSteps);
  const walkingTimeMinutes = route?.total_distance ? (route.total_distance * 0.063 / 84) : 0;
  const totalAnimDur = walkingTimeMinutes > 0 ? (walkingTimeMinutes * 60) / 4 : 15;
  const floorRatio = totalPixelDist > 0 ? floorPixelDist / totalPixelDist : 1;
  const animationDur = Math.max(3, Math.min(30, totalAnimDur * floorRatio));

  return (
    <div className="relative w-full h-full overflow-hidden bg-[#e5e7eb] shadow-sm flex items-center justify-center p-4">
      
      {/* Floating Floor Switcher Buttons (Moved to Top) */}
      <div className="absolute top-4 left-1/2 transform -translate-x-1/2 flex bg-white rounded-full shadow-lg border border-slate-200 p-1 z-50">
        <button 
          onClick={() => setActiveFloor(1)}
          className={`px-6 py-2 rounded-full text-sm font-semibold transition-colors focus:outline-none ${activeFloor === 1 ? 'bg-orange-500 text-white' : 'hover:bg-orange-50 hover:text-orange-600'}`}
        >
          Ground Floor
        </button>
        <button 
          onClick={() => setActiveFloor(2)}
          className={`px-6 py-2 rounded-full text-sm font-semibold transition-colors focus:outline-none ${activeFloor === 2 ? 'bg-orange-500 text-white' : 'hover:bg-orange-50 hover:text-orange-600'}`}
        >
          First Floor
        </button>
      </div>

      <div className="relative shadow-2xl rounded-lg overflow-hidden w-full h-full bg-white">
        <TransformWrapper
          initialScale={1}
          minScale={0.5}
          maxScale={4}
          centerOnInit={true}
          wheel={{ step: 0.1 }}
        >
          <TransformComponent wrapperClass="!w-full !h-full" contentClass="!w-full !h-full flex items-center justify-center">
            <div className="relative" style={{ width: '100%', height: 'auto', aspectRatio: `${SVG_W}/${SVG_H}`, maxWidth: '100%', maxHeight: '100%', backgroundColor: '#fff' }}>
              
              <img src={mapImage} alt={`Floor ${activeFloor}`} className="absolute top-0 left-0 w-full h-full object-cover block pointer-events-none select-none opacity-95" />
              
              <svg viewBox={viewBox} className="absolute top-0 left-0 w-full h-full" preserveAspectRatio="none">
                <defs>
                  <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="15" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                  </filter>
                </defs>

                <rect x="250" y="20" width="550" height="90" fill="#ffffff" />
                <text x="512" y="70" fontFamily="sans-serif" fontSize="42" fontWeight="900" fill="#F97316" textAnchor="middle">
                  Disha - {activeFloor === 1 ? 'Ground Floor' : 'First Floor'}
                </text>

                {routePoints && currentFloorSteps.length > 1 && (
                  <>
                    <polyline points={routePoints} fill="none" stroke="#FDBA74" strokeWidth="45" strokeLinecap="round" strokeLinejoin="round" opacity="0.4" />
                    <polyline points={routePoints} fill="none" stroke="#F97316" strokeWidth="18" strokeLinecap="round" strokeLinejoin="round" />
                    <polyline points={routePoints} fill="none" stroke="#ffffff" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round" strokeDasharray="15,30" className="animate-dash" />
                    
                    <circle key={routePoints} r="15" fill="#F97316" stroke="#ffffff" strokeWidth="4">
                      <animateMotion key={`anim-${routePoints}`} dur={`${animationDur}s`} repeatCount="indefinite" path={currentFloorSteps.map((n, i) => `${i === 0 ? 'M' : 'L'} ${n.x},${n.y}`).join(' ')} />
                    </circle>
                  </>
                )}

                {currentLocations.map((loc) => {
                  const startNodeId = route?.steps?.[0]?.node_id;
                  const destNodeId = route?.steps?.[route.steps.length - 1]?.node_id;
                  
                  const isStart = loc.id === startNodeId;
                  const isDest = loc.id === destNodeId;
                  
                  if (!isStart && !isDest) return null;

                  return (
                    <circle
                      key={loc.id}
                      cx={loc.x}
                      cy={loc.y}
                      r="24"
                      fill={isStart ? '#22C55E' : '#EF4444'}
                      stroke="#fff"
                      strokeWidth="6"
                      className="shadow-xl transition-all duration-300"
                    >
                      <title>{loc.name}</title>
                    </circle>
                  );
                })}
              </svg>
            </div>
          </TransformComponent>
        </TransformWrapper>
      </div>
    </div>
  );
};

export default HospitalMap;
