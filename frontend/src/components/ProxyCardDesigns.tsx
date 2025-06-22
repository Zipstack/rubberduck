import React, { useState } from 'react';
import {
  PlayIcon,
  StopIcon,
  CogIcon,
  TrashIcon,
  ExclamationTriangleIcon,
  EllipsisVerticalIcon,
  CommandLineIcon,
  TrashIcon as CacheIcon,
  InformationCircleIcon,
  ChartBarIcon,
  CloudIcon,
  ServerIcon,
  SignalIcon,
} from '@heroicons/react/24/outline';
import type { Proxy } from '../types';

interface ProxyCardDesignsProps {
  proxy: Proxy;
  onStart: (id: number) => void;
  onStop: (id: number) => void;
  onConfigure: (proxy: Proxy) => void;
  onDelete: (id: number) => void;
  onClearCache: (proxy: Proxy) => void;
  onShowCode: (proxy: Proxy) => void;
  onShowCacheInfo: (proxy: Proxy) => void;
}

const ProxyCardDesigns: React.FC<ProxyCardDesignsProps> = ({
  proxy,
  onStart,
  onStop,
  onConfigure,
  onDelete,
  onClearCache,
  onShowCode,
  onShowCacheInfo,
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [showActionsDropdown, setShowActionsDropdown] = useState<{[key: string]: boolean}>({});
  const [showDeleteWarning, setShowDeleteWarning] = useState<{[key: string]: boolean}>({});

  const handleAction = async (action: () => void) => {
    setIsLoading(true);
    try {
      action();
      await new Promise(resolve => setTimeout(resolve, 1000));
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    return status === 'running' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800';
  };

  const getProviderIcon = (provider: string) => {
    const icons: Record<string, string> = {
      openai: '🤖',
      anthropic: '🧠',
      azure_openai: '☁️',
      bedrock: '🟠',
      vertex_ai: '🔍',
    };
    return icons[provider.toLowerCase()] || '🔧';
  };

  const toggleDropdown = (designId: string) => {
    setShowActionsDropdown(prev => ({
      ...prev,
      [designId]: !prev[designId]
    }));
  };

  const handleDeleteClick = (designId: string) => {
    if (proxy.status === 'running') {
      setShowDeleteWarning(prev => ({
        ...prev,
        [designId]: true
      }));
      setTimeout(() => {
        setShowDeleteWarning(prev => ({
          ...prev,
          [designId]: false
        }));
      }, 3000);
    } else {
      onDelete(proxy.id);
    }
  };

  const hasFailureConfig = proxy.failure_config && (
    proxy.failure_config.timeout_enabled ||
    proxy.failure_config.error_injection_enabled ||
    proxy.failure_config.ip_filtering_enabled ||
    proxy.failure_config.rate_limiting_enabled
  );

  return (
    <div className="space-y-8 p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-8">Proxy Card Design Variations</h1>
      
      {/* Design #1: Compact Horizontal Layout */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-700">Design #1: Compact Horizontal</h2>
        <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="text-3xl">{getProviderIcon(proxy.provider)}</div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-lg font-semibold text-gray-900">{proxy.name}</h3>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(proxy.status)}`}>
                    {proxy.status}
                  </span>
                </div>
                <p className="text-sm text-gray-500">
                  {proxy.provider} • Port {proxy.port}
                  {proxy.tags && proxy.tags.length > 0 && (
                    <span className="ml-2">
                      {proxy.tags.slice(0, 2).map((tag, index) => (
                        <span key={index} className="inline-block px-1 py-0.5 bg-blue-50 text-blue-600 text-xs rounded mr-1">
                          {tag}
                        </span>
                      ))}
                    </span>
                  )}
                </p>
              </div>
            </div>
            <div className="flex space-x-2">
              {proxy.status === 'stopped' ? (
                <button className="px-3 py-1 bg-green-50 text-green-700 hover:bg-green-100 rounded text-sm">
                  <PlayIcon className="h-4 w-4 inline mr-1" />Start
                </button>
              ) : (
                <button className="px-3 py-1 bg-red-50 text-red-700 hover:bg-red-100 rounded text-sm">
                  <StopIcon className="h-4 w-4 inline mr-1" />Stop
                </button>
              )}
              <button className="px-3 py-1 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded text-sm">
                <CogIcon className="h-4 w-4 inline mr-1" />Config
              </button>
              <button 
                onClick={() => handleDeleteClick('design1')}
                className={`px-3 py-1 rounded text-sm ${
                  proxy.status === 'running'
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-red-50 text-red-700 hover:bg-red-100'
                }`}
                disabled={proxy.status === 'running'}
              >
                <TrashIcon className="h-4 w-4 inline mr-1" />Delete
              </button>
            </div>
          </div>
          {showDeleteWarning['design1'] && (
            <div className="mt-2 flex items-center space-x-2 p-2 bg-red-50 border border-red-200 rounded">
              <ExclamationTriangleIcon className="h-4 w-4 text-red-600" />
              <span className="text-xs text-red-700">Cannot delete running proxy. Stop the proxy first.</span>
            </div>
          )}
          {hasFailureConfig && (
            <div className="mt-2 flex items-center space-x-2 p-2 bg-yellow-50 border border-yellow-200 rounded">
              <ExclamationTriangleIcon className="h-4 w-4 text-yellow-600" />
              <span className="text-xs text-yellow-700">Failure simulation active</span>
            </div>
          )}
        </div>
      </div>

      {/* Design #2: Card with Header Bar */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-700">Design #2: Header Bar Style</h2>
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow overflow-hidden">
          <div className={`h-2 ${proxy.status === 'running' ? 'bg-green-500' : 'bg-gray-400'}`}></div>
          <div className="p-4">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-gray-50 rounded-lg">
                  <div className="text-2xl">{getProviderIcon(proxy.provider)}</div>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{proxy.name}</h3>
                  <p className="text-sm text-gray-500 capitalize">{proxy.provider}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${proxy.status === 'running' ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                <span className="text-sm font-medium text-gray-700 capitalize">{proxy.status}</span>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
              <div>
                <span className="text-gray-500">Port:</span>
                <span className="ml-2 font-medium">{proxy.port}</span>
              </div>
              <div>
                <span className="text-gray-500">Provider:</span>
                <span className="ml-2 font-medium capitalize">{proxy.provider}</span>
              </div>
            </div>

            {proxy.tags && proxy.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-4">
                {proxy.tags.map((tag, index) => (
                  <span key={index} className="px-2 py-1 bg-blue-50 text-blue-600 text-xs rounded-full">
                    {tag}
                  </span>
                ))}
              </div>
            )}

            <div className="flex space-x-2">
              {proxy.status === 'stopped' ? (
                <button className="flex-1 flex items-center justify-center space-x-1 py-2 bg-green-50 text-green-700 hover:bg-green-100 rounded-md text-sm font-medium">
                  <PlayIcon className="h-4 w-4" />
                  <span>Start</span>
                </button>
              ) : (
                <button className="flex-1 flex items-center justify-center space-x-1 py-2 bg-red-50 text-red-700 hover:bg-red-100 rounded-md text-sm font-medium">
                  <StopIcon className="h-4 w-4" />
                  <span>Stop</span>
                </button>
              )}
              <button className="flex-1 flex items-center justify-center space-x-1 py-2 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-md text-sm font-medium">
                <CogIcon className="h-4 w-4" />
                <span>Configure</span>
              </button>
              <button 
                onClick={() => handleDeleteClick('design2')}
                className={`px-4 py-2 rounded-md text-sm font-medium ${
                  proxy.status === 'running'
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-red-50 text-red-700 hover:bg-red-100'
                }`}
                disabled={proxy.status === 'running'}
              >
                <TrashIcon className="h-4 w-4" />
              </button>
            </div>
            {showDeleteWarning['design2'] && (
              <div className="mt-3 flex items-center space-x-2 p-2 bg-red-50 border border-red-200 rounded">
                <ExclamationTriangleIcon className="h-4 w-4 text-red-600" />
                <span className="text-xs text-red-700">Cannot delete running proxy. Stop the proxy first.</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Design #3: Minimal Card */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-700">Design #3: Minimal Clean</h2>
        <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-lg transition-all duration-200">
          <div className="text-center">
            <div className="text-4xl mb-3">{getProviderIcon(proxy.provider)}</div>
            <h3 className="text-xl font-bold text-gray-900 mb-1">{proxy.name}</h3>
            <p className="text-gray-500 text-sm mb-4 capitalize">{proxy.provider}</p>
            
            <div className="flex items-center justify-center space-x-4 mb-4">
              <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(proxy.status)}`}>
                <div className={`w-2 h-2 rounded-full mr-2 ${proxy.status === 'running' ? 'bg-green-500' : 'bg-gray-500'}`}></div>
                {proxy.status}
              </div>
              <span className="text-gray-500 text-sm">Port {proxy.port}</span>
            </div>

            {proxy.tags && proxy.tags.length > 0 && (
              <div className="flex justify-center flex-wrap gap-1 mb-4">
                {proxy.tags.slice(0, 3).map((tag, index) => (
                  <span key={index} className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                    {tag}
                  </span>
                ))}
              </div>
            )}

            <div className="flex space-x-2 justify-center">
              {proxy.status === 'stopped' ? (
                <button className="px-4 py-2 bg-green-500 text-white hover:bg-green-600 rounded-lg text-sm font-medium transition-colors">
                  Start
                </button>
              ) : (
                <button className="px-4 py-2 bg-red-500 text-white hover:bg-red-600 rounded-lg text-sm font-medium transition-colors">
                  Stop
                </button>
              )}
              <button className="px-4 py-2 border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-lg text-sm font-medium transition-colors">
                Configure
              </button>
              <button 
                onClick={() => handleDeleteClick('design3')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  proxy.status === 'running'
                    ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                    : 'border border-red-300 text-red-700 hover:bg-red-50'
                }`}
                disabled={proxy.status === 'running'}
              >
                Delete
              </button>
            </div>
            {showDeleteWarning['design3'] && (
              <div className="mt-4 flex items-center justify-center space-x-2 p-2 bg-red-50 border border-red-200 rounded">
                <ExclamationTriangleIcon className="h-4 w-4 text-red-600" />
                <span className="text-xs text-red-700">Cannot delete running proxy. Stop the proxy first.</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Design #4: Dashboard Style with Metrics */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-700">Design #4: Dashboard Metrics</h2>
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow">
          <div className="p-4 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="relative">
                  <div className="text-2xl">{getProviderIcon(proxy.provider)}</div>
                  <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-white ${proxy.status === 'running' ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{proxy.name}</h3>
                  <p className="text-sm text-gray-500 capitalize">{proxy.provider}</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-500">Port</div>
                <div className="text-lg font-semibold text-gray-900">{proxy.port}</div>
              </div>
            </div>
          </div>
          
          <div className="p-4">
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center">
                <div className="flex items-center justify-center mb-1">
                  <ServerIcon className="h-4 w-4 text-gray-400 mr-1" />
                  <span className="text-xs text-gray-500">Status</span>
                </div>
                <div className={`text-sm font-medium ${proxy.status === 'running' ? 'text-green-600' : 'text-gray-600'}`}>
                  {proxy.status}
                </div>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center mb-1">
                  <SignalIcon className="h-4 w-4 text-gray-400 mr-1" />
                  <span className="text-xs text-gray-500">Uptime</span>
                </div>
                <div className="text-sm font-medium text-gray-900">
                  {proxy.status === 'running' ? '2h 15m' : '-'}
                </div>
              </div>
              <div className="text-center">
                <div className="flex items-center justify-center mb-1">
                  <ChartBarIcon className="h-4 w-4 text-gray-400 mr-1" />
                  <span className="text-xs text-gray-500">Requests</span>
                </div>
                <div className="text-sm font-medium text-gray-900">
                  {proxy.status === 'running' ? '1.2k' : '0'}
                </div>
              </div>
            </div>

            {proxy.tags && proxy.tags.length > 0 && (
              <div className="flex flex-wrap gap-1 mb-4">
                {proxy.tags.map((tag, index) => (
                  <span key={index} className="px-2 py-1 bg-indigo-50 text-indigo-600 text-xs rounded">
                    {tag}
                  </span>
                ))}
              </div>
            )}

            <div className="flex space-x-2">
              {proxy.status === 'stopped' ? (
                <button className="flex-1 py-2 bg-green-50 text-green-700 hover:bg-green-100 rounded text-sm font-medium">
                  Start Proxy
                </button>
              ) : (
                <button className="flex-1 py-2 bg-red-50 text-red-700 hover:bg-red-100 rounded text-sm font-medium">
                  Stop Proxy
                </button>
              )}
              <button className="px-4 py-2 bg-gray-50 text-gray-700 hover:bg-gray-100 rounded text-sm">
                ⚙️
              </button>
              <button 
                onClick={() => handleDeleteClick('design4')}
                className={`px-4 py-2 rounded text-sm ${
                  proxy.status === 'running'
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-red-50 text-red-700 hover:bg-red-100'
                }`}
                disabled={proxy.status === 'running'}
              >
                🗑️
              </button>
            </div>
            {showDeleteWarning['design4'] && (
              <div className="mt-3 flex items-center space-x-2 p-2 bg-red-50 border border-red-200 rounded">
                <ExclamationTriangleIcon className="h-4 w-4 text-red-600" />
                <span className="text-xs text-red-700">Cannot delete running proxy. Stop the proxy first.</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Design #5: Card with Side Status Bar */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-700">Design #5: Side Status Bar</h2>
        <div className="bg-white border border-gray-200 rounded-lg shadow-sm hover:shadow-md transition-shadow overflow-hidden">
          <div className="flex">
            <div className={`w-1 ${proxy.status === 'running' ? 'bg-green-500' : 'bg-gray-400'}`}></div>
            <div className="flex-1 p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className={`p-3 rounded-full ${proxy.status === 'running' ? 'bg-green-50' : 'bg-gray-50'}`}>
                    <div className="text-xl">{getProviderIcon(proxy.provider)}</div>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{proxy.name}</h3>
                    <p className="text-sm text-gray-500 capitalize">{proxy.provider} Proxy</p>
                  </div>
                </div>
                <div className="relative">
                  <button 
                    onClick={() => toggleDropdown('design5')}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    <EllipsisVerticalIcon className="h-5 w-5 text-gray-400" />
                  </button>
                  {showActionsDropdown['design5'] && (
                    <div className="absolute right-0 mt-1 w-32 bg-white border border-gray-200 rounded-md shadow-lg z-10">
                      <button className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50">
                        Configure
                      </button>
                      <button className="w-full px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50">
                        View Logs
                      </button>
                      <button 
                        onClick={() => handleDeleteClick('design5')}
                        className={`w-full px-3 py-2 text-left text-sm hover:bg-gray-50 ${
                          proxy.status === 'running'
                            ? 'text-gray-400 cursor-not-allowed'
                            : 'text-red-600'
                        }`}
                        disabled={proxy.status === 'running'}
                      >
                        Delete
                      </button>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex items-center space-x-6 mb-4 text-sm">
                <div className="flex items-center space-x-2">
                  <span className="text-gray-500">Port:</span>
                  <span className="font-medium text-gray-900">{proxy.port}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-gray-500">Status:</span>
                  <span className={`font-medium ${proxy.status === 'running' ? 'text-green-600' : 'text-gray-600'}`}>
                    {proxy.status}
                  </span>
                </div>
              </div>

              {proxy.tags && proxy.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mb-4">
                  {proxy.tags.map((tag, index) => (
                    <span key={index} className="px-2 py-1 bg-purple-50 text-purple-600 text-xs rounded-full">
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              <div className="flex items-center justify-between">
                <div className="flex space-x-2">
                  {proxy.status === 'stopped' ? (
                    <button className="flex items-center space-x-1 px-3 py-1.5 bg-green-100 text-green-700 hover:bg-green-200 rounded-full text-sm font-medium">
                      <PlayIcon className="h-3 w-3" />
                      <span>Start</span>
                    </button>
                  ) : (
                    <button className="flex items-center space-x-1 px-3 py-1.5 bg-red-100 text-red-700 hover:bg-red-200 rounded-full text-sm font-medium">
                      <StopIcon className="h-3 w-3" />
                      <span>Stop</span>
                    </button>
                  )}
                </div>
                <div className="text-xs text-gray-400">
                  {proxy.status === 'running' ? 'Running for 2h 15m' : 'Stopped'}
                </div>
              </div>
              {showDeleteWarning['design5'] && (
                <div className="mt-3 flex items-center space-x-2 p-2 bg-red-50 border border-red-200 rounded">
                  <ExclamationTriangleIcon className="h-4 w-4 text-red-600" />
                  <span className="text-xs text-red-700">Cannot delete running proxy. Stop the proxy first.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Design #6: Modern Glassmorphism Style */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-700">Design #6: Modern Glassmorphism</h2>
        <div className="relative bg-gradient-to-br from-blue-50 to-indigo-100 border border-white/20 rounded-2xl p-6 shadow-xl backdrop-blur-sm">
          <div className="absolute inset-0 bg-white/30 rounded-2xl"></div>
          <div className="relative z-10">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-4">
                <div className="relative">
                  <div className="w-12 h-12 bg-white/50 rounded-xl flex items-center justify-center backdrop-blur-sm">
                    <span className="text-2xl">{getProviderIcon(proxy.provider)}</span>
                  </div>
                  <div className={`absolute -top-1 -right-1 w-4 h-4 rounded-full border-2 border-white ${proxy.status === 'running' ? 'bg-green-400' : 'bg-gray-400'}`}></div>
                </div>
                <div>
                  <h3 className="text-lg font-bold text-gray-900">{proxy.name}</h3>
                  <p className="text-sm text-gray-600 capitalize">{proxy.provider}</p>
                </div>
              </div>
              <div className="text-right">
                <div className="text-2xl font-bold text-gray-900">{proxy.port}</div>
                <div className="text-xs text-gray-600">PORT</div>
              </div>
            </div>

            {proxy.description && (
              <p className="text-sm text-gray-700 mb-4 bg-white/30 p-3 rounded-lg">
                {proxy.description}
              </p>
            )}

            {proxy.tags && proxy.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-4">
                {proxy.tags.map((tag, index) => (
                  <span key={index} className="px-3 py-1 bg-white/40 text-gray-700 text-sm rounded-full backdrop-blur-sm">
                    {tag}
                  </span>
                ))}
              </div>
            )}

            <div className="flex space-x-3">
              {proxy.status === 'stopped' ? (
                <button className="flex-1 flex items-center justify-center space-x-2 py-3 bg-green-500/80 text-white hover:bg-green-500 rounded-xl font-medium transition-all duration-200 backdrop-blur-sm">
                  <PlayIcon className="h-4 w-4" />
                  <span>Start Proxy</span>
                </button>
              ) : (
                <button className="flex-1 flex items-center justify-center space-x-2 py-3 bg-red-500/80 text-white hover:bg-red-500 rounded-xl font-medium transition-all duration-200 backdrop-blur-sm">
                  <StopIcon className="h-4 w-4" />
                  <span>Stop Proxy</span>
                </button>
              )}
              <button className="px-4 py-3 bg-white/40 text-gray-700 hover:bg-white/60 rounded-xl font-medium transition-all duration-200 backdrop-blur-sm">
                <CogIcon className="h-4 w-4" />
              </button>
              <button 
                onClick={() => handleDeleteClick('design6')}
                className={`px-4 py-3 rounded-xl font-medium transition-all duration-200 backdrop-blur-sm ${
                  proxy.status === 'running'
                    ? 'bg-gray-300/40 text-gray-400 cursor-not-allowed'
                    : 'bg-red-500/40 text-red-700 hover:bg-red-500/60'
                }`}
                disabled={proxy.status === 'running'}
              >
                <TrashIcon className="h-4 w-4" />
              </button>
            </div>
            {showDeleteWarning['design6'] && (
              <div className="mt-4 flex items-center space-x-2 p-3 bg-red-400/20 border border-red-400/30 rounded-xl backdrop-blur-sm">
                <ExclamationTriangleIcon className="h-4 w-4 text-red-700" />
                <span className="text-sm text-red-700 font-medium">
                  Cannot delete running proxy. Stop the proxy first.
                </span>
              </div>
            )}

            {hasFailureConfig && (
              <div className="mt-4 flex items-center space-x-2 p-3 bg-yellow-400/20 border border-yellow-400/30 rounded-xl backdrop-blur-sm">
                <ExclamationTriangleIcon className="h-4 w-4 text-yellow-700" />
                <span className="text-sm text-yellow-700 font-medium">
                  Failure simulation active
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProxyCardDesigns;