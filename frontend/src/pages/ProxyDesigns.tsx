import React from 'react';
import ProxyCardDesigns from '../components/ProxyCardDesigns';
import type { Proxy } from '../types';

const ProxyDesigns: React.FC = () => {
  // Sample proxy data for demonstration
  const sampleProxy: Proxy = {
    id: 1,
    name: "My OpenAI Proxy",
    provider: "openai",
    description: "Sample OpenAI Proxy for testing",
    tags: ["production", "gpt-4", "api"],
    port: 3001,
    status: "running",
    user_id: "user123",
    failure_config: {
      timeout_enabled: true,
      error_injection_enabled: false,
      ip_filtering_enabled: false,
      rate_limiting_enabled: false,
      timeout_duration: 5000,
      error_injection_rate: 0,
      allowed_ips: [],
      blocked_ips: [],
      rate_limit_requests: 0,
      rate_limit_window: 0
    }
  };

  const sampleProxyStopped: Proxy = {
    ...sampleProxy,
    id: 2,
    name: "My Anthropic Proxy",
    provider: "anthropic",
    description: "Sample Anthropic Proxy - currently stopped",
    tags: ["staging", "claude", "test"],
    port: 3002,
    status: "stopped",
    failure_config: undefined
  };

  const handleStart = (id: number) => {
    console.log('Start proxy:', id);
  };

  const handleStop = (id: number) => {
    console.log('Stop proxy:', id);
  };

  const handleConfigure = (proxy: Proxy) => {
    console.log('Configure proxy:', proxy);
  };

  const handleDelete = (id: number) => {
    console.log('Delete proxy:', id);
  };

  const handleClearCache = (proxy: Proxy) => {
    console.log('Clear cache for proxy:', proxy);
  };

  const handleShowCode = (proxy: Proxy) => {
    console.log('Show code for proxy:', proxy);
  };

  const handleShowCacheInfo = (proxy: Proxy) => {
    console.log('Show cache info for proxy:', proxy);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Proxy Card Design Showcase</h1>
          <p className="text-gray-600">
            Here are 6 different design variations for the proxy cards. Each design showcases different 
            approaches to layout, visual hierarchy, and user interaction patterns.
          </p>
        </div>

        <div className="space-y-12">
          <div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Running Proxy Examples</h2>
            <ProxyCardDesigns
              proxy={sampleProxy}
              onStart={handleStart}
              onStop={handleStop}
              onConfigure={handleConfigure}
              onDelete={handleDelete}
              onClearCache={handleClearCache}
              onShowCode={handleShowCode}
              onShowCacheInfo={handleShowCacheInfo}
            />
          </div>

          <div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">Stopped Proxy Examples</h2>
            <ProxyCardDesigns
              proxy={sampleProxyStopped}
              onStart={handleStart}
              onStop={handleStop}
              onConfigure={handleConfigure}
              onDelete={handleDelete}
              onClearCache={handleClearCache}
              onShowCode={handleShowCode}
              onShowCacheInfo={handleShowCacheInfo}
            />
          </div>
        </div>

        <div className="mt-12 p-6 bg-blue-50 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">Design Notes</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li><strong>Design #1:</strong> Compact horizontal layout - saves vertical space</li>
            <li><strong>Design #2:</strong> Header bar with status indicator - clear visual hierarchy</li>
            <li><strong>Design #3:</strong> Minimal clean design - modern and focused</li>
            <li><strong>Design #4:</strong> Dashboard metrics style - information-rich</li>
            <li><strong>Design #5:</strong> Side status bar - unique visual indicator</li>
            <li><strong>Design #6:</strong> Modern glassmorphism - contemporary aesthetic</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ProxyDesigns;