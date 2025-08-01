import React, { useState, useEffect } from 'react';
import { PlusIcon, MagnifyingGlassIcon, XMarkIcon, ClipboardDocumentIcon, CheckIcon } from '@heroicons/react/24/outline';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import type { Proxy } from '../types';
import ProxyCard from '../components/ProxyCard';
import ProxyConfigModal from '../components/ProxyConfigModal';
import { apiClient, ApiError } from '../utils/api';
import { usePageTitle } from '../hooks/usePageTitle';

const generateCurlExample = (proxy: Proxy): string => {
  const baseUrl = `http://localhost:${proxy.port}`;
  
  switch (proxy.provider.toLowerCase()) {
    case 'openai':
      return `curl -X POST "${baseUrl}/v1/chat/completions" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer \${OPENAI_API_KEY:-YOUR_OPENAI_API_KEY}" \\
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ]
  }'`;
    
    case 'anthropic':
      return `curl -X POST "${baseUrl}/messages" \\
  -H "Content-Type: application/json" \\
  -H "x-api-key: \${ANTHROPIC_API_KEY:-YOUR_ANTHROPIC_API_KEY}" \\
  -H "anthropic-version: 2023-06-01" \\
  -d '{
    "model": "claude-3-sonnet-20240229",
    "max_tokens": 1024,
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ]
  }'`;
    
    case 'azure_openai':
      return `curl -X POST "${baseUrl}/openai/deployments/\${AZURE_DEPLOYMENT_NAME:-YOUR_DEPLOYMENT}/chat/completions?api-version=2023-12-01-preview" \\
  -H "Content-Type: application/json" \\
  -H "api-key: \${AZURE_OPENAI_API_KEY:-YOUR_AZURE_API_KEY}" \\
  -d '{
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ]
  }'`;
    
    case 'bedrock':
      return `curl -X POST "${baseUrl}/model/anthropic.claude-3-sonnet-20240229-v1:0/invoke" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: AWS4-HMAC-SHA256 Credential=\${AWS_ACCESS_KEY_ID:-YOUR_AWS_ACCESS_KEY}..." \\
  -d '{
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 1024,
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ]
  }'`;
    
    case 'vertex_ai':
      return `curl -X POST "${baseUrl}/projects/\${GOOGLE_CLOUD_PROJECT:-YOUR_PROJECT}/locations/us-central1/publishers/google/models/gemini-pro:generateContent" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer \${GOOGLE_ACCESS_TOKEN:-YOUR_ACCESS_TOKEN}" \\
  -d '{
    "contents": [{
      "parts": [{"text": "Hello, world!"}]
    }]
  }'`;
    
    case 'deepseek':
      return `curl -X POST "${baseUrl}/v1/chat/completions" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer \${DEEPSEEK_API_KEY:-YOUR_DEEPSEEK_API_KEY}" \\
  -d '{
    "model": "deepseek-chat",
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ]
  }'`;
    
    default:
      return `curl -X POST "${baseUrl}/your-endpoint" \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer \${API_KEY:-YOUR_API_KEY}" \\
  -d '{"message": "Hello, world!"}'`;
  }
};

