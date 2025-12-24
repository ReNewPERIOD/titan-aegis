import { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, BarChart, Bar, Cell, XAxis, YAxis, ResponsiveContainer, ReferenceLine, Tooltip, CartesianGrid } from 'recharts';
import { Activity, TrendingUp, TrendingDown, Zap, Shield, AlertTriangle } from 'lucide-react';
import './App.css';

const API_URL = 'https://titan-backend-rl21.onrender.com';

function App() {
  const [market, setMarket] = useState(null);
  const [simPaths, setSimPaths] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  // Khởi tạo đúng cấu trúc mới
  const [volatilityData, setVolatilityData] = useState({ chart: [], stats: null });

  const fetchData = async () => {
    try {
      const [marketRes, simRes, logsRes, volRes] = await Promise.all([
        axios.get(`${API_URL}/market-data`),
        axios.get(`${API_URL}/simulation-paths`),
        axios.get(`${API_URL}/trade-logs`),
        axios.get(`${API_URL}/volatility-analysis`)
      ]);

      setMarket(marketRes.data);

      if (simRes.data.paths) {
        const formattedPaths = simRes.data.paths[0].map((_, index) => {
          let point = { index };
          simRes.data.paths.forEach((path, i) => { point[`path_${i}`] = path[index]; });
          point.mean = simRes.data.mean_path[index];
          return point;
        });
        setSimPaths(formattedPaths);
      }
      setLogs(logsRes.data);
      
      // Xử lý dữ liệu Volatility (Quan trọng)
      if (volRes.data && volRes.data.stats) {
        setVolatilityData(volRes.data);
      }
      
      setLoading(false);
    } catch (err) {
      console.error("Kết nối thất bại:", err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="loading-screen">CONNECTING TO TITAN SERVER...</div>;

  return (
    <div className="dashboard-container">
      {/* SIDEBAR TRÁI */}
      <aside className="sidebar">
        <div className="logo-section">
          <Shield color="#00ff41"/> <span>TITAN OS</span>
        </div>
        
        <div>
          <h2>Analysis Config</h2>
          <div className="control-group">
            <label className="label">Timeframe</label>
            <select className="control-input">
              <option>15 Minute</option>
              <option>1 Hour</option>
              <option>4 Hour</option>
            </select>
          </div>
          <div className="control-group" style={{marginTop:15}}>
            <label className="label">Volatility Method</label>
            <select className="control-input">
              <option>ATR (Standard)</option>
              <option>Bollinger Band</option>
            </select>
          </div>
        </div>

        <div>
          <h2>Risk Manager</h2>
          <div className="control-group">
            <label className="label">Max Risk / Trade</label>
            <div style={{display:'flex', gap:5}}>
               <input type="range" className="control-input" style={{flex:1}} />
            </div>
          </div>
        </div>
      </aside>
      
      {/* NỘI DUNG CHÍNH (Phải) */}
      <main className="content-area">
        {/* HEADER */}
        <header className="header">
          <div className="logo-section">
            <Shield className="logo-icon" size={28} />
            <div>
              <h1>TITAN AEGIS <span style={{color:'var(--neon-yellow)'}}>V7</span></h1>
            </div>
          </div>
          <div className="status-badge online">
            <div className="dot"></div> SYSTEM ONLINE
          </div>
        </header>

        {/* STATS ROW */}
        {market && (
          <div className="stats-grid">
            {/* Thẻ 1: Giá hiện tại */}
            <div className="stat-card pro-card">
              <div className="label">CURRENT PRICE</div>
              <div className="value" style={{color: '#fff'}}>
                 ${market ? market.price.toLocaleString() : '---'}
              </div>
              <div className="sub-label">BTC/USDT</div>
            </div>

            {/* Thẻ 2: Average Intraday */}
            <div className="stat-card pro-card">
              <div className="label">AVG INTRADAY %</div>
              <div className="value text-blue">
                 {volatilityData.stats ? volatilityData.stats.avg_intraday : '-'}%
              </div>
              <div className="sub-label">Volatility Score</div>
            </div>

            {/* Thẻ 3: Peak Volatility */}
            <div className="stat-card pro-card">
              <div className="label">PEAK INTRADAY</div>
              <div className="value text-purple">
                 {volatilityData.stats ? volatilityData.stats.peak_intraday : '-'}%
              </div>
              <div className="sub-label">Max 1H Range</div>
            </div>

            {/* Thẻ 4: Best Trading Time */}
            <div className="stat-card pro-card">
              <div className="label">PEAK TIME</div>
              <div className="value text-yellow">
                 {volatilityData.stats ? volatilityData.stats.best_hour : '--:--'}
              </div>
              <div className="sub-label">Best Volatility</div>
            </div>

            {/* Thẻ 5: AI Winrate */}
            <div className="stat-card pro-card">
              <div className="label">AI WINRATE</div>
              <div className={`value ${market && market.winrate > 60 ? 'text-green' : 'text-red'}`}>
                 {market ? market.winrate : '-'}%
              </div>
              <div className="sub-label">Model Confidence</div>
            </div>
          </div>
        )}

        {/* MAIN CHART & LOGS (SPLIT VIEW) */}
        <div className="main-layout">
          {/* CHART SECTION */}
          <div className="panel chart-panel">
            <div className="panel-header">
              <Zap size={18} color="#ffd700"/> THE ORACLE PREDICTION
            </div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={simPaths}>
                  <Tooltip 
                     contentStyle={{backgroundColor: '#000', border: '1px solid #333'}} 
                     itemStyle={{color: '#fff'}}
                     labelStyle={{display:'none'}}
                     filterNull={true}
                  />
                  {/* 20 Đường mờ */}
                  {Array.from({ length: 20 }).map((_, i) => (
                    <Line key={i} type="monotone" dataKey={`path_${i}`} 
                      stroke="#00ff41" strokeOpacity={0.08} dot={false} activeDot={false} strokeWidth={1}
                      isAnimationActive={false}
                    />
                  ))}
                  {/* Đường chính (Vàng) */}
                  <Line type="monotone" dataKey="mean" stroke="#ffd700" strokeWidth={2} dot={false} activeDot={{r: 6, fill: '#ffd700'}} />
                  
                  {market && (
                    <>
                      <ReferenceLine y={market.tp} stroke="#00ff41" strokeDasharray="3 3" label={{position: 'right', value:'TP', fill:'#00ff41', fontSize:10}} />
                      <ReferenceLine y={market.sl} stroke="#ff003c" strokeDasharray="3 3" label={{position: 'right', value:'SL', fill:'#ff003c', fontSize:10}} />
                    </>
                  )}
                  <YAxis domain={['auto', 'auto']} hide />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* LOGS SECTION */}
          <div className="panel logs-panel">
            <div className="panel-header">
              <AlertTriangle size={18} /> EXECUTION LOGS
            </div>
            <div className="logs-list">
              <table>
                <thead>
                  <tr>
                    <th>TIME</th>
                    <th>ACTION</th>
                    <th>PRICE</th>
                    <th>SCORE</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log, index) => (
                    <tr key={index}>
                      <td className="text-gray">{log.Timestamp.split(' ')[1]}</td>
                      <td className={log.Action === 'LONG' ? 'text-green' : 'text-red'}>{log.Action}</td>
                      <td>${Number(log.Price).toFixed(0)}</td>
                      <td><span className={`badge ${log.Score >= 14 ? 'high' : 'low'}`}>{log.Score}</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* VOLATILITY CHART */}
        <div className="panel" style={{marginTop: '15px', height: '250px', flexShrink: 0}}>
          <div className="panel-header">
            <Activity size={18} /> MARKET VOLATILITY BY HOUR (UTC)
          </div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
            {/* SỬA LỖI: Dùng đúng volatilityData.chart */}
            <BarChart data={volatilityData.chart || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
                <XAxis 
                  dataKey="hour" 
                  tick={{fill: '#666', fontSize: 10}} 
                  tickFormatter={(val) => `${val}h`}
                />
                <Tooltip 
                  cursor={{fill: 'rgba(255,255,255,0.05)'}}
                  contentStyle={{backgroundColor: '#000', border: '1px solid #333', color: '#fff'}}
                />
                <Bar dataKey="volatility" name="Biến động TB (%)">
                  {/* SỬA LỖI: Map vào mảng chart bên trong, không map object cha */}
                  {(volatilityData.chart || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.volatility > 0.5 ? '#ff003c' : '#00ff41'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

      </main>
    </div>
  );
}

export default App;