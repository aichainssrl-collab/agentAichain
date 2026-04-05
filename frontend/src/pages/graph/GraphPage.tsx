import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import apiClient from '@/lib/api/client';
import ForceGraph2D, { ForceGraphMethods } from 'react-force-graph-2d';
import { RefreshCw, Maximize, ZoomIn, ZoomOut } from 'lucide-react';

interface GraphData {
  nodes: {
    id: string;
    label: string;
    name: string;
    role?: string;
  }[];
  links: {
    source: string;
    target: string;
    label: string;
  }[];
}

const GraphPage: React.FC = () => {
  const fgRef = useRef<ForceGraphMethods>();
  const [containerDimensions, setContainerDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef<HTMLDivElement>(null);

  const { data, isLoading, isError, refetch } = useQuery<GraphData>({
    queryKey: ['tenant-graph'],
    queryFn: async () => {
      const data = await apiClient.request<GraphData>('/graph/tenant');
      return data;
    },
  });

  // Update dimensions on window resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setContainerDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };
    
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Fit graph to view when data loads
  useEffect(() => {
    if (data && data.nodes.length > 0 && fgRef.current) {
      setTimeout(() => {
        fgRef.current?.zoomToFit(400, 50);
      }, 500);
    }
  }, [data]);

  const getNodeColor = (node: any) => {
    switch (node.label) {
      case 'Tenant': return '#3b82f6'; // blue
      case 'Team': return '#10b981'; // green
      case 'Agent': return '#8b5cf6'; // light blue/purple
      case 'Tool': return '#f59e0b'; // yellow/orange
      default: return '#9ca3af'; // gray
    }
  };

  const getNodeSize = (node: any) => {
    switch (node.label) {
      case 'Tenant': return 10;
      case 'Team': return 8;
      case 'Agent': return 6;
      case 'Tool': return 4;
      default: return 5;
    }
  };

  const handleZoomIn = useCallback(() => {
    if (fgRef.current) {
      const currentZoom = fgRef.current.zoom();
      fgRef.current.zoom(currentZoom * 1.5, 400);
    }
  }, []);

  const handleZoomOut = useCallback(() => {
    if (fgRef.current) {
      const currentZoom = fgRef.current.zoom();
      fgRef.current.zoom(currentZoom / 1.5, 400);
    }
  }, []);

  const handleFit = useCallback(() => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(400, 50);
    }
  }, []);

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)]">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Neural Network</h1>
          <p className="text-sm text-gray-500 mt-1">
            Visualizzazione in tempo reale dell'architettura e delle relazioni del tuo ecosistema AI.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => refetch()}
            className="flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Aggiorna
          </button>
        </div>
      </div>

      <div 
        className="flex-1 bg-gray-900 rounded-xl overflow-hidden relative shadow-inner border border-gray-800"
        ref={containerRef}
      >
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900 bg-opacity-75 z-10">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
          </div>
        )}
        
        {isError && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900 z-10">
            <div className="text-red-400 bg-red-900 bg-opacity-20 p-4 rounded-lg border border-red-800">
              Errore nel caricamento del grafo. Assicurati che Neo4j sia attivo.
            </div>
          </div>
        )}

        {/* Floating controls */}
        <div className="absolute bottom-6 right-6 flex flex-col gap-2 z-10">
          <button 
            onClick={handleZoomIn}
            className="p-2 bg-gray-800 text-gray-300 hover:text-white hover:bg-gray-700 rounded-full shadow-lg border border-gray-700 transition-colors"
            title="Zoom In"
          >
            <ZoomIn size={20} />
          </button>
          <button 
            onClick={handleFit}
            className="p-2 bg-gray-800 text-gray-300 hover:text-white hover:bg-gray-700 rounded-full shadow-lg border border-gray-700 transition-colors"
            title="Adatta alla vista"
          >
            <Maximize size={20} />
          </button>
          <button 
            onClick={handleZoomOut}
            className="p-2 bg-gray-800 text-gray-300 hover:text-white hover:bg-gray-700 rounded-full shadow-lg border border-gray-700 transition-colors"
            title="Zoom Out"
          >
            <ZoomOut size={20} />
          </button>
        </div>

        {/* Legend */}
        <div className="absolute top-6 left-6 bg-gray-800 bg-opacity-80 p-4 rounded-lg border border-gray-700 shadow-lg z-10 backdrop-blur-sm">
          <h3 className="text-white text-sm font-semibold mb-3">Legenda Nodi</h3>
          <div className="space-y-2">
            <div className="flex items-center">
              <div className="w-3 h-3 rounded-full bg-[#3b82f6] mr-2 shadow-[0_0_8px_#3b82f6]"></div>
              <span className="text-gray-300 text-xs">Tenant</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 rounded-full bg-[#10b981] mr-2 shadow-[0_0_8px_#10b981]"></div>
              <span className="text-gray-300 text-xs">Team</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 rounded-full bg-[#8b5cf6] mr-2 shadow-[0_0_8px_#8b5cf6]"></div>
              <span className="text-gray-300 text-xs">Agente</span>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 rounded-full bg-[#f59e0b] mr-2 shadow-[0_0_8px_#f59e0b]"></div>
              <span className="text-gray-300 text-xs">Tool / Skill</span>
            </div>
          </div>
        </div>

        {data && (
          <ForceGraph2D
            ref={fgRef}
            width={containerDimensions.width}
            height={containerDimensions.height}
            graphData={data}
            nodeLabel="name"
            nodeColor={getNodeColor}
            nodeVal={getNodeSize}
            linkColor={() => 'rgba(255,255,255,0.2)'}
            linkWidth={1.5}
            linkDirectionalParticles={2}
            linkDirectionalParticleWidth={2}
            linkDirectionalParticleSpeed={0.005}
            d3AlphaDecay={0.01}
            d3VelocityDecay={0.08}
            cooldownTime={3000}
            nodeCanvasObject={(node: any, ctx, globalScale) => {
              const label = node.name;
              const fontSize = 12 / globalScale;
              ctx.font = `${fontSize}px Sans-Serif`;
              const textWidth = ctx.measureText(label).width;
              const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.2);

              ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
              ctx.fillRect(
                node.x - bckgDimensions[0] / 2,
                node.y - bckgDimensions[1] / 2 + 10,
                bckgDimensions[0],
                bckgDimensions[1]
              );

              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
              ctx.fillText(label, node.x, node.y + 10);

              // Draw circle
              ctx.beginPath();
              ctx.arc(node.x, node.y, getNodeSize(node), 0, 2 * Math.PI, false);
              ctx.fillStyle = getNodeColor(node);
              
              // Add glow effect
              ctx.shadowColor = getNodeColor(node);
              ctx.shadowBlur = 10;
              ctx.fill();
              
              // Reset shadow
              ctx.shadowBlur = 0;
            }}
          />
        )}
      </div>
    </div>
  );
};

export default GraphPage;
