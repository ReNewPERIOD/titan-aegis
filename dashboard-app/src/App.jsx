import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
// Charting Libraries
import { LineChart, Line, Bar, ComposedChart, Cell, YAxis, ResponsiveContainer, ReferenceLine, Tooltip, AreaChart, Area } from 'recharts';
import { createChart, ColorType } from 'lightweight-charts';
// Icons
import { Activity, Zap, Shield, AlertTriangle, BarChart2, AlertOctagon } from 'lucide-react';
import './App.css';

const API_URL = 'https://titan-backend-rl21.onrender.com';

function App() {
  const [market, setMarket] = useState(null);
  const [simPaths, setSimPaths] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [volatilityData, setVolatilityData] = useState({ chart: [], stats: null });
  const [aiThoughts, setAiThoughts] = useState([]);
  const [indicators, setIndicators] = useState([]); 
  const [dangerLevel, setDangerLevel] = useState('SAFE');

  // Refs for Lightweight Chart
  const chartContainerRef = useRef();
  const chartRef = useRef(); // Store chart instance
  const candlestickSeriesRef = useRef(); // Store series instance

  // Config States
  const [timeframe, setTimeframe] = useState('15m');
  const [capital, setCapital] = useState(1000);
  const [target, setTarget] = useState(500);
  const [trades, setTrades] = useState(5);
  const [leverage, setLeverage] = useState(1);
  const [entrySize, setEntrySize] = useState(0);
  
  const [trailing, setTrailing] = useState(true);
  const [hedge, setHedge] = useState(false);
  const [compound, setCompound] = useState(false);

  // --- STRATEGY & RISK LOGIC ---
  useEffect(() => {
    const sizePerTrade = capital / trades; 
    const requiredProfit = target / trades;
    const requiredRoi = (requiredProfit / sizePerTrade) * 100;

    let atrPercent = 0.5; 
    if (timeframe === '3m') atrPercent = 0.15;
    if (timeframe === '5m') atrPercent = 0.25;
    if (timeframe === '1h') atrPercent = 0.8;
    if (timeframe === '4h') atrPercent = 1.5;

    let estLev = Math.ceil(requiredRoi / atrPercent);
    if (estLev < 1) estLev = 1;
    if (estLev > 125) estLev = 125;

    setLeverage(estLev);
    setEntrySize(sizePerTrade);

    const positionSize = sizePerTrade * estLev;
    const riskAmount = capital * 0.02; 
    const safeBuffer = (riskAmount / positionSize) * 100;

    if (estLev >= 50 || safeBuffer < 0.3) {
        setDangerLevel("CRITICAL");
    } else if (estLev >= 20 || safeBuffer < 0.8) {
        setDangerLevel("WARNING");
    } else {
        setDangerLevel("SAFE");
    }
  }, [capital, target, trades, timeframe]);

  // --- DATA FETCHING ---
  // --- FETCH DATA ---
  const fetchData = async () => {
    try {
      // Gọi API...
      const [marketRes, simRes, logsRes, volRes, indRes] = await Promise.all([
        axios.get(`${API_URL}/market-data?tf=${timeframe}`), 
        axios.get(`${API_URL}/simulation-paths?tf=${timeframe}`),
        axios.get(`${API_URL}/trade-logs`),
        axios.get(`${API_URL}/volatility-analysis`),
        axios.get(`${API_URL}/technical-indicators?tf=${timeframe}`)
      ]);

      // Set dữ liệu...
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
      if (volRes.data && volRes.data.stats) setVolatilityData(volRes.data);
      if (indRes.data) setIndicators(indRes.data);

    } catch (err) { 
      console.error("Lỗi kết nối:", err); 
      // Không làm gì cả để giữ nguyên dữ liệu cũ trên màn hình
    } finally {
      // QUAN TRỌNG: Luôn tắt Loading dù thành công hay thất bại
      setLoading(false); 
    }
  };

  useEffect(() => {
    setLoading(true);
    fetchData();
    // QUAN TRỌNG: Tăng lên 10000ms (10 giây) để giảm tải cho Server Render Free
    const interval = setInterval(fetchData, 10000); 
    return () => clearInterval(interval);
  }, [timeframe]);

  // --- LIGHTWEIGHT CHART INIT & UPDATE ---
  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Initialize chart only once
    if (!chartRef.current) {
      const chart = createChart(chartContainerRef.current, {
        layout: {
          background: { type: ColorType.Solid, color: '#14151a' },
          textColor: '#94a3b8',
        },
        grid: {
          vertLines: { color: '#262626' },
          horzLines: { color: '#262626' },
        },
        width: chartContainerRef.current.clientWidth,
        height: chartContainerRef.current.clientHeight,
        timeScale: {
          timeVisible: true,
          secondsVisible: false,
          borderColor: '#262626',
        },
        rightPriceScale: {
          borderColor: '#262626',
          scaleMargins: {
            top: 0.1,
            bottom: 0.1,
          },
        },
      });

      const series = chart.addCandlestickSeries({
        upColor: '#00ff41',
        downColor: '#ff003c',
        borderVisible: false,
        wickUpColor: '#00ff41',
        wickDownColor: '#ff003c',
      });

      chartRef.current = chart;
      candlestickSeriesRef.current = series;

      const handleResize = () => {
        if (chartContainerRef.current) {
          chart.applyOptions({ width: chartContainerRef.current.clientWidth, height: chartContainerRef.current.clientHeight });
        }
      };
      window.addEventListener('resize', handleResize);
      
      return () => {
        window.removeEventListener('resize', handleResize);
        chart.remove();
        chartRef.current = null;
      };
    }
  }, []);

  // Update chart data when indicators change
  useEffect(() => {
    if (candlestickSeriesRef.current && indicators.length > 0) {
      const chartData = indicators.map(item => ({
        time: item.timestamp / 1000, 
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
      }));
      candlestickSeriesRef.current.setData(chartData);
      chartRef.current.timeScale().fitContent(); // Auto zoom to fit data
    }
  }, [indicators]);


  // AI Thoughts
  useEffect(() => {
    const messages = ["Scanning market...", "Analyzing volume...", "Calculated Fibonacci 0.618...", "Whale detected...", "Sentiment: BULLISH", "Optimizing SL..."];
    const interval = setInterval(() => {
      const randomMsg = messages[Math.floor(Math.random() * messages.length)];
      const timestamp = new Date().toLocaleTimeString('en-US', {hour12: false});
      setAiThoughts(prev => [{ time: timestamp, msg: randomMsg, type: Math.random() > 0.8 ? 'highlight' : 'normal' }, ...prev].slice(0, 15));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !market) return <div className="loading-screen">SYNCING DATA STREAM ({timeframe})...</div>;

  return (
    <div className="dashboard-container">
      {/* SIDEBAR - CONFIG */}
      <aside className="sidebar">
        <div className="logo-section"><Shield color="#00ff41"/> <span>TITAN OS</span></div>
        
        <div>
          <h2>Market Data Feed</h2>
          <div className="control-group">
            <label className="label">Active Timeframe</label>
            <select className="control-input" value={timeframe} onChange={(e) => setTimeframe(e.target.value)}>
              <option value="3m">⚡ 3 Minute (Scalp)</option>
              <option value="5m">⚡ 5 Minute (Scalp)</option>
              <option value="15m">⏱ 15 Minute (Day)</option>
              <option value="1h">⏱ 1 Hour (Swing)</option>
              <option value="4h">🌊 4 Hour (Trend)</option>
            </select>
          </div>
        </div>

        <div>
          <h2>Strategy Core</h2>
          <div className="strategy-form">
            <div className="input-row">
              <div className="input-group"><label>Capital ($)</label><input type="number" value={capital} onChange={e => setCapital(Number(e.target.value))} /></div>
              <div className="input-group"><label>Target ($)</label><input type="number" value={target} onChange={e => setTarget(Number(e.target.value))} /></div>
            </div>
            <div className="input-group">
              <label>Est. Trades</label>
              <input type="range" min="1" max="20" value={trades} onChange={e => setTrades(Number(e.target.value))} />
              <div style={{textAlign:'right', fontSize:10, color:'#888'}}>{trades} trades</div>
            </div>

            <div className="toggle-row"><span>Trailing SL</span><label className="switch"><input type="checkbox" checked={trailing} onChange={() => setTrailing(!trailing)} /><span className="slider round"></span></label></div>
            <div className="toggle-row"><span>Hedge Mode</span><label className="switch"><input type="checkbox" checked={hedge} onChange={() => setHedge(!hedge)} /><span className="slider round"></span></label></div>

            {/* RESULTS & ALERTS */}
            <div className={`plan-result ${dangerLevel === 'CRITICAL' ? 'blink-border' : ''}`} 
                 style={{borderColor: dangerLevel === 'CRITICAL' ? '#ff003c' : (dangerLevel === 'WARNING' ? '#facc15' : '#4ade80')}}>
               
               {dangerLevel === 'CRITICAL' && (
                 <div style={{color:'#ff003c', fontSize:10, fontWeight:'bold', marginBottom:5, display:'flex', alignItems:'center', gap:5}}>
                   <AlertOctagon size={12}/> HIGH LIQUIDATION RISK!
                 </div>
               )}

               <div className="plan-row"><span>Rec. Leverage:</span> <span className={`plan-val ${dangerLevel === 'CRITICAL' ? 'text-red' : 'text-yellow'}`}>{leverage}x</span></div>
               <div className="plan-row"><span>Entry Size:</span> <span className="plan-val">${entrySize.toFixed(0)}</span></div>
               
               <div className="plan-row" style={{marginTop:5, borderTop:'1px dashed #333', paddingTop:5}}>
                  <span style={{color:'#888'}}>Safe Buffer:</span> 
                  <span className="plan-val" style={{color: dangerLevel === 'CRITICAL' ? '#ff003c' : '#fff'}}>
                    {((capital * 0.02) / (entrySize * leverage) * 100).toFixed(2)}%
                  </span>
               </div>
            </div>
            
             <div className="target-progress">
              <div className="progress-label"><span>SESSION GOAL</span> <span>$0 / ${target}</span></div>
              <div className="p-bar-bg"><div className="p-bar-fill" style={{width: '2%'}}></div></div>
            </div>
          </div>
        </div>
      </aside>
      
      {/* MAIN CONTENT AREA */}
      <main className="content-area">
        <header className="header">
          <div className="logo-section"><Shield className="logo-icon" size={28} /><div><h1>TITAN AEGIS <span style={{color:'var(--neon-yellow)'}}>V7</span></h1></div></div>
          <div className="status-badge online"><div className="dot"></div> SYNCED: {timeframe.toUpperCase()}</div>
        </header>

        {market && (
          <div className="stats-grid">
            <div className="stat-card pro-card"><div className="label">CURRENT PRICE</div><div className="value" style={{color: '#fff'}}>${market.price.toLocaleString()}</div></div>
            <div className="stat-card pro-card"><div className="label">VOLUME POWER</div><div className={`value ${market.volume_power > 100 ? 'text-green' : 'text-yellow'}`}>{market.volume_power}%</div></div>
            <div className="stat-card pro-card"><div className="label">TREND ({timeframe})</div><div className={`value ${market.trend === 'UP' ? 'text-green' : 'text-red'}`}>{market.trend}</div></div>
            <div className="stat-card pro-card"><div className="label">VOLATILITY (ATR)</div><div className="value text-purple">{market.atr ? market.atr.toFixed(2) : '-'}</div></div>
            <div className="stat-card pro-card"><div className="label">AI CONFIDENCE</div><div className={`value ${market.winrate > 60 ? 'text-green' : 'text-red'}`}>{market.winrate}%</div></div>
          </div>
        )}

        <div className="main-layout">
          {/* LEFT: ORACLE CHART */}
          <div className="panel chart-panel">
            <div className="panel-header"><Zap size={18} color="#ffd700"/> PRICE SIMULATION ({timeframe})</div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={simPaths}>
                  <Tooltip contentStyle={{backgroundColor: '#000', border: '1px solid #333'}} itemStyle={{color: '#fff'}} labelStyle={{display:'none'}} filterNull={true} />
                  {Array.from({ length: 15 }).map((_, i) => (<Line key={i} type="monotone" dataKey={`path_${i}`} stroke="#00ff41" strokeOpacity={0.05} dot={false} activeDot={false} isAnimationActive={false} />))}
                  <Line type="monotone" dataKey="mean" stroke="#ffd700" strokeWidth={2} dot={false} activeDot={{r: 6, fill: '#ffd700'}} />
                  <YAxis domain={['auto', 'auto']} hide />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* RIGHT: LOGS & INDICATORS */}
          <div style={{display: 'flex', flexDirection: 'column', gap: '15px', minWidth: 0, flex: 1}}>
              
              {/* 1. EXECUTION LOGS */}
              <div className="panel" style={{flex: 1, minHeight: '150px'}}>
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

              {/* 2. TECHNICAL INDICATORS (RSI/MACD) */}
              <div className="panel" style={{height: '240px', display: 'flex', flexDirection: 'column'}}>
                <div className="panel-header" style={{fontSize: 10, padding: '8px 15px'}}><Activity size={14} color="#38bdf8"/> TECHNICALS (RSI + MACD)</div>
                <div style={{flex: 2, borderBottom: '1px solid #222', padding: '5px'}}>
                   <ResponsiveContainer width="100%" height="100%"><AreaChart data={indicators}><defs><linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#8884d8" stopOpacity={0.3}/><stop offset="95%" stopColor="#8884d8" stopOpacity={0}/></linearGradient></defs><YAxis domain={['auto', 'auto']} hide /><Tooltip contentStyle={{background:'#000', border:'none', fontSize:10}} itemStyle={{padding:0}} labelStyle={{display:'none'}}/><Area type="monotone" dataKey="close" stroke="#8884d8" fillOpacity={1} fill="url(#colorPrice)" strokeWidth={1.5} /></AreaChart></ResponsiveContainer>
                </div>
                <div style={{flex: 1, borderBottom: '1px solid #222', padding: '5px', position:'relative'}}>
                   <span style={{position:'absolute', top:2, left:5, fontSize:8, color:'#666'}}>RSI(14)</span>
                   <ResponsiveContainer width="100%" height="100%"><LineChart data={indicators}><YAxis domain={[0, 100]} hide /><ReferenceLine y={70} stroke="#ff003c" strokeDasharray="2 2" /><ReferenceLine y={30} stroke="#00ff41" strokeDasharray="2 2" /><Line type="monotone" dataKey="rsi" stroke="#38bdf8" dot={false} strokeWidth={1} /></LineChart></ResponsiveContainer>
                </div>
                <div style={{flex: 1, padding: '5px', position:'relative'}}>
                   <span style={{position:'absolute', top:2, left:5, fontSize:8, color:'#666'}}>MACD</span>
                   <ResponsiveContainer width="100%" height="100%"><ComposedChart data={indicators}><YAxis hide /><Bar dataKey="macd_hist" fill="#4ade80">{indicators.map((entry, index) => (<Cell key={`cell-${index}`} fill={entry.macd_hist > 0 ? '#4ade80' : '#ff003c'} />))}</Bar><Line type="monotone" dataKey="macd" stroke="#fff" dot={false} strokeWidth={1} /><Line type="monotone" dataKey="macd_signal" stroke="#facc15" dot={false} strokeWidth={1} /></ComposedChart></ResponsiveContainer>
                </div>
              </div>
          </div>
        </div>

        {/* --- BOTTOM PANEL: REAL-TIME CANDLESTICK CHART (NEW) --- */}
        <div className="bottom-chart-panel">
           <div className="panel-header"><BarChart2 size={18} /> REAL-TIME MARKET STRUCTURE ({timeframe})</div>
           {/* Container for Lightweight Chart */}
           <div ref={chartContainerRef} className="chart-container" style={{padding: 0, height: '100%', width: '100%'}}></div>
        </div>
      </main>

      {/* RIGHT SIDEBAR - AI & ORDER BOOK */}
      <aside className="right-sidebar">
        <div className="right-panel" style={{flex: 2}}>
          <div className="terminal-header"><span>⚡ TITAN CORTEX AI</span><span style={{fontSize: 10, color: '#666'}}>v7.1</span></div>
          <div className="terminal-content">{aiThoughts.map((log, i) => (<div key={i} className={`ai-log ${log.type}`}><span style={{opacity:0.5, fontSize:10, marginRight:5}}>[{log.time}]</span>{log.msg}</div>))}</div>
        </div>
        <div className="right-panel" style={{flex: 1, borderTop: '1px solid #333'}}>
           <div className="terminal-header"><span>🌊 ORDER FLOW</span></div>
           <div className="order-book">
              <div className="ob-row"><span className="ask">87,240.00</span> <span>0.45</span></div><div className="ob-bar"><div className="ob-fill" style={{width: '40%', background: '#ff003c'}}></div></div>
              <div className="ob-row"><span className="ask">87,235.50</span> <span>1.20</span></div><div className="ob-bar"><div className="ob-fill" style={{width: '80%', background: '#ff003c'}}></div></div>
              <div style={{margin: '5px 0', textAlign:'center', color:'#444', fontSize:8}}>SPREAD</div>
              <div className="ob-row"><span className="bid">87,230.00</span> <span>2.50</span></div><div className="ob-bar"><div className="ob-fill" style={{width: '90%', background: '#00ff41'}}></div></div>
              <div className="ob-row"><span className="bid">87,225.00</span> <span>0.80</span></div><div className="ob-bar"><div className="ob-fill" style={{width: '30%', background: '#00ff41'}}></div></div>
           </div>
        </div>
      </aside>
    </div>
  );
}

export default App;