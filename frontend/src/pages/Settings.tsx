import React, { useState } from 'react';
import {
  UserPlusIcon,
  GlobeAltIcon,
  ShieldCheckIcon,
  KeyIcon,
  TrashIcon,
  UserIcon,
} from '@heroicons/react/24/outline';
import { apiClient, ApiError } from '../utils/api';
import { usePageTitle } from '../hooks/usePageTitle';

const Settings: React.FC = () => {
  usePageTitle('Settings');
  
  const [settings, setSettings] = useState({
    allowNewRegistrations: false,
    allowEmailPasswordLogin: true,
    allowGoogleLogin: true,
    allowGitHubLogin: true,
    globalIpAllowlist: ['192.168.0.0/16', '10.0.0.0/8'],
    globalIpBlocklist: ['0.0.0.0/0'],
    requireEmailVerification: true,
    sessionTimeout: 24, // hours
    maxProxiesPerUser: 10,
    enableMetricsCollection: true,
    enableDetailedLogging: true,
  });

  const [isLoading, setIsLoading] = useState(false);
  const [isClearingCache, setIsClearingCache] = useState(false);
  const [cacheMessage, setCacheMessage] = useState<string | null>(null);
  
  // Password change state
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState<string | null>(null);
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);

  const handleSettingsChange = (key: string, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const handleIpListChange = (listType: 'allowlist' | 'blocklist', value: string) => {
    const ips = value.split('\n').filter(ip => ip.trim());
    setSettings(prev => ({
      ...prev,
      [`globalIp${listType.charAt(0).toUpperCase() + listType.slice(1)}`]: ips
    }));
  };

  const handleSave = async () => {
    setIsLoading(true);
    try {
      // Mock API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('Settings saved:', settings);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearCache = async () => {
    setIsClearingCache(true);
    setCacheMessage(null);
    try {
      console.log('Attempting to clear cache...');
      const response = await apiClient.clearAllCache();
      console.log('Cache clear response:', response);
      setCacheMessage(`${response.message} (${response.entries_removed} entries removed)`);
    } catch (error) {
      console.error('Cache clear error:', error);
      console.error('Error details:', JSON.stringify(error, null, 2));
      if (error instanceof ApiError) {
        setCacheMessage(`Error (${error.status}): ${error.message}`);
      } else {
        setCacheMessage(`Failed to clear cache: ${error}`);
      }
    } finally {
      setIsClearingCache(false);
      // Clear message after 5 seconds
      setTimeout(() => setCacheMessage(null), 5000);
    }
  };

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsChangingPassword(true);
    setPasswordMessage(null);

    try {
      // Validate passwords match
      if (passwordForm.newPassword !== passwordForm.confirmPassword) {
        setPasswordMessage('New passwords do not match');
        return;
      }

      // Validate password length
      if (passwordForm.newPassword.length < 6) {
        setPasswordMessage('New password must be at least 6 characters long');
        return;
      }

      const response = await apiClient.changePassword(passwordForm.currentPassword, passwordForm.newPassword);
      setPasswordMessage('Password changed successfully');
      
      // Reset form
      setPasswordForm({
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
      });

      // Close modal after successful change
      setTimeout(() => {
        setIsPasswordModalOpen(false);
        setPasswordMessage(null);
      }, 2000);
      
    } catch (error) {
      console.error('Password change error:', error);
      if (error instanceof ApiError) {
        setPasswordMessage(`Error: ${error.message}`);
      } else {
        setPasswordMessage('Failed to change password');
      }
    } finally {
      setIsChangingPassword(false);
      // Clear message after 5 seconds
      setTimeout(() => setPasswordMessage(null), 5000);
    }
  };

  const handlePasswordFormChange = (field: string, value: string) => {
    setPasswordForm(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-1">Configure global system settings</p>
        </div>
        <button
          onClick={handleSave}
          disabled={isLoading}
          className="btn-primary"
        >
          {isLoading ? 'Saving...' : 'Save Settings'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Authentication Settings */}
        <div className="card space-y-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-50 text-blue-600 rounded-lg">
              <KeyIcon className="h-5 w-5" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900">Authentication</h2>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-900">Allow New Registrations</label>
                <p className="text-xs text-gray-500">Enable users to create new accounts</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.allowNewRegistrations}
                  onChange={(e) => handleSettingsChange('allowNewRegistrations', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-900">Email/Password Login</label>
                <p className="text-xs text-gray-500">Allow traditional email login</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.allowEmailPasswordLogin}
                  onChange={(e) => handleSettingsChange('allowEmailPasswordLogin', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-900">Google Login</label>
                <p className="text-xs text-gray-500">Enable Google OAuth</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.allowGoogleLogin}
                  onChange={(e) => handleSettingsChange('allowGoogleLogin', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-900">GitHub Login</label>
                <p className="text-xs text-gray-500">Enable GitHub OAuth</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.allowGitHubLogin}
                  onChange={(e) => handleSettingsChange('allowGitHubLogin', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-900">Require Email Verification</label>
                <p className="text-xs text-gray-500">Users must verify email</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.requireEmailVerification}
                  onChange={(e) => handleSettingsChange('requireEmailVerification', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>

        {/* Security Settings */}
        <div className="card space-y-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-green-50 text-green-600 rounded-lg">
              <ShieldCheckIcon className="h-5 w-5" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900">Security</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">
                Session Timeout (hours)
              </label>
              <input
                type="number"
                min="1"
                max="168"
                value={settings.sessionTimeout}
                onChange={(e) => handleSettingsChange('sessionTimeout', parseInt(e.target.value))}
                className="input-field"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">
                Max Proxies Per User
              </label>
              <input
                type="number"
                min="1"
                max="100"
                value={settings.maxProxiesPerUser}
                onChange={(e) => handleSettingsChange('maxProxiesPerUser', parseInt(e.target.value))}
                className="input-field"
              />
            </div>
          </div>
        </div>

        {/* Left Column: Account and System stacked */}
        <div className="space-y-6">
          {/* Account Settings */}
          <div className="card space-y-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-indigo-50 text-indigo-600 rounded-lg">
                <UserIcon className="h-5 w-5" />
              </div>
              <h2 className="text-lg font-semibold text-gray-900">Account</h2>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">Password</h3>
                  <p className="text-xs text-gray-500">Change your account password</p>
                </div>
                <button
                  onClick={() => setIsPasswordModalOpen(true)}
                  className="btn-secondary text-sm px-3 py-1.5"
                >
                  Change Password
                </button>
              </div>
            </div>
          </div>

          {/* System Settings */}
          <div className="card space-y-4">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-yellow-50 text-yellow-600 rounded-lg">
                <UserPlusIcon className="h-5 w-5" />
              </div>
              <h2 className="text-lg font-semibold text-gray-900">System</h2>
            </div>

            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-900">Enable Metrics Collection</label>
                  <p className="text-xs text-gray-500">Collect system performance metrics</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.enableMetricsCollection}
                    onChange={(e) => handleSettingsChange('enableMetricsCollection', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-900">Enable Detailed Logging</label>
                  <p className="text-xs text-gray-500">Log detailed request information</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.enableDetailedLogging}
                    onChange={(e) => handleSettingsChange('enableDetailedLogging', e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: IP Filtering */}
        <div className="card space-y-6">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-purple-50 text-purple-600 rounded-lg">
              <GlobeAltIcon className="h-5 w-5" />
            </div>
            <h2 className="text-lg font-semibold text-gray-900">Global IP Filtering</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">
                IP Allowlist
              </label>
              <textarea
                rows={4}
                value={settings.globalIpAllowlist.join('\n')}
                onChange={(e) => handleIpListChange('allowlist', e.target.value)}
                placeholder="192.168.0.0/16&#10;10.0.0.0/8&#10;172.16.0.1"
                className="input-field resize-none"
              />
              <p className="text-xs text-gray-500 mt-1">
                One IP/CIDR per line. Leave empty to allow all.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-900 mb-2">
                IP Blocklist
              </label>
              <textarea
                rows={4}
                value={settings.globalIpBlocklist.join('\n')}
                onChange={(e) => handleIpListChange('blocklist', e.target.value)}
                placeholder="192.168.1.100&#10;10.0.0.1"
                className="input-field resize-none"
              />
              <p className="text-xs text-gray-500 mt-1">
                One IP/CIDR per line. These IPs will be blocked.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Cache Management */}
      <div className="card">
        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2 bg-red-50 text-red-600 rounded-lg">
            <TrashIcon className="h-5 w-5" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900">Cache Management</h2>
        </div>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-gray-900">Clear All Cache</h3>
              <p className="text-xs text-gray-500">Remove all cached responses from your proxies</p>
            </div>
            <button
              onClick={handleClearCache}
              disabled={isClearingCache}
              className="btn-secondary text-red-600 border-red-200 hover:bg-red-50"
            >
              {isClearingCache ? 'Clearing...' : 'Clear Cache'}
            </button>
          </div>
          
          {cacheMessage && (
            <div className={`p-3 rounded-lg text-sm ${
              cacheMessage.startsWith('Error') 
                ? 'bg-red-50 text-red-700 border border-red-200' 
                : 'bg-green-50 text-green-700 border border-green-200'
            }`}>
              {cacheMessage}
            </div>
          )}
        </div>
      </div>

      {/* System Info */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Information</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Version:</span>
            <span className="ml-2 font-medium">0.1.0</span>
          </div>
          <div>
            <span className="text-gray-500">Database:</span>
            <span className="ml-2 font-medium">SQLite</span>
          </div>
          <div>
            <span className="text-gray-500">Uptime:</span>
            <span className="ml-2 font-medium">2d 14h 32m</span>
          </div>
        </div>
      </div>

      {/* Password Change Modal */}
      {isPasswordModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Change Password</h3>
              <button
                onClick={() => {
                  setIsPasswordModalOpen(false);
                  setPasswordMessage(null);
                  setPasswordForm({
                    currentPassword: '',
                    newPassword: '',
                    confirmPassword: '',
                  });
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handlePasswordChange} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Current Password
                </label>
                <input
                  type="password"
                  value={passwordForm.currentPassword}
                  onChange={(e) => handlePasswordFormChange('currentPassword', e.target.value)}
                  className="input-field"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  New Password
                </label>
                <input
                  type="password"
                  value={passwordForm.newPassword}
                  onChange={(e) => handlePasswordFormChange('newPassword', e.target.value)}
                  className="input-field"
                  minLength={6}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Confirm New Password
                </label>
                <input
                  type="password"
                  value={passwordForm.confirmPassword}
                  onChange={(e) => handlePasswordFormChange('confirmPassword', e.target.value)}
                  className="input-field"
                  minLength={6}
                  required
                />
              </div>

              {passwordMessage && (
                <div className={`p-3 rounded-lg text-sm ${
                  passwordMessage.includes('success') 
                    ? 'bg-green-50 text-green-700 border border-green-200' 
                    : 'bg-red-50 text-red-700 border border-red-200'
                }`}>
                  {passwordMessage}
                </div>
              )}

              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setIsPasswordModalOpen(false);
                    setPasswordMessage(null);
                    setPasswordForm({
                      currentPassword: '',
                      newPassword: '',
                      confirmPassword: '',
                    });
                  }}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isChangingPassword}
                  className="btn-primary flex-1"
                >
                  {isChangingPassword ? 'Changing...' : 'Change Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Settings;