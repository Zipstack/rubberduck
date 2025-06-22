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
} from '@heroicons/react/24/outline';
import type { Proxy } from '../types';

interface ProxyCardProps {
  proxy: Proxy;
  onStart: (id: number) => void;
  onStop: (id: number) => void;
  onConfigure: (proxy: Proxy) => void;
  onDelete: (id: number) => void;
  onClearCache: (proxy: Proxy) => void;
  onShowCode: (proxy: Proxy) => void;
  onShowCacheInfo: (proxy: Proxy) => void;
}

const ProxyCard: React.FC<ProxyCardProps> = ({
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
  const [showActionsDropdown, setShowActionsDropdown] = useState(false);
  const [showDeleteWarning, setShowDeleteWarning] = useState(false);

  const handleAction = async (action: () => void) => {
    setIsLoading(true);
    try {
      action();
      // Simulate API call delay
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

  const handleDeleteClick = () => {
    if (proxy.status === 'running') {
      setShowDeleteWarning(true);
      setTimeout(() => setShowDeleteWarning(false), 3000); // Hide warning after 3 seconds
    } else {
      onDelete(proxy.id);
    }
  };

  return (
    <div className="card hover:shadow-lg transition-all duration-200">
      <div className="flex items-start justify-between">
        <div className="flex items-center space-x-3">
          <div className="text-2xl">{getProviderIcon(proxy.provider)}</div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{proxy.name}</h3>
            <p className="text-sm text-gray-500 capitalize">
              {proxy.provider}
            </p>
            {proxy.description && (
              <p className="text-sm text-gray-600 mt-1">{proxy.description}</p>
            )}
          </div>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(proxy.status)}`}>
          {proxy.status}
        </span>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center space-x-4 text-sm text-gray-500">
          <span>Port: {proxy.port}</span>
          {proxy.tags && proxy.tags.length > 0 && (
            <div className="flex space-x-1">
              {proxy.tags.slice(0, 2).map((tag, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-blue-50 text-blue-600 text-xs rounded"
                >
                  {tag}
                </span>
              ))}
              {proxy.tags.length > 2 && (
                <span className="text-xs text-gray-400">+{proxy.tags.length - 2}</span>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="mt-4 flex items-center justify-between pt-4 border-t border-gray-100">
        <div className="flex space-x-2">
          {proxy.status === 'stopped' ? (
            <button
              onClick={() => handleAction(() => onStart(proxy.id))}
              disabled={isLoading}
              className="flex items-center space-x-1 px-3 py-1 bg-green-50 text-green-700 hover:bg-green-100 rounded-md text-sm font-medium transition-colors"
            >
              <PlayIcon className="h-4 w-4" />
              <span>{isLoading ? 'Starting...' : 'Start'}</span>
            </button>
          ) : (
            <button
              onClick={() => handleAction(() => onStop(proxy.id))}
              disabled={isLoading}
              className="flex items-center space-x-1 px-3 py-1 bg-red-50 text-red-700 hover:bg-red-100 rounded-md text-sm font-medium transition-colors"
            >
              <StopIcon className="h-4 w-4" />
              <span>{isLoading ? 'Stopping...' : 'Stop'}</span>
            </button>
          )}
          
          <button
            onClick={() => onConfigure(proxy)}
            className="flex items-center space-x-1 px-3 py-1 bg-blue-50 text-blue-700 hover:bg-blue-100 rounded-md text-sm font-medium transition-colors"
          >
            <CogIcon className="h-4 w-4" />
            <span>Configure</span>
          </button>
        </div>

        <div className="flex space-x-2">
          {/* Actions Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowActionsDropdown(!showActionsDropdown)}
              className="flex items-center space-x-1 px-3 py-1 bg-gray-50 text-gray-600 hover:bg-gray-100 rounded-md text-sm font-medium transition-colors"
            >
              <EllipsisVerticalIcon className="h-4 w-4" />
              <span>Actions</span>
            </button>
            
            {showActionsDropdown && (
              <div className="absolute right-0 mt-1 w-48 bg-white border border-gray-200 rounded-md shadow-lg z-10">
                <button
                  onClick={() => {
                    onShowCacheInfo(proxy);
                    setShowActionsDropdown(false);
                  }}
                  className="w-full flex items-center space-x-2 px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
                >
                  <InformationCircleIcon className="h-4 w-4" />
                  <span>Show Cache Info</span>
                </button>
                <button
                  onClick={() => {
                    onClearCache(proxy);
                    setShowActionsDropdown(false);
                  }}
                  className="w-full flex items-center space-x-2 px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
                >
                  <CacheIcon className="h-4 w-4" />
                  <span>Clear Cache</span>
                </button>
                <button
                  onClick={() => {
                    onShowCode(proxy);
                    setShowActionsDropdown(false);
                  }}
                  className="w-full flex items-center space-x-2 px-3 py-2 text-left text-sm text-gray-700 hover:bg-gray-50"
                >
                  <CommandLineIcon className="h-4 w-4" />
                  <span>Show Code</span>
                </button>
              </div>
            )}
          </div>

          <button
            onClick={handleDeleteClick}
            className={`flex items-center space-x-1 px-3 py-1 rounded-md text-sm font-medium transition-colors ${
              proxy.status === 'running'
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-gray-50 text-gray-600 hover:bg-red-50 hover:text-red-700'
            }`}
            disabled={proxy.status === 'running'}
          >
            <TrashIcon className="h-4 w-4" />
            <span>Delete</span>
          </button>
        </div>
      </div>

      {/* Delete warning message */}
      {showDeleteWarning && (
        <div className="mt-3 flex items-center space-x-2 p-2 bg-red-50 border border-red-200 rounded-md">
          <ExclamationTriangleIcon className="h-4 w-4 text-red-600" />
          <span className="text-xs text-red-700 font-medium">
            Cannot delete running proxy. Stop the proxy first.
          </span>
        </div>
      )}

      {/* Failure simulation indicator */}
      {proxy.failure_config && (
        proxy.failure_config.timeout_enabled ||
        proxy.failure_config.error_injection_enabled ||
        proxy.failure_config.ip_filtering_enabled ||
        proxy.failure_config.rate_limiting_enabled
      ) && (
        <div className="mt-3 flex items-center space-x-2 p-2 bg-yellow-50 border border-yellow-200 rounded-md">
          <ExclamationTriangleIcon className="h-4 w-4 text-yellow-600" />
          <span className="text-xs text-yellow-700 font-medium">
            Failure simulation active
          </span>
        </div>
      )}
    </div>
  );
};

export default ProxyCard;