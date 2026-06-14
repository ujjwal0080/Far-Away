import React, { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Activity, Package, Truck, Zap, BrainCircuit, X, Droplets, Utensils, CupSoda } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import './index.css';

const createIcon = (className) => L.divIcon({ className, iconSize: [20, 20], iconAnchor: [10, 10] });
const healthyIcon = createIcon('store-marker-healthy');
const sinkIcon = createIcon('store-marker-sink');
const sourceIcon = createIcon('store-marker-source');
const driverIcon = L.divIcon({ className: 'driver-marker', iconSize: [16, 16], iconAnchor: [8, 8] });

const BANGALORE_CENTER = [12.9716, 77.5946];

const poissonPmf = (k, lambda) => {
  let fact = 1;
  for(let i=1; i<=k; i++) fact *= i;
  return (Math.pow(lambda, k) * Math.exp(-lambda)) / fact;
};

const ProductIcon = ({ name }) => {
  if (name === "Daily Essentials") return <Droplets size={14} color="#3b82f6" />;
  if (name === "Match Day Snacks") return <Utensils size={14} color="#f59e0b" />;
  if (name === "Cold Beverages") return <CupSoda size={14} color="#10b981" />;
  return <Package size={14} />;
};

function App() {
  const [gameState, setGameState] = useState({ stores: {}, drivers: [], routes: [], ghost_routes: [], insights: [] });
  const [isConnected, setIsConnected] = useState(false);
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedProduct, setSelectedProduct] = useState("Match Day Snacks");

  const chartData = React.useMemo(() => {
    if (!selectedNode || !gameState.stores[selectedNode]) return [];
    const prod = gameState.stores[selectedNode].products[selectedProduct];
    if (!prod) return [];
    const data = [];
    for (let k = 0; k <= Math.max(30, prod.lambda * 2); k++) {
      data.push({ k: k, probability: (poissonPmf(k, prod.lambda) * 100).toFixed(2) });
    }
    return data;
  }, [selectedNode, selectedProduct, gameState.stores]);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onmessage = (event) => setGameState(JSON.parse(event.data));
    return () => ws.close();
  }, []);

  const getIconForStatus = (status) => {
    if (status === 'SINK') return sinkIcon;
    if (status === 'SOURCE') return sourceIcon;
    return healthyIcon;
  };

  return (
    <div className="dashboard-container">
      <div className="sidebar custom-scrollbar">
        <h1><Zap size={24} color="#8b5cf6" /> <span>Zepto</span> Optimizer</h1>
        
        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Activity size={18} color={isConnected ? '#10b981' : '#ef4444'} />
            <span style={{ fontWeight: 600 }}>System Status</span>
          </div>
          <div style={{ color: 'var(--text-muted)', fontSize: '14px' }}>
            {isConnected ? 'Engine Online - VRPTW Active' : 'Reconnecting to Engine...'}
          </div>
        </div>

        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <Package size={18} color="#8b5cf6" />
            <span style={{ fontWeight: 600 }}>Network Nodes (Max Risk)</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {Object.entries(gameState.stores || {}).map(([id, data]) => (
              <div key={id} style={{ display: 'flex', flexDirection: 'column', fontSize: '14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span style={{ color: data.status === 'SINK' ? '#ef4444' : 'var(--text-main)', cursor: 'pointer', fontWeight: 600 }} onClick={() => setSelectedNode(id)}>
                    {id.replace('Store_', '')}
                  </span>
                  <span style={{ color: 'var(--text-muted)' }}>{(data.stockout_prob * 100).toFixed(0)}% Risk</span>
                </div>
                <div style={{ width: '100%', height: '4px', backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: '2px', overflow: 'hidden' }}>
                  <div style={{ 
                    height: '100%', width: `${Math.min(100, data.stockout_prob * 100)}%`, 
                    backgroundColor: data.status === 'SINK' ? '#ef4444' : (data.stockout_prob > 0.5 ? '#f59e0b' : '#10b981'),
                    transition: 'width 0.5s ease-in-out'
                  }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="glass-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
            <BrainCircuit size={18} color="#8b5cf6" />
            <span style={{ fontWeight: 600 }}>AI Supervisor Log</span>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px', color: 'var(--text-main)', maxHeight: '350px', overflowY: 'auto' }} className="custom-scrollbar">
            {gameState.insights?.map((insight, idx) => (
              <div key={idx} style={{ padding: '8px', backgroundColor: 'rgba(139, 92, 246, 0.1)', borderRadius: '6px', borderLeft: '3px solid #8b5cf6', lineHeight: '1.4' }}>
                {insight}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="map-container">
        <MapContainer center={BANGALORE_CENTER} zoom={12} zoomControl={false} style={{ height: '100%', width: '100%' }}>
          <TileLayer attribution='&copy; Carto' url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png" />
          
          {Object.entries(gameState.stores || {}).map(([id, data]) => (
            <Marker key={id} position={data.coords} icon={getIconForStatus(data.status)} eventHandlers={{ click: () => setSelectedNode(id) }}>
              <Tooltip direction="top" offset={[0, -10]} opacity={1}>
                <span style={{ fontWeight: 'bold' }}>{id.replace('Store_', '')}</span><br/>
                <span style={{ color: data.status === 'SINK' ? '#ef4444' : 'inherit' }}>Max Risk: {(data.stockout_prob*100).toFixed(0)}%</span>
              </Tooltip>
            </Marker>
          ))}

          {gameState.drivers?.map((driver, index) => (
            <Marker key={`driver-${index}`} position={driver.coords} icon={driverIcon}>
              <Tooltip direction="bottom" offset={[0, 10]} opacity={1}><strong>Agent {driver.id}</strong></Tooltip>
            </Marker>
          ))}

          {/* Ghost Routes */}
          {gameState.ghost_routes?.map((routeCoords, idx) => (
            <Polyline key={`ghost-${idx}`} positions={routeCoords} color="#f59e0b" weight={2} dashArray="4, 8" opacity={0.5} className="animated-polyline" />
          ))}

          {/* Active Routes */}
          {gameState.routes?.map((routeCoords, idx) => (
            <Polyline key={`route-${idx}`} positions={routeCoords} color="#8b5cf6" weight={3} dashArray="8, 12" className="animated-polyline" />
          ))}
        </MapContainer>

        {/* Node Inspector Overlay */}
        {selectedNode && gameState.stores[selectedNode] && (
          <div className="inspector-panel">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2 style={{ margin: 0, fontSize: '18px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Package size={18} color="#8b5cf6" />
                {selectedNode.replace('Store_', '')}
              </h2>
              <button className="close-btn" onClick={() => setSelectedNode(null)}><X size={20} /></button>
            </div>
            
            {/* Product Tabs */}
            <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '12px' }}>
              {Object.keys(gameState.stores[selectedNode].products).map(prod => (
                <button 
                  key={prod}
                  onClick={() => setSelectedProduct(prod)}
                  style={{
                    background: selectedProduct === prod ? 'rgba(139, 92, 246, 0.2)' : 'transparent',
                    border: 'none', color: selectedProduct === prod ? '#8b5cf6' : 'var(--text-muted)',
                    padding: '6px 10px', borderRadius: '6px', cursor: 'pointer', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px'
                  }}
                >
                  <ProductIcon name={prod} />
                </button>
              ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div style={{ background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '8px' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>Stock: {selectedProduct}</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{gameState.stores[selectedNode].products[selectedProduct].stock}</div>
              </div>
              <div style={{ background: 'rgba(0,0,0,0.2)', padding: '12px', borderRadius: '8px' }}>
                <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>λ (Orders/Tick)</div>
                <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#8b5cf6' }}>{gameState.stores[selectedNode].products[selectedProduct].lambda.toFixed(1)}</div>
              </div>
            </div>

            <div style={{ marginTop: '8px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
                <span style={{ fontSize: '13px', fontWeight: 600 }}>Stockout Probability Math</span>
              </div>
              
              <div style={{ height: '180px', width: '100%', marginLeft: '-15px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="colorProb" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="k" stroke="rgba(255,255,255,0.2)" fontSize={11} tick={{fill: '#8e8e9e'}} tickLine={false} />
                    <YAxis stroke="rgba(255,255,255,0.2)" fontSize={11} tick={{fill: '#8e8e9e'}} tickLine={false} axisLine={false} />
                    <RechartsTooltip 
                      contentStyle={{ backgroundColor: '#15151a', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                      itemStyle={{ color: '#f0f0f5' }}
                      labelStyle={{ color: '#8e8e9e' }}
                      formatter={(value) => [`${value}%`, 'Probability']}
                      labelFormatter={(label) => `Demand (k): ${label}`}
                    />
                    <Area type="monotone" dataKey="probability" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#colorProb)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <div style={{ textAlign: 'center', fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                Cumulative Poisson P(X &gt; Stock)
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;