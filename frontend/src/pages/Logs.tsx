import React, { useState, useEffect } from 'react';
import {
  FunnelIcon,
  ArrowDownTrayIcon,
  TrashIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
import type { LogEntry } from '../types';
import { apiClient, ApiError } from '../utils/api';

const Logs: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [proxyFilter, setProxyFilter] = useState('all');
  const [cacheFilter, setCacheFilter] = useState('all');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  // WebSocket temporarily disabled - using polling instead
  const isConnected = false;

  const toggleStreaming = () => {
    // WebSocket disabled - toggle between fast/slow polling
    setIsStreaming(!isStreaming);
  };

  useEffect(() => {
    loadLogs();
  }, [statusFilter, proxyFilter, cacheFilter]);

  // Polling for log updates - always active with different rates
  useEffect(() => {
    const refreshRate = isStreaming ? 3000 : 10000; // 3s when streaming, 10s normally
    
    const interval = setInterval(() => {
      loadLogs(false); // Don't show loading spinner on auto-refresh
    }, refreshRate);
    
    return () => clearInterval(interval);
  }, [isStreaming, statusFilter, proxyFilter, cacheFilter]);

  const loadLogs = async (showLoading = true) => {
    if (showLoading) {
      setIsLoading(true);
    }
    setError(null);
    try {
      const filters: any = {};
      if (statusFilter === 'success') filters.status_code = 200;
      if (statusFilter === 'error') filters.status_code = 400;
      if (proxyFilter !== 'all') filters.proxy_id = parseInt(proxyFilter);
      if (cacheFilter === 'hit') filters.cache_hit = true;
      if (cacheFilter === 'miss') filters.cache_hit = false;

      const data = await apiClient.getLogs(filters);
      setLogs(data);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message);
      } else {
        setError('Failed to load logs');
      }
      console.error('Failed to load logs:', error);
    } finally {
      if (showLoading) {
        setIsLoading(false);
      }
    }
  };

  const filteredLogs = logs.filter(log => {
    const matchesSearch = 
      (log.ip_address || '').includes(searchTerm) ||
      (log.prompt_hash || '').includes(searchTerm) ||
      log.proxy_id.toString().includes(searchTerm);
    
    const matchesStatus = statusFilter === 'all' || 
      (statusFilter === 'success' && log.status_code >= 200 && log.status_code < 300) ||
      (statusFilter === 'error' && (log.status_code >= 400 || log.failure_type));
    
    const matchesProxy = proxyFilter === 'all' || log.proxy_id.toString() === proxyFilter;
    
    const matchesCache = cacheFilter === 'all' ||
      (cacheFilter === 'hit' && log.cache_hit) ||
      (cacheFilter === 'miss' && !log.cache_hit);
    
    return matchesSearch && matchesStatus && matchesProxy && matchesCache;
  });


  const getStatusColor = (statusCode: number, failureType?: string) => {
    if (failureType) return 'bg-orange-100 text-orange-800';
    if (statusCode >= 200 && statusCode < 300) return 'bg-green-100 text-green-800';
    if (statusCode >= 400) return 'bg-red-100 text-red-800';
    return 'bg-gray-100 text-gray-800';
  };

  const formatLatency = (latency: number) => {
    return latency > 1000 ? `${(latency / 1000).toFixed(1)}s` : `${latency}ms`;
  };

  const exportLogs = async (format: 'csv' | 'json') => {
    try {
      const filters: any = {};
      if (statusFilter === 'success') filters.status_code = 200;
      if (statusFilter === 'error') filters.status_code = 400;
      if (proxyFilter !== 'all') filters.proxy_id = parseInt(proxyFilter);
      if (cacheFilter === 'hit') filters.cache_hit = true;
      if (cacheFilter === 'miss') filters.cache_hit = false;

      const blob = await apiClient.exportLogs(format, filters);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `logs-${new Date().toISOString().split('T')[0]}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error(`Failed to export logs as ${format}:`, error);
      if (error instanceof ApiError) {
        alert(`Failed to export logs: ${error.message}`);
      }
    }
  };

  const clearLogs = () => {
    if (confirm('Are you sure you want to clear all logs?')) {
      setLogs([]);
      // In a real implementation, this would call an API endpoint to clear logs
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Logs</h1>
          <div className="flex items-center space-x-4 mt-1">
            <p className="text-gray-600">
              Monitor request activity across all proxies • {filteredLogs.length} entries
            </p>
            <div className="flex items-center space-x-1 text-sm text-gray-500">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
              <span>
                {isConnected ? 'Live connection' : 'Disconnected'} 
                {lastUpdated && ` • Updated ${lastUpdated}`}
              </span>
            </div>
          </div>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={toggleStreaming}
            disabled={!isConnected}
            className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
              isStreaming 
                ? 'bg-red-100 text-red-700 hover:bg-red-200' 
                : 'bg-green-100 text-green-700 hover:bg-green-200'
            } ${!isConnected ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <div className="flex items-center space-x-2">
              <div className={`w-2 h-2 rounded-full ${isStreaming ? 'bg-red-500 animate-pulse' : 'bg-gray-400'}`}></div>
              <span>{isStreaming ? 'Stop Live' : 'Start Live'}</span>
            </div>
          </button>
          <div className="flex space-x-2">
            <button
              onClick={() => exportLogs('csv')}
              className="btn-secondary flex items-center space-x-1"
            >
              <ArrowDownTrayIcon className="h-4 w-4" />
              <span>CSV</span>
            </button>
            <button
              onClick={() => exportLogs('json')}
              className="btn-secondary flex items-center space-x-1"
            >
              <ArrowDownTrayIcon className="h-4 w-4" />
              <span>JSON</span>
            </button>
            <button
              onClick={clearLogs}
              className="btn-secondary flex items-center space-x-1 text-red-600 hover:bg-red-50"
            >
              <TrashIcon className="h-4 w-4" />
              <span>Clear</span>
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search logs..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field pl-10"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="input-field"
        >
          <option value="all">All Status</option>
          <option value="success">Success</option>
          <option value="error">Error</option>
        </select>
        <select
          value={proxyFilter}
          onChange={(e) => setProxyFilter(e.target.value)}
          className="input-field"
        >
          <option value="all">All Proxies</option>
          <option value="1">OpenAI GPT-4</option>
          <option value="2">Claude-3 Sonnet</option>
          <option value="3">Gemini Pro</option>
          <option value="4">GPT-3.5 Turbo</option>
        </select>
        <select
          value={cacheFilter}
          onChange={(e) => setCacheFilter(e.target.value)}
          className="input-field"
        >
          <option value="all">All Cache</option>
          <option value="hit">Cache Hit</option>
          <option value="miss">Cache Miss</option>
        </select>
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <FunnelIcon className="h-4 w-4" />
          <span>{filteredLogs.length} filtered</span>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <div className="flex items-center justify-between">
            <span>{error}</span>
            <button
              onClick={() => loadLogs()}
              className="text-red-600 hover:text-red-800 font-medium"
            >
              Retry
            </button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-8">
          <div className="inline-flex items-center space-x-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <span className="text-gray-600">Loading logs...</span>
          </div>
        </div>
      )}

      {/* Logs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Proxy
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  IP Address
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Latency
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cache
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Tokens
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Cost
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredLogs.map((log) => (
                <tr key={log.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    Proxy {log.proxy_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {log.ip_address}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(log.status_code, log.failure_type)}`}>
                      {log.failure_type || log.status_code}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatLatency(log.latency)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      log.cache_hit ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {log.cache_hit ? 'Hit' : 'Miss'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {log.token_usage || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {log.cost ? `$${log.cost.toFixed(4)}` : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {filteredLogs.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 text-4xl mb-4">📋</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">No logs found</h3>
            <p className="text-gray-500">
              {searchTerm || statusFilter !== 'all' || proxyFilter !== 'all' || cacheFilter !== 'all'
                ? 'Try adjusting your filters'
                : 'Start streaming to see real-time logs'
              }
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Logs;