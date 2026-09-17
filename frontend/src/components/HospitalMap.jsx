import React, { useRef, useEffect } from 'react';
import { TransformWrapper, TransformComponent } from 'react-zoom-pan-pinch';

const SVG_W = 1024;
const SVG_H = 1142;
const PADDING = 50; // SVG units of padding around the route bounding box

const HospitalMap = ({ locations, route }) => {
  // SVG coordinates map to the absolute pixel size of the original SVG
  const viewBox = `0 0 ${SVG_W} ${SVG_H}`;
  const mapImage = "/map_final.svg?v=4";
  const currentLocations = locations;

  // Use raw path coordinates for drawing the line so it doesn't cut through corners,
  // fallback to route.steps for backward compatibility with older API versions.
  const currentFloorSteps = route?.path_coords || route?.steps || [];
  const routePoints = currentFloorSteps.map(node => `${node.x},${node.y}`).join(' ');

  // Calculate dynamic duration based on the distance (min 15s, max 45s) for a realistic GPS illusion
  const floorDistance = currentFloorSteps.reduce((sum, step) => sum + (step.distance || 0), 0);
  const animationDur = floorDistance > 0 ? Math.max(15, Math.min(45, floorDistance / 80)) : 15;

  // Refs for auto-zoom to fit route
  const transformRef = useRef(null);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!route || currentFloorSteps.length < 2 || !transformRef.current || !containerRef.current) return;

    // Give the DOM a moment to settle before reading dimensions
    const timer = setTimeout(() => {
      const xs = currentFloorSteps.map(n => n.x);
      const ys = currentFloorSteps.map(n => n.y);
      const minX = Math.max(0, Math.min(...xs) - PADDING);
      const maxX = Math.min(SVG_W, Math.max(...xs) + PADDING);
      const minY = Math.max(0, Math.min(...ys) - PADDING);
      const maxY = Math.min(SVG_H, Math.max(...ys) + PADDING);

      const container = containerRef.current;
      const containerW = container.clientWidth;
      const containerH = container.clientHeight;

      // SVG unit → pixel ratio (preserveAspectRatio="none" means it stretches to fill)
      const svgToPxX = containerW / SVG_W;
      const svgToPxY = containerH / SVG_H;

      // Bounding box dimensions in pixels (at scale=1)
      const bboxW = (maxX - minX) * svgToPxX;
      const bboxH = (maxY - minY) * svgToPxY;

      // Scale to fit the bounding box with a little breathing room
      const scale = Math.min(containerW / bboxW, containerH / bboxH, 4) * 0.9;

      // Center of the bounding box in pixels (at scale=1)
      const centerXPx = ((minX + maxX) / 2) * svgToPxX;
      const centerYPx = ((minY + maxY) / 2) * svgToPxY;

      // Translate so the bounding box center lands in the middle of the container
      const posX = containerW / 2 - centerXPx * scale;
      const posY = containerH / 2 - centerYPx * scale;

      transformRef.current.setTransform(posX, posY, scale, 600, 'easeOut');
    }, 150);

    return () => clearTimeout(timer);
  }, [route]);

  return (
    <div ref={containerRef} className="relative w-full h-full overflow-hidden bg-white shadow-sm flex items-center justify-center">
      <TransformWrapper
        ref={transformRef}
        initialScale={1}
        minScale={0.5}
        maxScale={4}
        centerOnInit={true}
        wheel={{ step: 0.1 }}
      >
        <TransformComponent wrapperClass="!w-full !h-full" contentClass="!w-full !h-full flex items-center justify-center">
          {/* This wrapper ensures the SVG and IMG exactly match dimensions */}
          <div className="relative max-w-full max-h-full">
            <img 
              src={mapImage} 
              alt={`Disha Demo Map`}
              className="max-w-full max-h-full w-auto h-auto opacity-95 pointer-events-none select-none block"
            />
            
            {/* Overlay SVG for plotting points and lines */}
            <svg 
              viewBox={viewBox} 
              className="absolute top-0 left-0 w-full h-full"
              preserveAspectRatio="none"
            >
              <defs>
                <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                  <feGaussianBlur stdDeviation="15" result="blur" />
                  <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
              </defs>

              {/* Draw Route Line */}
              {routePoints && currentFloorSteps.length > 1 && (
                <>
                  {/* Outer shadow/glow line */}
                  <polyline
                    points={routePoints}
                    fill="none"
                    stroke="#FDBA74"
                    strokeWidth="45"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    opacity="0.4"
                  />
                  {/* Inner solid line */}
                  <polyline
                    points={routePoints}
                    fill="none"
                    stroke="#F97316"
                    strokeWidth="18"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                  {/* Animated dotted path to show direction */}
                  <polyline
                    points={routePoints}
                    fill="none"
                    stroke="#ffffff"
                    strokeWidth="6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeDasharray="15,30"
                    className="animate-dash"
                  />
                  
                  {/* Blue Dot Tracking */}
                  <circle key={routePoints} r="15" fill="#F97316" stroke="#ffffff" strokeWidth="4">
                    <animateMotion
                      key={`anim-${routePoints}`}
                      dur={`${animationDur}s`}
                      repeatCount="indefinite"
                      path={currentFloorSteps.map((n, i) => `${i === 0 ? 'M' : 'L'} ${n.x},${n.y}`).join(' ')}
                    />
                  </circle>
                </>
              )}

              {/* Draw Nodes - Only show Start and End to keep map clean */}
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
  );
};

export default HospitalMap;
