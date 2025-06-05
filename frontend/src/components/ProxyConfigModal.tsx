import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { apiClient, ApiError } from '../utils/api';
import type { Proxy } from '../types';

interface FailureConfig {
  timeout_enabled: boolean;
  timeout_seconds?: number;
  timeout_rate: number;
  error_injection_enabled: boolean;
  error_rates: Record<number, number>;
  ip_filtering_enabled: boolean;
  ip_allowlist: string[];
  ip_blocklist: string[];
  rate_limiting_enabled: boolean;
  requests_per_minute: number;
}

interface ProxyConfigModalProps {
  proxy: Proxy;
  isOpen: boolean;
  onClose: () => void;
  onUpdate: () => void;
}

const ProxyConfigModal: React.FC<ProxyConfigModalProps> = ({
  proxy,
  isOpen,
  onClose,
  onUpdate,
}) => {
  const [config, setConfig] = useState<FailureConfig>({
    timeout_enabled: false,
    timeout_seconds: 5.0,
    timeout_rate: 0.0,
    error_injection_enabled: false,
    error_rates: {
      429: 0.0,
      500: 0.0,
      502: 0.0,
      503: 0.0,
    },
    ip_filtering_enabled: false,
    ip_allowlist: [],
    ip_blocklist: [],
    rate_limiting_enabled: false,
    requests_per_minute: 60,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load configuration when modal opens
  useEffect(() => {
    if (isOpen) {
      loadConfig();
    }
  }, [isOpen, proxy.id]);

  const loadConfig = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.getProxyFailureConfig(proxy.id);
      setConfig(response.failure_config);
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message);
      } else {
        setError('Failed to load configuration');
      }
      console.error('Failed to load proxy config:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    try {
      await apiClient.updateProxyFailureConfig(proxy.id, config);
      onUpdate();
      onClose();
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message);
      } else {
        setError('Failed to save configuration');
      }
      console.error('Failed to save proxy config:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleReset = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await apiClient.request(`/proxies/${proxy.id}/failure-config/reset`, {
        method: 'POST',
      });
      await loadConfig(); // Reload to get default values
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message);
      } else {
        setError('Failed to reset configuration');
      }
      console.error('Failed to reset proxy config:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateErrorRate = (statusCode: number, rate: number) => {
    setConfig(prev => ({
      ...prev,
      error_rates: {
        ...prev.error_rates,
        [statusCode]: rate,
      },
    }));
  };

  const updateIPList = (type: 'allowlist' | 'blocklist', value: string) => {
    const ips = value.split('\n').map(ip => ip.trim()).filter(ip => ip);
    setConfig(prev => ({
      ...prev,
      [`ip_${type}`]: ips,
    }));
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">
            Configure {proxy.name}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {isLoading ? (
            <div className="text-center py-8">
              <div className="inline-flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span className="text-gray-600">Loading configuration...</span>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Timeout Configuration */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900">Timeout Simulation</h3>
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={config.timeout_enabled}
                      onChange={(e) =>
                        setConfig(prev => ({ ...prev, timeout_enabled: e.target.checked }))
                      }
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Enable timeout simulation</span>
                  </label>

                  {config.timeout_enabled && (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Timeout Rate (0.0 - 1.0)
                        </label>
                        <input
                          type="number"
                          min="0"
                          max="1"
                          step="0.1"
                          value={config.timeout_rate}
                          onChange={(e) =>
                            setConfig(prev => ({ ...prev, timeout_rate: parseFloat(e.target.value) || 0 }))
                          }
                          className="input-field"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Timeout Duration (seconds, empty = indefinite)
                        </label>
                        <input
                          type="number"
                          min="0"
                          step="0.1"
                          value={config.timeout_seconds || ''}
                          onChange={(e) =>
                            setConfig(prev => ({ 
                              ...prev, 
                              timeout_seconds: e.target.value ? parseFloat(e.target.value) : undefined 
                            }))
                          }
                          className="input-field"
                          placeholder="Leave empty for indefinite hang"
                        />
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Error Injection */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900">Error Injection</h3>
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={config.error_injection_enabled}
                      onChange={(e) =>
                        setConfig(prev => ({ ...prev, error_injection_enabled: e.target.checked }))
                      }
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Enable error injection</span>
                  </label>

                  {config.error_injection_enabled && (
                    <div className="space-y-2">
                      {Object.entries(config.error_rates).map(([statusCode, rate]) => (
                        <div key={statusCode} className="flex items-center space-x-2">
                          <span className="w-12 text-sm text-gray-600">{statusCode}:</span>
                          <input
                            type="number"
                            min="0"
                            max="1"
                            step="0.1"
                            value={rate}
                            onChange={(e) =>
                              updateErrorRate(parseInt(statusCode), parseFloat(e.target.value) || 0)
                            }
                            className="flex-1 input-field"
                          />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Rate Limiting */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900">Rate Limiting</h3>
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={config.rate_limiting_enabled}
                      onChange={(e) =>
                        setConfig(prev => ({ ...prev, rate_limiting_enabled: e.target.checked }))
                      }
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Enable rate limiting</span>
                  </label>

                  {config.rate_limiting_enabled && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Requests per minute
                      </label>
                      <input
                        type="number"
                        min="1"
                        value={config.requests_per_minute}
                        onChange={(e) =>
                          setConfig(prev => ({ ...prev, requests_per_minute: parseInt(e.target.value) || 60 }))
                        }
                        className="input-field"
                      />
                    </div>
                  )}
                </div>
              </div>

              {/* IP Filtering */}
              <div className="space-y-4">
                <h3 className="text-lg font-medium text-gray-900">IP Filtering</h3>
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={config.ip_filtering_enabled}
                      onChange={(e) =>
                        setConfig(prev => ({ ...prev, ip_filtering_enabled: e.target.checked }))
                      }
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">Enable IP filtering</span>
                  </label>

                  {config.ip_filtering_enabled && (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          IP Allowlist (one per line)
                        </label>
                        <textarea
                          rows={3}
                          value={config.ip_allowlist.join('\n')}
                          onChange={(e) => updateIPList('allowlist', e.target.value)}
                          className="input-field"
                          placeholder="192.168.1.0/24&#10;127.0.0.1&#10;10.0.0.0/8"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          IP Blocklist (one per line)
                        </label>
                        <textarea
                          rows={3}
                          value={config.ip_blocklist.join('\n')}
                          onChange={(e) => updateIPList('blocklist', e.target.value)}
                          className="input-field"
                          placeholder="192.168.100.0/24&#10;1.2.3.4"
                        />
                      </div>
                    </>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200">
          <button
            onClick={handleReset}
            disabled={isLoading || isSaving}
            className="text-gray-600 hover:text-gray-800 font-medium"
          >
            Reset to Defaults
          </button>

          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              disabled={isSaving}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={isLoading || isSaving}
              className="btn-primary flex items-center space-x-2"
            >
              {isSaving && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              )}
              <span>{isSaving ? 'Saving...' : 'Save Configuration'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProxyConfigModal;