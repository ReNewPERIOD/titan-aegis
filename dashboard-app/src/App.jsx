import { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Activity, TrendingUp, TrendingDown, Zap, Shield, AlertTriangle } from 'lucide-react';
import './App.css';

const API_URL = 'http://127.0.0.1:8000';

function App() {
  const [market, setMarket] = useState(null);
  const [simPaths, setSimPaths] = useState([]);
  const [meanPath, setMeanPath] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  // Hàm lấy dữ liệu từ Python Server
  const fetchData = async () => {
    try {
      // 1. Lấy dữ liệu thị trường
      const marketRes = await axios.get(`${API_URL}/market-data`);
      setMarket(marketRes.data);

      // 2. Lấy dữ liệu biểu đồ Monte Carlo
      const simRes = await axios.get(`${API_URL}/simulation-paths`);
      // Chuyển đổi dữ liệu mảng thành format Recharts hiểu được
      const formattedPaths = simRes.data.paths[0].map((_, index) => {
        let point = { index };
        simRes.data.paths.forEach((path, pathIndex) => {
          point[`path_${pathIndex}`] = path[index];
        });
        point.mean = simRes.data.mean_path[index];
        return point;
      });
      setSimPaths(formattedPaths);
      setMeanPath(simRes.data.mean_path);

      // 3. Lấy lịch sử lệnh
      const logsRes = await axios.get(`${API_URL}/trade-logs`);
      setLogs(logsRes.data);

      setError(false);
      setLoading(false);
    } catch (err) {
      console.error("Lỗi kết nối:", err);
      setError(true);
    }
  };

  // Tự động quét mỗi 2 giây
  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !market) return <div className="loading-screen">INITIALIZING TITAN PROTOCOL...</div>;

  return (
    <div className="dashboard-container">
      {/* HEADER */}
      <header className="header">
        <div className="logo-section">
          <Shield className="logo-icon" size={32} />
          <div>
            <h1>TITAN AEGIS V7</h1>
            <span className="subtitle">AI HEDGE FUND / QUANT CORE</span>
          </div>
        </div>
        <div className={`status-badge ${error ? 'offline' : 'online'}`}>
          <div className="dot"></div>
          {error ? 'CONNECTION LOST' : 'SYSTEM ONLINE'}
        </div>
      </header>

      {/* STATS GRID */}
      {market && (
        <div className="stats-grid">
          <div className="card stat-card">
            <div className="stat-label">BITCOIN PRICE</div>
            <div className="stat-value price">${market.price.toLocaleString()}</div>
          </div>
          
          <div className="card stat-card">
            <div className="stat-label">AI CONFIDENCE (WINRATE)</div>
            <div className={`stat-value ${market.winrate > 60 ? 'text-green' : 'text-red'}`}>
              {market.winrate}%
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill" 
                style={{ width: `${market.winrate}%`, backgroundColor: market.winrate > 60 ? '#00ff41' : '#ff003c' }}
              ></div>
            </div>
          </div>

          <div className="card stat-card">
            <div className="stat-label">TREND BIAS</div>
            <div className={`stat-value flex-center ${market.trend === 'UP' ? 'text-green' : 'text-red'}`}>
              {market.trend === 'UP' ? <TrendingUp size={30} /> : <TrendingDown size={30} />}
              <span style={{marginLeft: 10}}>{market.trend}</span>
            </div>
          </div>

          <div className="card stat-card">
            <div className="stat-label">VOLATILITY (ATR)</div>
            <div className="stat-value text-yellow">
              <Activity size={24} style={{display:'inline', marginRight:5}}/>
              {market.atr.toFixed(2)}
            </div>
          </div>
        </div>
      )}

      {/* MAIN CONTENT */}
      <div className="main-layout">
        {/* LEFT: ORACLE CHART */}
        <div className="card chart-section">
          <div className="card-header">
            <Zap size={20} color="#ffd700"/>
            <h3>THE ORACLE (MONTE CARLO PREDICTION)</h3>
          </div>
          <div className="chart-wrapper">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={simPaths}>
                {/* Vẽ 50 đường mờ ảo */}
                {Array.from({ length: 50 }).map((_, i) => (
                  <Line 
                    key={i} 
                    type="monotone" 
                    dataKey={`path_${i}`} 
                    stroke="#00ff41" 
                    strokeOpacity={0.05} 
                    dot={false} 
                    strokeWidth={1}
                  />
                ))}
                {/* Đường trung bình màu vàng */}
                <Line type="monotone" dataKey="mean" stroke="#ffd700" strokeWidth={3} dot={false} />
                
                {market && (
                  <>
                    <ReferenceLine y={market.tp} stroke="#00ff41" strokeDasharray="3 3" label="TP" />
                    <ReferenceLine y={market.sl} stroke="#ff003c" strokeDasharray="3 3" label="SL" />
                  </>
                )}
                <XAxis dataKey="index" hide />
                <YAxis domain={['auto', 'auto']} hide />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="chart-legend">
            <span style={{color: '#ffd700'}}>— Mean Path</span>
            <span style={{color: '#00ff41', opacity: 0.5}}>— Monte Carlo Simulations</span>
          </div>
        </div>

        {/* BOTTOM: TRADE LOGS */}
        <div className="card logs-section">
          <div className="card-header">
            <AlertTriangle size={20} />
            <h3>EXECUTION LOGS</h3>
          </div>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>TIME</th>
                  <th>PAIR</th>
                  <th>ACTION</th>
                  <th>PRICE</th>
                  <th>SCORE</th>
                  <th>STATUS</th>
                </tr>
              </thead>
              <tbody>
                {logs.map((log, index) => (
                  <tr key={index} className="log-row">
                    <td>{log.Timestamp.split(' ')[1]}</td>
                    <td>{log.Symbol}</td>
                    <td className={log.Action === 'LONG' ? 'text-green' : 'text-red'}>{log.Action}</td>
                    <td>${log.Price}</td>
                    <td>
                      <span className={`score-badge ${log.Score >= 14 ? 'high' : 'low'}`}>
                        {log.Score}/15
                      </span>
                    </td>
                    <td>EXECUTED</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;