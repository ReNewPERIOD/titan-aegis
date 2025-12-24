import { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, ReferenceLine, Tooltip } from 'recharts';
import { Activity, TrendingUp, TrendingDown, Zap, Shield, AlertTriangle } from 'lucide-react';
import './App.css';

// --- CẤU HÌNH API (Đã tự động lấy link từ bước trước) ---
const API_URL = 'https://titan-backend-rl21.onrender.com'; // Thay bằng link Render của bạn nếu cần

function App() {
  const [market, setMarket] = useState(null);
  const [simPaths, setSimPaths] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [marketRes, simRes, logsRes] = await Promise.all([
        axios.get(`${API_URL}/market-data`),
        axios.get(`${API_URL}/simulation-paths`),
        axios.get(`${API_URL}/trade-logs`)
      ]);

      setMarket(marketRes.data);

      // Xử lý dữ liệu biểu đồ
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
      setLoading(false);
    } catch (err) {
      console.error("Kết nối thất bại:", err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 3000); // 3s cập nhật 1 lần cho đỡ lag
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="loading-screen">CONNECTING TO TITAN SERVER...</div>;

  return (
    <div className="dashboard-container">
      {/* HEADER COMPACT */}
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
          <div className="stat-card">
            <div className="label">BITCOIN PRICE</div>
            <div className="value glow">${market.price.toLocaleString()}</div>
          </div>
          
          <div className="stat-card">
            <div className="label">AI WINRATE</div>
            <div className={`value ${market.winrate > 60 ? 'text-green' : 'text-red'}`}>
              {market.winrate}%
            </div>
            <div className="progress-bg"><div className="progress-fill" style={{width: `${market.winrate}%`, background: market.winrate > 60 ? '#00ff41' : '#ff003c'}}></div></div>
          </div>

          <div className="stat-card">
            <div className="label">TREND</div>
            <div className={`value flex-row ${market.trend === 'UP' ? 'text-green' : 'text-red'}`}>
              {market.trend === 'UP' ? <TrendingUp /> : <TrendingDown />} 
              {market.trend}
            </div>
          </div>

          <div className="stat-card">
            <div className="label">VOLATILITY (ATR)</div>
            <div className="value text-yellow"><Activity size={20}/> {market.atr.toFixed(2)}</div>
          </div>
        </div>
      )}

      {/* MAIN CONTENT SPLIT */}
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
                {/* 50 Đường mờ (Tắt dot, tắt activeDot để không bị lỗi cột trắng) */}
                {Array.from({ length: 20 }).map((_, i) => (
                  <Line key={i} type="monotone" dataKey={`path_${i}`} 
                    stroke="#00ff41" strokeOpacity={0.08} dot={false} activeDot={false} strokeWidth={1}
                    isAnimationActive={false} // Tắt animation để nhẹ máy
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
    </div>
  );
}

export default App;