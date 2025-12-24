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
  const [volatilityData, setVolatilityData] = useState({ chart: [], stats: null });
  const [aiThoughts, setAiThoughts] = useState([]);

  // --- STATE MỚI: STRATEGY PLANNER ---
  const [capital, setCapital] = useState(50);     // Vốn
  const [target, setTarget] = useState(10);       // Mục tiêu lãi ($)
  const [trades, setTrades] = useState(5);        // Số lệnh dự kiến
  const [leverage, setLeverage] = useState(1);    // Đòn bẩy tính toán
  
  // Toggles
  const [trailing, setTrailing] = useState(true);
  const [hedge, setHedge] = useState(false);
  const [compound, setCompound] = useState(false);

  // Tự động tính toán Plan khi nhập liệu thay đổi
  useEffect(() => {
    // Logic đơn giản: (Target / Vốn) / Số lệnh = % Lãi cần mỗi lệnh
    // Đòn bẩy = % Lãi cần / (Biến động trung bình ~0.5%)
    const requiredRoi = (target / capital) * 100;
    const roiPerTrade = requiredRoi / trades;
    const estLev = Math.ceil(roiPerTrade / 0.6); // Giả sử nến 15m biến động 0.6%
    setLeverage(estLev < 1 ? 1 : (estLev > 125 ? 125 : estLev));
  }, [capital, target, trades]);


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

  useEffect(() => {
    const messages = [
      "Scanning market microstructure...", "Analyzing volume delta divergence...",
      "Calculated Fibonacci retracement at 0.618", "Checking correlation with SPX500...",
      "Whale wallet movement detected...", "Sentiment analysis: NEUTRAL-BULLISH",
      "Optimizing stop-loss parameters...", "Fetching latest funding rates...",
      "Resistance detected at $88,500", "Executing Monte Carlo simulation (n=1000)...",
      "Order book imbalance detected on Binance..."
    ];
    const interval = setInterval(() => {
      const randomMsg = messages[Math.floor(Math.random() * messages.length)];
      const timestamp = new Date().toLocaleTimeString('en-US', {hour12: false});
      setAiThoughts(prev => {
        const type = Math.random() > 0.8 ? 'highlight' : (Math.random() > 0.9 ? 'danger' : 'normal');
        return [{ time: timestamp, msg: randomMsg, type: type }, ...prev].slice(0, 15);
      });
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return <div className="loading-screen">CONNECTING TO TITAN SERVER...</div>;

  return (
    <div className="dashboard-container">
      {/* --- CỘT 1: SIDEBAR TRÁI (CONFIG & STRATEGY) --- */}
      <aside className="sidebar">
        <div className="logo-section">
          <Shield color="#00ff41"/> <span>TITAN OS</span>
        </div>
        
        {/* Market Config */}
        <div>
          <h2>Market Config</h2>
          <div className="control-group">
            <label className="label">Timeframe</label>
            <select className="control-input"><option>15 Minute</option><option>1 Hour</option></select>
          </div>
          <div className="control-group" style={{marginTop:10}}>
            <label className="label">Volatility Method</label>
            <select className="control-input"><option>ATR (Standard)</option><option>Bollinger Band</option></select>
          </div>
        </div>

        {/* --- PHẦN MỚI: STRATEGY CORE --- */}
        <div>
          <h2>Strategy Core</h2>
          <div className="strategy-form">
            <div className="input-row">
              <div className="input-group">
                <label>Capital ($)</label>
                <input type="number" value={capital} onChange={e => setCapital(Number(e.target.value))} />
              </div>
              <div className="input-group">
                <label>Target ($)</label>
                <input type="number" value={target} onChange={e => setTarget(Number(e.target.value))} />
              </div>
            </div>

            <div className="input-group">
              <label>Est. Trades</label>
              <input type="range" min="1" max="20" value={trades} onChange={e => setTrades(Number(e.target.value))} />
              <div style={{textAlign:'right', fontSize:10, color:'#888'}}>{trades} trades per session</div>
            </div>

            {/* Toggles */}
            <div className="toggle-row">
              <span>Trailing SL (Auto)</span>
              <label className="switch">
                <input type="checkbox" checked={trailing} onChange={() => setTrailing(!trailing)} />
                <span className="slider round"></span>
              </label>
            </div>
            <div className="toggle-row">
              <span>Hedge Mode (Safe)</span>
              <label className="switch">
                <input type="checkbox" checked={hedge} onChange={() => setHedge(!hedge)} />
                <span className="slider round"></span>
              </label>
            </div>
            <div className="toggle-row">
              <span>Compound (Risky)</span>
              <label className="switch">
                <input type="checkbox" checked={compound} onChange={() => setCompound(!compound)} />
                <span className="slider round"></span>
              </label>
            </div>

            {/* KẾT QUẢ TÍNH TOÁN CỦA AI */}
            <div className="plan-result">
               <div className="plan-row"><span>Rec. Leverage:</span> <span className="plan-val">{leverage}x</span></div>
               <div className="plan-row"><span>Entry Size:</span> <span className="plan-val">${(capital * leverage / trades).toFixed(0)}</span></div>
               <div className="plan-row"><span>Risk / Trade:</span> <span className="plan-val text-red">${(capital * 0.02).toFixed(2)}</span></div>
            </div>

            {/* PROGRESS BAR */}
            <div className="target-progress">
              <div className="progress-label"><span>SESSION GOAL</span> <span>$0 / ${target}</span></div>
              <div className="p-bar-bg"><div className="p-bar-fill" style={{width: '5%'}}></div></div>
            </div>
          </div>
        </div>
      </aside>
      
      {/* --- CỘT 2: DATA CENTER --- */}
      <main className="content-area">
        <header className="header">
          <div className="logo-section">
            <Shield className="logo-icon" size={28} />
            <div><h1>TITAN AEGIS <span style={{color:'var(--neon-yellow)'}}>V7</span></h1></div>
          </div>
          <div className="status-badge online"><div className="dot"></div> SYSTEM ONLINE</div>
        </header>

        {market && (
          <div className="stats-grid">
            <div className="stat-card pro-card">
              <div className="label">CURRENT PRICE</div>
              <div className="value" style={{color: '#fff'}}>${market ? market.price.toLocaleString() : '---'}</div>
              <div className="sub-label">BTC/USDT</div>
            </div>
            <div className="stat-card pro-card">
              <div className="label">AVG INTRADAY %</div>
              <div className="value text-blue">{volatilityData.stats ? volatilityData.stats.avg_intraday : '-'}%</div>
              <div className="sub-label">Volatility Score</div>
            </div>
            <div className="stat-card pro-card">
              <div className="label">PEAK INTRADAY</div>
              <div className="value text-purple">{volatilityData.stats ? volatilityData.stats.peak_intraday : '-'}%</div>
              <div className="sub-label">Max 1H Range</div>
            </div>
            <div className="stat-card pro-card">
              <div className="label">PEAK TIME</div>
              <div className="value text-yellow">{volatilityData.stats ? volatilityData.stats.best_hour : '--:--'}</div>
              <div className="sub-label">Best Volatility</div>
            </div>
            <div className="stat-card pro-card">
              <div className="label">AI WINRATE</div>
              <div className={`value ${market && market.winrate > 60 ? 'text-green' : 'text-red'}`}>{market ? market.winrate : '-'}%</div>
              <div className="sub-label">Model Confidence</div>
            </div>
          </div>
        )}

        <div className="main-layout">
          <div className="panel chart-panel">
            <div className="panel-header"><Zap size={18} color="#ffd700"/> THE ORACLE PREDICTION</div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={simPaths}>
                  <Tooltip contentStyle={{backgroundColor: '#000', border: '1px solid #333'}} itemStyle={{color: '#fff'}} labelStyle={{display:'none'}} filterNull={true} />
                  {Array.from({ length: 20 }).map((_, i) => (
                    <Line key={i} type="monotone" dataKey={`path_${i}`} stroke="#00ff41" strokeOpacity={0.08} dot={false} activeDot={false} strokeWidth={1} isAnimationActive={false} />
                  ))}
                  <Line type="monotone" dataKey="mean" stroke="#ffd700" strokeWidth={2} dot={false} activeDot={{r: 6, fill: '#ffd700'}} />
                  {market && (
                    <><ReferenceLine y={market.tp} stroke="#00ff41" strokeDasharray="3 3" label={{position: 'right', value:'TP', fill:'#00ff41', fontSize:10}} /><ReferenceLine y={market.sl} stroke="#ff003c" strokeDasharray="3 3" label={{position: 'right', value:'SL', fill:'#ff003c', fontSize:10}} /></>
                  )}
                  <YAxis domain={['auto', 'auto']} hide />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="panel logs-panel">
            <div className="panel-header"><AlertTriangle size={18} /> EXECUTION LOGS</div>
            <div className="logs-list">
              <table>
                <thead><tr><th>TIME</th><th>ACTION</th><th>PRICE</th><th>SCORE</th></tr></thead>
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

        <div className="panel" style={{marginTop: '15px', height: '250px', flexShrink: 0}}>
          <div className="panel-header"><Activity size={18} /> MARKET VOLATILITY BY HOUR (UTC)</div>
          <div className="chart-container">
            <ResponsiveContainer width="100%" height="100%">
            <BarChart data={volatilityData.chart || []}>
                <CartesianGrid strokeDasharray="3 3" stroke="#222" vertical={false} />
                <XAxis dataKey="hour" tick={{fill: '#666', fontSize: 10}} tickFormatter={(val) => `${val}h`} />
                <Tooltip cursor={{fill: 'rgba(255,255,255,0.05)'}} contentStyle={{backgroundColor: '#000', border: '1px solid #333', color: '#fff'}} />
                <Bar dataKey="volatility" name="Biến động TB (%)">
                  {(volatilityData.chart || []).map((entry, index) => (<Cell key={`cell-${index}`} fill={entry.volatility > 0.5 ? '#ff003c' : '#00ff41'} />))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </main>

      {/* --- CỘT 3: RIGHT SIDEBAR --- */}
      <aside className="right-sidebar">
        <div className="right-panel" style={{flex: 2}}>
          <div className="terminal-header"><span>⚡ TITAN CORTEX AI</span><span style={{fontSize: 10, color: '#666'}}>v7.0.1</span></div>
          <div className="terminal-content">
            {aiThoughts.map((log, i) => (
              <div key={i} className={`ai-log ${log.type}`}><span style={{opacity:0.5, fontSize:10, marginRight:5}}>[{log.time}]</span>{log.msg}</div>
            ))}
          </div>
        </div>
        <div className="right-panel" style={{flex: 1, borderTop: '1px solid #333'}}>
           <div className="terminal-header"><span>🌊 MARKET DEPTH</span></div>
          <div className="order-book">
             <div className="ob-row"><span className="ask">87,240.00</span> <span>0.45 BTC</span></div>
             <div className="ob-bar"><div className="ob-fill" style={{width: '40%', background: '#ff003c'}}></div></div>
             <div className="ob-row"><span className="ask">87,235.50</span> <span>1.20 BTC</span></div>
             <div className="ob-bar"><div className="ob-fill" style={{width: '80%', background: '#ff003c'}}></div></div>
             <div style={{margin: '10px 0', textAlign:'center', color:'#888', fontSize:10}}>--- SPREAD ---</div>
             <div className="ob-row"><span className="bid">87,230.00</span> <span>2.50 BTC</span></div>
             <div className="ob-bar"><div className="ob-fill" style={{width: '90%', background: '#00ff41'}}></div></div>
             <div className="ob-row"><span className="bid">87,225.00</span> <span>0.80 BTC</span></div>
             <div className="ob-bar"><div className="ob-fill" style={{width: '30%', background: '#00ff41'}}></div></div>
          </div>
        </div>
      </aside>
    </div>
  );
}

export default App;