import React, { useState, useEffect } from 'react';
import {
  ServerIcon,
  ChartBarIcon,
  ClockIcon,
  CurrencyDollarIcon,
  ExclamationTriangleIcon,
  ArrowUpIcon,
  ArrowDownIcon,
} from '@heroicons/react/24/outline';
import type { DashboardStats, Proxy } from '../types';
import { apiClient, ApiError } from '../utils/api';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats>({
    total_proxies: 0,
    running_proxies: 0,
    stopped_proxies: 0,
    cache_hit_rate: 0,
    error_rate: 0,
    total_rpm: 0,
    total_cost: 0,
    in_flight_requests: 0,
  });

  const [proxies, setProxies] = useState<any[]>([]);
  const [recentActivity, setRecentActivity] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  useEffect(() => {
    loadDashboardData();
    
    // Refresh data every 5 seconds for real-time updates
    const interval = setInterval(() => {
      loadDashboardData();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    setError(null);
    try {
      // Load real metrics from backend
      const [metricsData, activityData] = await Promise.all([
        apiClient.getDashboardMetrics(),
        apiClient.getRecentActivity(5)
      ]);

      setStats(metricsData);
      // Use proxy_metrics from the dashboard metrics instead of separate proxy call
      setProxies(metricsData.proxy_metrics || []);
      setRecentActivity(activityData.logs || []);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message);
      } else {
        setError('Failed to load dashboard data');
      }
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const statsCards = [
    {
      title: 'Total Proxies',
      value: stats.total_proxies,
      subtext: `${stats.running_proxies} running, ${stats.stopped_proxies} stopped`,
      icon: ServerIcon,
      color: 'blue',
      trend: null,
    },
    {
      title: 'Cache Hit Rate',
      value: `${stats.cache_hit_rate.toFixed(1)}%`,
      subtext: 'Last 24 hours',
      icon: ChartBarIcon,
      color: 'green',
      trend: { value: 2.4, direction: 'up' },
    },
    {
      title: 'Error Rate',
      value: `${stats.error_rate.toFixed(1)}%`,
      subtext: 'Last 24 hours',
      icon: ExclamationTriangleIcon,
      color: stats.error_rate > 3 ? 'red' : 'yellow',
      trend: { value: 0.7, direction: 'down' },
    },
    {
      title: 'Total RPM',
      value: stats.total_rpm.toLocaleString(),
      subtext: 'Requests per minute',
      icon: ClockIcon,
      color: 'purple',
      trend: { value: 12.5, direction: 'up' },
    },
    {
      title: 'Total Cost',
      value: `$${stats.total_cost.toFixed(2)}`,
      subtext: 'This month',
      icon: CurrencyDollarIcon,
      color: 'indigo',
      trend: { value: 8.2, direction: 'up' },
    },
    {
      title: 'In-flight Requests',
      value: stats.in_flight_requests,
      subtext: 'Currently processing',
      icon: ArrowUpIcon,
      color: 'gray',
      trend: null,
    },
  ];

  const getColorClasses = (color: string) => {
    const colors = {
      blue: 'bg-blue-50 text-blue-600',
      green: 'bg-green-50 text-green-600',
      red: 'bg-red-50 text-red-600',
      yellow: 'bg-yellow-50 text-yellow-600',
      purple: 'bg-purple-50 text-purple-600',
      indigo: 'bg-indigo-50 text-indigo-600',
      gray: 'bg-gray-50 text-gray-600',
    };
    return colors[color as keyof typeof colors] || colors.gray;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">Monitor your LLM proxy performance</p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1 text-sm text-gray-500">
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
            <span>Live data{lastUpdated && ` • Updated ${lastUpdated}`}</span>
          </div>
          <button
            onClick={loadDashboardData}
            disabled={isLoading}
            className="btn-secondary"
          >
            {isLoading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <div className="flex items-center justify-between">
            <span>{error}</span>
            <button
              onClick={loadDashboardData}
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
            <span className="text-gray-600">Loading dashboard data...</span>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statsCards.map((stat, index) => (
          <div key={index} className="card hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <div className={`p-2 rounded-lg ${getColorClasses(stat.color)}`}>
                    <stat.icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-sm font-medium text-gray-900">{stat.title}</h3>
                </div>
                <div className="mt-3">
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                  <div className="flex items-center space-x-2 mt-1">
                    <p className="text-sm text-gray-500">{stat.subtext}</p>
                    {stat.trend && (
                      <div className={`flex items-center text-xs ${
                        stat.trend.direction === 'up' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {stat.trend.direction === 'up' ? (
                          <ArrowUpIcon className="h-3 w-3 mr-1" />
                        ) : (
                          <ArrowDownIcon className="h-3 w-3 mr-1" />
                        )}
                        {stat.trend.value}%
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Proxies */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Active Proxies</h3>
          <div className="space-y-3">
            {proxies.length === 0 && !isLoading ? (
              <div className="text-center py-4 text-gray-500">
                No proxies configured
              </div>
            ) : (
              proxies.slice(0, 4).map((proxy) => (
                <div key={proxy.id} className="flex items-center justify-between py-2 border-b border-gray-100 last:border-b-0">
                  <div className="flex items-center space-x-3">
                    <div className={`w-2 h-2 rounded-full ${
                      proxy.status === 'running' ? 'bg-green-400' : 'bg-gray-400'
                    }`}></div>
                    <div>
                      <p className="font-medium text-sm text-gray-900">{proxy.name}</p>
                      <p className="text-xs text-gray-500">{proxy.provider} • Port {proxy.port}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{proxy.rpm ? proxy.rpm.toFixed(1) : '0.0'} RPM</p>
                    <p className={`text-xs capitalize ${
                      proxy.status === 'running' ? 'text-green-600' : 'text-gray-500'
                    }`}>
                      {proxy.status}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Logs */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
          <div className="space-y-3">
            {recentActivity.length === 0 && !isLoading ? (
              <div className="text-center py-4 text-gray-500">
                No recent activity
              </div>
            ) : (
              recentActivity.map((log, index) => (
                <div key={index} className="flex items-center space-x-3 py-2">
                  <div className={`w-2 h-2 rounded-full ${
                    log.status === 'success' ? 'bg-green-400' :
                    log.status === 'warning' ? 'bg-yellow-400' :
                    log.status === 'error' ? 'bg-red-400' : 'bg-blue-400'
                  }`}></div>
                  <div className="flex-1">
                    <p className="text-sm text-gray-900">{log.event}</p>
                    <p className="text-xs text-gray-500">{log.proxy} • {log.time}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;