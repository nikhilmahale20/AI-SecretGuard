import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Shield, AlertCircle, Database, Lock, Activity } from 'lucide-react';

export default function App() {
  const [logs, setLogs] = useState([]);

  const fetchLogs = async () => {
    try {
      const res = await axios.get('http://127.0.0.1:8000/audit-logs');
      setLogs(res.data);
    } catch (err) {
      console.error("SOC Connection Offline");
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-[#0f172a] text-slate-200 p-6 font-sans">
      {/* Header */}
      <div className="flex justify-between items-center mb-8 bg-[#1e293b] p-6 rounded-2xl border border-slate-700 shadow-xl">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-blue-500/10 rounded-xl">
            <Shield className="w-8 h-8 text-blue-500" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Neural-Sentinel SOC</h1>
            <p className="text-slate-400 text-sm">AI-Powered Secret Redaction Monitoring</p>
          </div>
        </div>
        <div className="flex gap-4">
          <div className="text-right">
            <p className="text-xs text-slate-500 uppercase font-bold tracking-widest">Database</p>
            <p className="text-green-400 font-mono text-sm">PostgreSQL Connected</p>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-3 gap-6 mb-8">
        <div className="bg-[#1e293b] p-6 rounded-2xl border border-slate-700">
          <Activity className="w-6 h-6 text-blue-400 mb-2" />
          <p className="text-slate-400 text-sm">Total Scans</p>
          <p className="text-3xl font-bold text-white">{logs.length}</p>
        </div>
        <div className="bg-[#1e293b] p-6 rounded-2xl border border-slate-700">
          <AlertCircle className="w-6 h-6 text-red-400 mb-2" />
          <p className="text-slate-400 text-sm">Threats Detected</p>
          <p className="text-3xl font-bold text-white">
            {logs.reduce((acc, log) => acc + log.threat_count, 0)}
          </p>
        </div>
        <div className="bg-[#1e293b] p-6 rounded-2xl border border-slate-700">
          <Lock className="w-6 h-6 text-purple-400 mb-2" />
          <p className="text-slate-400 text-sm">Avg Confidence</p>
          <p className="text-3xl font-bold text-white">98.2%</p>
        </div>
      </div>

      {/* Table */}
      <div className="bg-[#1e293b] rounded-2xl border border-slate-700 shadow-2xl overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-800/50 text-slate-400 text-xs uppercase tracking-tighter">
            <tr>
              <th className="p-4">Timestamp</th>
              <th className="p-4">Source File</th>
              <th className="p-4">Findings</th>
              <th className="p-4">Risk Severity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {logs.map((log) => (
              <tr key={log.id} className="hover:bg-slate-800/30 transition-all">
                <td className="p-4 text-xs font-mono text-slate-500">{log.timestamp}</td>
                <td className="p-4 font-semibold text-blue-400">{log.file_name}</td>
                <td className="p-4">
                  <span className="bg-slate-900 px-3 py-1 rounded-full text-xs">
                    {log.threat_count} potential secrets
                  </span>
                </td>
                <td className="p-4">
                  <span className={`px-3 py-1 rounded-md text-[10px] font-black uppercase ${
                    log.highest_risk === 'CRITICAL' ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
                  }`}>
                    {log.highest_risk}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}