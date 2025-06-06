import { render, screen, fireEvent } from '@testing-library/react';
import ProxyCard from '../components/ProxyCard';
import type { Proxy } from '../types';

const mockProxy: Proxy = {
  id: 1,
  name: 'Test Proxy',
  provider: 'openai',
  description: 'Test proxy description',
  tags: ['test', 'development'],
  port: 8001,
  status: 'running',
  user_id: '1',
};

const mockHandlers = {
  onStart: vi.fn(),
  onStop: vi.fn(),
  onConfigure: vi.fn(),
  onDelete: vi.fn(),
  onClearCache: vi.fn(),
  onShowCode: vi.fn(),
  onShowCacheInfo: vi.fn(),
};

describe('ProxyCard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders proxy information correctly', () => {
    render(<ProxyCard proxy={mockProxy} {...mockHandlers} />);
    
    expect(screen.getByText('Test Proxy')).toBeInTheDocument();
    expect(screen.getByText('openai')).toBeInTheDocument();
    expect(screen.getByText('Test proxy description')).toBeInTheDocument();
    expect(screen.getByText('Port: 8001')).toBeInTheDocument();
    expect(screen.getByText('running')).toBeInTheDocument();
  });

  it('shows tags when present', () => {
    render(<ProxyCard proxy={mockProxy} {...mockHandlers} />);
    
    expect(screen.getByText('test')).toBeInTheDocument();
    expect(screen.getByText('development')).toBeInTheDocument();
  });

  it('shows stop button for running proxy', () => {
    render(<ProxyCard proxy={mockProxy} {...mockHandlers} />);
    
    expect(screen.getByText('Stop')).toBeInTheDocument();
    expect(screen.queryByText('Start')).not.toBeInTheDocument();
  });

  it('shows start button for stopped proxy', () => {
    const stoppedProxy = { ...mockProxy, status: 'stopped' as const };
    render(<ProxyCard proxy={stoppedProxy} {...mockHandlers} />);
    
    expect(screen.getByText('Start')).toBeInTheDocument();
    expect(screen.queryByText('Stop')).not.toBeInTheDocument();
  });

  it('calls onStop when stop button is clicked', () => {
    render(<ProxyCard proxy={mockProxy} {...mockHandlers} />);
    
    fireEvent.click(screen.getByText('Stop'));
    expect(mockHandlers.onStop).toHaveBeenCalledWith(mockProxy.id);
  });

  it('calls onConfigure when configure button is clicked', () => {
    render(<ProxyCard proxy={mockProxy} {...mockHandlers} />);
    
    fireEvent.click(screen.getByText('Configure'));
    expect(mockHandlers.onConfigure).toHaveBeenCalledWith(mockProxy);
  });

  it('calls onDelete when delete button is clicked', () => {
    render(<ProxyCard proxy={mockProxy} {...mockHandlers} />);
    
    fireEvent.click(screen.getByText('Delete'));
    expect(mockHandlers.onDelete).toHaveBeenCalledWith(mockProxy.id);
  });

  it('shows failure simulation indicator when active', () => {
    const proxyWithFailure = {
      ...mockProxy,
      failure_config: {
        timeout_enabled: true,
        timeout_rate: 0.1,
        error_injection_enabled: false,
        error_rates: {},
        ip_filtering_enabled: false,
        ip_allowlist: [],
        ip_blocklist: [],
        rate_limiting_enabled: false,
        requests_per_minute: 60,
      },
    };
    
    render(<ProxyCard proxy={proxyWithFailure} {...mockHandlers} />);
    
    expect(screen.getByText('Failure simulation active')).toBeInTheDocument();
  });
});