const generatePythonExample = (proxy: Proxy): string => {
  const baseUrl = `http://localhost:${proxy.port}`;
  
  switch (proxy.provider.toLowerCase()) {
    case 'openai':
      return `import os
import openai

client = openai.OpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY"),
    base_url="${baseUrl}/v1"
)

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "user", "content": "Hello, world!"}
    ]
)
print(response.choices[0].message.content)`;
    
    case 'anthropic':
      return `import os
import anthropic

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY"),
    base_url="${baseUrl}"
)

message = client.messages.create(
    model="claude-3-sonnet-20240229",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, world!"}
    ]
)
print(message.content[0].text)`;
    
    case 'azure_openai':
      return `import os
import openai

client = openai.AzureOpenAI(
    azure_endpoint="${baseUrl}",
    api_key=os.getenv("AZURE_OPENAI_API_KEY", "YOUR_AZURE_API_KEY"),
    api_version="2023-12-01-preview"
)

response = client.chat.completions.create(
    model=os.getenv("AZURE_DEPLOYMENT_NAME", "YOUR_DEPLOYMENT_NAME"),
    messages=[
        {"role": "user", "content": "Hello, world!"}
    ]
)
print(response.choices[0].message.content)`;
    
    case 'bedrock':
      return `import os
import boto3
import json

client = boto3.client('bedrock-runtime',
    region_name=os.getenv("AWS_REGION", "us-east-1"),
    endpoint_url="${baseUrl}",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

response = client.invoke_model(
    modelId='anthropic.claude-3-sonnet-20240229-v1:0',
    body=json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": "Hello, world!"}
        ]
    })
)
print(json.loads(response['body'].read())['content'][0]['text'])`;
    
    case 'vertex_ai':
      return `import os
import requests

headers = {
    'Authorization': f'Bearer {os.getenv("GOOGLE_ACCESS_TOKEN", "YOUR_ACCESS_TOKEN")}',
    'Content-Type': 'application/json'
}

data = {
    'contents': [{
        'parts': [{'text': 'Hello, world!'}]
    }]
}

project = os.getenv("GOOGLE_CLOUD_PROJECT", "YOUR_PROJECT")
response = requests.post(
    f'${baseUrl}/projects/{project}/locations/us-central1/publishers/google/models/gemini-pro:generateContent',
    headers=headers,
    json=data
)
print(response.json()['candidates'][0]['content']['parts'][0]['text'])`;
    
    case 'deepseek':
      return `import os
import openai

client = openai.OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY", "YOUR_DEEPSEEK_API_KEY"),
    base_url="${baseUrl}/v1"
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "Hello, world!"}
    ]
)
print(response.choices[0].message.content)`;
    
    default:
      return `import os
import requests

response = requests.post('${baseUrl}/your-endpoint',
    headers={
        'Authorization': f'Bearer {os.getenv("API_KEY", "YOUR_API_KEY")}',
        'Content-Type': 'application/json'
    },
    json={'message': 'Hello, world!'}
)
print(response.json())`;
  }
};

const generateJavaScriptExample = (proxy: Proxy): string => {
  const baseUrl = `http://localhost:${proxy.port}`;
  
  switch (proxy.provider.toLowerCase()) {
    case 'openai':
      return `import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY || 'YOUR_OPENAI_API_KEY',
  baseURL: '${baseUrl}/v1'
});

const response = await openai.chat.completions.create({
  model: 'gpt-4',
  messages: [
    { role: 'user', content: 'Hello, world!' }
  ]
});

console.log(response.choices[0].message.content);`;
    
    case 'anthropic':
      return `import Anthropic from '@anthropic-ai/sdk';

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY || 'YOUR_ANTHROPIC_API_KEY',
  baseURL: '${baseUrl}'
});

const message = await anthropic.messages.create({
  model: 'claude-3-sonnet-20240229',
  max_tokens: 1024,
  messages: [
    { role: 'user', content: 'Hello, world!' }
  ]
});

console.log(message.content[0].text);`;
    
    case 'azure_openai':
      return `import { AzureOpenAI } from 'openai';

const client = new AzureOpenAI({
  endpoint: '${baseUrl}',
  apiKey: process.env.AZURE_OPENAI_API_KEY || 'YOUR_AZURE_API_KEY',
  apiVersion: '2023-12-01-preview'
});

const response = await client.chat.completions.create({
  model: process.env.AZURE_DEPLOYMENT_NAME || 'YOUR_DEPLOYMENT_NAME',
  messages: [
    { role: 'user', content: 'Hello, world!' }
  ]
});

console.log(response.choices[0].message.content);`;
    
    case 'bedrock':
      return `import { BedrockRuntimeClient, InvokeModelCommand } from '@aws-sdk/client-bedrock-runtime';

const client = new BedrockRuntimeClient({
  region: process.env.AWS_REGION || 'us-east-1',
  endpoint: '${baseUrl}',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
  }
});

const command = new InvokeModelCommand({
  modelId: 'anthropic.claude-3-sonnet-20240229-v1:0',
  body: JSON.stringify({
    anthropic_version: 'bedrock-2023-05-31',
    max_tokens: 1024,
    messages: [
      { role: 'user', content: 'Hello, world!' }
    ]
  })
});

const response = await client.send(command);
const result = JSON.parse(new TextDecoder().decode(response.body));
console.log(result.content[0].text);`;
    
    case 'vertex_ai':
      return `const project = process.env.GOOGLE_CLOUD_PROJECT || 'YOUR_PROJECT';
const accessToken = process.env.GOOGLE_ACCESS_TOKEN || 'YOUR_ACCESS_TOKEN';

const response = await fetch(\`\${baseUrl}/projects/\${project}/locations/us-central1/publishers/google/models/gemini-pro:generateContent\`, {
  method: 'POST',
  headers: {
    'Authorization': \`Bearer \${accessToken}\`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    contents: [{
      parts: [{ text: 'Hello, world!' }]
    }]
  })
});

const data = await response.json();
console.log(data.candidates[0].content.parts[0].text);`;
    
    case 'deepseek':
      return `import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.DEEPSEEK_API_KEY || 'YOUR_DEEPSEEK_API_KEY',
  baseURL: '${baseUrl}/v1'
});

const response = await openai.chat.completions.create({
  model: 'deepseek-chat',
  messages: [
    { role: 'user', content: 'Hello, world!' }
  ]
});

console.log(response.choices[0].message.content);`;
    
    default:
      return `const response = await fetch('${baseUrl}/your-endpoint', {
  method: 'POST',
  headers: {
    'Authorization': \`Bearer \${process.env.API_KEY || 'YOUR_API_KEY'}\`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ message: 'Hello, world!' })
});

const data = await response.json();
console.log(data);`;
  }
};

