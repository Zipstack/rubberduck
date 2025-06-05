import React, { useState, useEffect } from 'react';
import { PlusIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import type { Proxy } from '../types';
import ProxyCard from '../components/ProxyCard';
import { apiClient, ApiError } from '../utils/api';

const Proxies: React.FC = () => {
  const [proxies, setProxies] = useState<Proxy[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProxies();
  }, []);

  const loadProxies = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient.getProxies();
      setProxies(data);
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message);
      } else {
        setError('Failed to load proxies');
      }
      console.error('Failed to load proxies:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredProxies = proxies.filter(proxy => {
    const matchesSearch = proxy.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         proxy.provider.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         proxy.model_name.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = selectedStatus === 'all' || proxy.status === selectedStatus;
    
    return matchesSearch && matchesStatus;
  });

  const handleStartProxy = async (id: number) => {
    try {
      await apiClient.startProxy(id);
      await loadProxies(); // Refresh the list
    } catch (error) {
      console.error('Failed to start proxy:', error);
      if (error instanceof ApiError) {
        alert(`Failed to start proxy: ${error.message}`);
      }
    }
  };

  const handleStopProxy = async (id: number) => {
    try {
      await apiClient.stopProxy(id);
      await loadProxies(); // Refresh the list
    } catch (error) {
      console.error('Failed to stop proxy:', error);
      if (error instanceof ApiError) {
        alert(`Failed to stop proxy: ${error.message}`);
      }
    }
  };

  const handleConfigureProxy = (proxy: Proxy) => {
    console.log('Configure proxy:', proxy);
    // This will open the configuration modal
  };

  const handleDeleteProxy = async (id: number) => {
    if (confirm('Are you sure you want to delete this proxy?')) {
      try {
        await apiClient.deleteProxy(id);
        await loadProxies(); // Refresh the list
      } catch (error) {
        console.error('Failed to delete proxy:', error);
        if (error instanceof ApiError) {
          alert(`Failed to delete proxy: ${error.message}`);
        }
      }
    }
  };

  const runningCount = proxies.filter(p => p.status === 'running').length;
  const stoppedCount = proxies.filter(p => p.status === 'stopped').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Proxies</h1>
          <p className="text-gray-600 mt-1">
            Manage your LLM proxy instances • {runningCount} running, {stoppedCount} stopped
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary flex items-center space-x-2"
        >
          <PlusIcon className="h-5 w-5" />
          <span>Create Proxy</span>
        </button>
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
          <div className="flex items-center justify-between">
            <span>{error}</span>
            <button
              onClick={loadProxies}
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
            <span className="text-gray-600">Loading proxies...</span>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search proxies..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field pl-10"
          />
        </div>
        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="input-field w-full sm:w-auto"
        >
          <option value="all">All Status</option>
          <option value="running">Running</option>
          <option value="stopped">Stopped</option>
        </select>
      </div>

      {/* Stats Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center">
            <div className="text-2xl font-bold text-gray-900">{proxies.length}</div>
            <div className="ml-2 text-sm text-gray-500">Total</div>
          </div>
        </div>
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center">
            <div className="text-2xl font-bold text-green-600">{runningCount}</div>
            <div className="ml-2 text-sm text-gray-500">Running</div>
          </div>
        </div>
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center">
            <div className="text-2xl font-bold text-gray-600">{stoppedCount}</div>
            <div className="ml-2 text-sm text-gray-500">Stopped</div>
          </div>
        </div>
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center">
            <div className="text-2xl font-bold text-blue-600">
              {proxies.reduce((sum, p) => sum + (p.failure_config ? 1 : 0), 0)}
            </div>
            <div className="ml-2 text-sm text-gray-500">With Failures</div>
          </div>
        </div>
      </div>

      {/* Proxies Grid */}
      {filteredProxies.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-400 text-6xl mb-4">🔍</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">No proxies found</h3>
          <p className="text-gray-500 mb-6">
            {searchTerm || selectedStatus !== 'all' 
              ? 'Try adjusting your search or filters'
              : 'Create your first proxy to get started'
            }
          </p>
          {!searchTerm && selectedStatus === 'all' && (
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn-primary"
            >
              Create Your First Proxy
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredProxies.map((proxy) => (
            <ProxyCard
              key={proxy.id}
              proxy={proxy}
              onStart={handleStartProxy}
              onStop={handleStopProxy}
              onConfigure={handleConfigureProxy}
              onDelete={handleDeleteProxy}
            />
          ))}
        </div>
      )}

      {/* Create Proxy Modal Placeholder */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-semibold mb-4">Create New Proxy</h2>
            <p className="text-gray-600 mb-4">Proxy creation form will be implemented here.</p>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="btn-secondary flex-1"
              >
                Cancel
              </button>
              <button
                onClick={() => setShowCreateModal(false)}
                className="btn-primary flex-1"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Proxies;