// Syntax highlighting component
const CodeBlock: React.FC<{ 
  code: string; 
  language: string; 
  onCopy: (code: string, language: string) => void;
  isCopied: boolean;
}> = ({ code, language, onCopy, isCopied }) => {
  // Map our language names to Prism language identifiers
  const getLanguageId = (lang: string) => {
    switch (lang) {
      case 'curl':
        return 'bash';
      case 'javascript':
        return 'javascript';
      case 'python':
        return 'python';
      default:
        return 'text';
    }
  };

  return (
    <div className="relative">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-md font-medium text-gray-900 capitalize">{language}</h3>
        <button
          onClick={() => onCopy(code, language)}
          className="flex items-center space-x-1 px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
        >
          {isCopied ? (
            <>
              <CheckIcon className="h-3 w-3 text-green-600" />
              <span className="text-green-600">Copied!</span>
            </>
          ) : (
            <>
              <ClipboardDocumentIcon className="h-3 w-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <div className="rounded-lg border overflow-hidden">
        <SyntaxHighlighter
          language={getLanguageId(language)}
          style={oneLight}
          customStyle={{
            margin: 0,
            padding: '1rem',
            fontSize: '0.875rem',
            lineHeight: '1.25rem'
          }}
        >
          {code}
        </SyntaxHighlighter>
      </div>
    </div>
  );
};

const Proxies: React.FC = () => {
  usePageTitle('Proxies');
  
  const [proxies, setProxies] = useState<Proxy[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [selectedProxy, setSelectedProxy] = useState<Proxy | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCodeModal, setShowCodeModal] = useState(false);
  const [codeModalProxy, setCodeModalProxy] = useState<Proxy | null>(null);
  const [copiedCode, setCopiedCode] = useState<string | null>(null);
  const [showCacheInfoModal, setShowCacheInfoModal] = useState(false);
  const [cacheInfoProxy, setCacheInfoProxy] = useState<Proxy | null>(null);
  const [cacheStats, setCacheStats] = useState<any>(null);
  const [isLoadingCacheStats, setIsLoadingCacheStats] = useState(false);
  
  // Create proxy form state
  const [providers, setProviders] = useState<string[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  
  // WebSocket temporarily disabled - using polling instead
  const isConnected = false;
  
  const [formData, setFormData] = useState({
    name: '',
    provider: '',
    description: '',
    port: ''
  });

  useEffect(() => {
    loadProxies();
    loadProviders();
  }, []);

  const loadProviders = async () => {
    try {
      const data = await apiClient.getProviders();
      setProviders(data.providers);
    } catch (error) {
      console.error('Failed to load providers:', error);
    }
  };

  const loadProxies = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient.getProxies();
      
      // Load failure_config for each proxy to enable feature indicators
      const proxiesWithConfig = await Promise.all(
        data.map(async (proxy: Proxy) => {
          try {
            const configResponse = await apiClient.getProxyFailureConfig(proxy.id);
            return {
              ...proxy,
              failure_config: configResponse.failure_config
            };
          } catch (error) {
            // If config fails to load, return proxy without config
            console.warn(`Failed to load config for proxy ${proxy.id}:`, error);
            return proxy;
          }
        })
      );
      
      setProxies(proxiesWithConfig);
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
                         (proxy.description || '').toLowerCase().includes(searchTerm.toLowerCase());
    
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
    setSelectedProxy(proxy);
    setShowConfigModal(true);
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

  const handleOpenCreateModal = () => {
    setFormData({
      name: '',
      provider: providers[0] || '',
      description: '',
      port: ''
    });
    setShowCreateModal(true);
  };

  const handleClearProxyCache = async (proxy: Proxy) => {
    if (confirm(`Are you sure you want to clear the cache for "${proxy.name}"? This action cannot be undone.`)) {
      try {
        await apiClient.invalidateCache(proxy.id);
        alert(`Cache cleared for ${proxy.name}`);
      } catch (error) {
        console.error('Failed to clear cache:', error);
        if (error instanceof ApiError) {
          alert(`Failed to clear cache: ${error.message}`);
        }
      }
    }
  };

  const handleShowCode = (proxy: Proxy) => {
    setCodeModalProxy(proxy);
    setShowCodeModal(true);
  };

  const handleShowCacheInfo = async (proxy: Proxy) => {
    setCacheInfoProxy(proxy);
    setShowCacheInfoModal(true);
    setIsLoadingCacheStats(true);
    
    try {
      const stats = await apiClient.getCacheStats(proxy.id);
      setCacheStats(stats);
    } catch (error) {
      console.error('Failed to load cache stats:', error);
      setCacheStats({ error: 'Failed to load cache statistics' });
    } finally {
      setIsLoadingCacheStats(false);
    }
  };

  const copyToClipboard = async (code: string, language: string) => {
    try {
      await navigator.clipboard.writeText(code);
      setCopiedCode(language);
      setTimeout(() => setCopiedCode(null), 2000);
    } catch (error) {
      console.error('Failed to copy code:', error);
    }
  };

  // Handle ESC key to close modals
  useEffect(() => {
    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        if (showCodeModal) {
          setShowCodeModal(false);
          setCopiedCode(null);
        }
        if (showCacheInfoModal) {
          setShowCacheInfoModal(false);
          setCacheStats(null);
        }
      }
    };

    if (showCodeModal || showCacheInfoModal) {
      document.addEventListener('keydown', handleEscapeKey);
    }

    return () => {
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, [showCodeModal, showCacheInfoModal]);

  const handleCloseCreateModal = () => {
    setShowCreateModal(false);
    setFormData({
      name: '',
      provider: '',
      description: '',
      port: ''
    });
  };

  const handleFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCreateProxy = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsCreating(true);

    try {
      const proxyData: any = {
        name: formData.name,
        provider: formData.provider,
        description: formData.description
      };

      // Only include port if provided
      if (formData.port && formData.port.trim()) {
        proxyData.port = parseInt(formData.port);
      }

      await apiClient.createProxy(proxyData);
      await loadProxies(); // Refresh the list
      handleCloseCreateModal();
    } catch (error) {
      console.error('Failed to create proxy:', error);
      if (error instanceof ApiError) {
        alert(`Failed to create proxy: ${error.message}`);
      }
    } finally {
      setIsCreating(false);
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
          <div className="flex items-center space-x-4 mt-1">
            <p className="text-gray-600">
              Manage your LLM proxy instances • {runningCount} running, {stoppedCount} stopped
            </p>
            <div className="flex items-center space-x-1 text-sm text-gray-500">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'}`}></div>
              <span>
                {isConnected ? 'Live updates' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
        <button
          onClick={handleOpenCreateModal}
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
              onClick={handleOpenCreateModal}
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
              onClearCache={handleClearProxyCache}
              onShowCode={handleShowCode}
              onShowCacheInfo={handleShowCacheInfo}
            />
          ))}
        </div>
      )}

      {/* Create Proxy Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <form onSubmit={handleCreateProxy}>
              {/* Modal Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200">
                <h2 className="text-lg font-semibold text-gray-900">Create New Proxy</h2>
                <button
                  type="button"
                  onClick={handleCloseCreateModal}
                  className="text-gray-400 hover:text-gray-500"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              {/* Modal Body */}
              <div className="p-6 space-y-4">
                {/* Proxy Name */}
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
                    Proxy Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleFormChange}
                    required
                    className="input-field"
                    placeholder="e.g., My OpenAI Proxy"
                  />
                </div>

                {/* Provider */}
                <div>
                  <label htmlFor="provider" className="block text-sm font-medium text-gray-700 mb-1">
                    Provider <span className="text-red-500">*</span>
                  </label>
                  <select
                    id="provider"
                    name="provider"
                    value={formData.provider}
                    onChange={handleFormChange}
                    required
                    className="input-field"
                  >
                    <option value="">Select a provider</option>
                    {providers.map((provider) => (
                      <option key={provider} value={provider}>
                        {provider.charAt(0).toUpperCase() + provider.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>


                {/* Port (Optional) */}
                <div>
                  <label htmlFor="port" className="block text-sm font-medium text-gray-700 mb-1">
                    Port (Optional)
                  </label>
                  <input
                    type="number"
                    id="port"
                    name="port"
                    value={formData.port}
                    onChange={handleFormChange}
                    min="1024"
                    max="65535"
                    className="input-field"
                    placeholder="Auto-assigned if not specified"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Leave empty to auto-assign an available port.
                  </p>
                </div>

                {/* Description */}
                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                    Description (Optional)
                  </label>
                  <textarea
                    id="description"
                    name="description"
                    value={formData.description}
                    onChange={handleFormChange}
                    rows={3}
                    className="input-field"
                    placeholder="Describe this proxy's purpose or configuration..."
                  />
                </div>
              </div>

              {/* Modal Footer */}
              <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200">
                <button
                  type="button"
                  onClick={handleCloseCreateModal}
                  disabled={isCreating}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreating || !formData.name || !formData.provider}
                  className="btn-primary flex items-center space-x-2"
                >
                  {isCreating && (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  )}
                  <span>{isCreating ? 'Creating...' : 'Create Proxy'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Configuration Modal */}
      {selectedProxy && (
        <ProxyConfigModal
          proxy={selectedProxy}
          isOpen={showConfigModal}
          onClose={() => {
            setShowConfigModal(false);
            setSelectedProxy(null);
          }}
          onUpdate={loadProxies}
        />
      )}

      {/* Code Modal */}
      {showCodeModal && codeModalProxy && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                Code Examples - {codeModalProxy.name}
              </h2>
              <button
                onClick={() => setShowCodeModal(false)}
                className="text-gray-400 hover:text-gray-500"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-6">
              <p className="text-gray-600">
                Here are code examples to connect to your {codeModalProxy.provider} proxy running on port {codeModalProxy.port}:
              </p>

              {/* cURL Example */}
              <CodeBlock
                code={generateCurlExample(codeModalProxy)}
                language="curl"
                onCopy={copyToClipboard}
                isCopied={copiedCode === 'curl'}
              />

              {/* Python Example */}
              <CodeBlock
                code={generatePythonExample(codeModalProxy)}
                language="python"
                onCopy={copyToClipboard}
                isCopied={copiedCode === 'python'}
              />

              {/* JavaScript Example */}
              <CodeBlock
                code={generateJavaScriptExample(codeModalProxy)}
                language="javascript"
                onCopy={copyToClipboard}
                isCopied={copiedCode === 'javascript'}
              />
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200">
              <button
                onClick={() => setShowCodeModal(false)}
                className="btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Cache Info Modal */}
      {showCacheInfoModal && cacheInfoProxy && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-md max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">
                Cache Information - {cacheInfoProxy.name}
              </h2>
              <button
                onClick={() => {
                  setShowCacheInfoModal(false);
                  setCacheStats(null);
                }}
                className="text-gray-400 hover:text-gray-500"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6">
              {isLoadingCacheStats ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-3 text-gray-600">Loading cache information...</span>
                </div>
              ) : cacheStats?.error ? (
                <div className="text-center py-8">
                  <div className="text-red-500 text-sm">{cacheStats.error}</div>
                </div>
              ) : cacheStats ? (
                <div className="space-y-4">
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-gray-700">Cached Prompts</span>
                      <span className="text-2xl font-bold text-blue-600">
                        {cacheStats.cache_stats?.total_entries || 0}
                      </span>
                    </div>
                  </div>
                  
                  {cacheStats.cache_stats?.total_size && (
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">Cache Size</span>
                        <span className="text-lg font-semibold text-gray-900">
                          {(cacheStats.cache_stats.total_size / 1024 / 1024).toFixed(2)} MB
                        </span>
                      </div>
                    </div>
                  )}
                  
                  {cacheStats.cache_stats?.hit_rate !== undefined && (
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-700">Hit Rate</span>
                        <span className="text-lg font-semibold text-green-600">
                          {(cacheStats.cache_stats.hit_rate * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  )}
                  
                  <div className="text-xs text-gray-500 text-center mt-4">
                    Proxy running on port {cacheInfoProxy.port}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <div className="text-gray-500 text-sm">No cache information available</div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end space-x-3 p-6 border-t border-gray-200">
              <button
                onClick={() => {
                  setShowCacheInfoModal(false);
                  setCacheStats(null);
                }}
                className="btn-secondary"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Proxies;