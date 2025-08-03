import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProxyConfigModal from '../components/ProxyConfigModal';
import type { Proxy, FailureConfig } from '../types';

const mockFailureConfig: FailureConfig = {
  timeout_enabled: false,
  timeout_seconds: 5,
  timeout_rate: 0.0,
  error_injection_enabled: false,
  error_rates: {},
  ip_filtering_enabled: false,
  ip_allowlist: [],
  ip_blocklist: [],
  rate_limiting_enabled: false,
  requests_per_minute: 60,
  response_delay_enabled: false,
  response_delay_min_seconds: 0.5,
  response_delay_max_seconds: 2.0,
  response_delay_cache_only: true,
};

const mockProxy: Proxy = {
  id: 1,
  name: 'Test Proxy',
  provider: 'openai',
  description: 'Test proxy description',
  tags: ['test'],
  port: 8001,
  status: 'running',
  user_id: '1',
  failure_config: mockFailureConfig,
};

const mockHandlers = {
  onClose: vi.fn(),
  onSave: vi.fn(),
  onUpdate: vi.fn(),
};

describe('ProxyConfigModal - Response Delay', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders response delay section', () => {
    render(
      <ProxyConfigModal
        isOpen={true}
        proxy={mockProxy}
        {...mockHandlers}
      />
    );

    expect(screen.getByText('Response Delay')).toBeInTheDocument();
    expect(screen.getByText('Simulate realistic response times for cached responses')).toBeInTheDocument();
  });

  it('shows response delay toggle switch', () => {
    render(
      <ProxyConfigModal
        isOpen={true}
        proxy={mockProxy}
        {...mockHandlers}
      />
    );

    const toggle = screen.getByRole('checkbox', { name: /enable response delay/i });
    expect(toggle).toBeInTheDocument();
    expect(toggle).not.toBeChecked();
  });

  it('shows response delay controls when enabled', async () => {
    const user = userEvent.setup();
    
    render(
      <ProxyConfigModal
        isOpen={true}
        proxy={mockProxy}
        {...mockHandlers}
      />
    );

    const toggle = screen.getByRole('checkbox', { name: /enable response delay/i });
    await user.click(toggle);

    // Should show min/max inputs
    expect(screen.getByLabelText(/minimum delay/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/maximum delay/i)).toBeInTheDocument();
    
    // Should show cache-only checkbox
    expect(screen.getByRole('checkbox', { name: /apply only to cache hits/i })).toBeInTheDocument();
  });

  it('hides response delay controls when disabled', () => {
    render(
      <ProxyConfigModal
        isOpen={true}
        proxy={mockProxy}
        {...mockHandlers}
      />
    );

    // Should not show delay inputs when disabled
    expect(screen.queryByLabelText(/minimum delay/i)).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/maximum delay/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('checkbox', { name: /apply only to cache hits/i })).not.toBeInTheDocument();
  });

  it('displays correct default values when enabled', async () => {
    const user = userEvent.setup();
    
    render(
      <ProxyConfigModal
        isOpen={true}
        proxy={mockProxy}
        {...mockHandlers}
      />
    );

    const toggle = screen.getByRole('checkbox', { name: /enable response delay/i });
    await user.click(toggle);

    const minInput = screen.getByLabelText(/minimum delay/i) as HTMLInputElement;
    const maxInput = screen.getByLabelText(/maximum delay/i) as HTMLInputElement;
    const cacheOnlyCheckbox = screen.getByRole('checkbox', { name: /apply only to cache hits/i });

    expect(minInput.value).toBe('0.5');
    expect(maxInput.value).toBe('2.0');
    expect(cacheOnlyCheckbox).toBeChecked();
  });

  it('displays existing config values correctly', () => {
    const proxyWithDelay = {
      ...mockProxy,
      failure_config: {
        ...mockFailureConfig,
        response_delay_enabled: true,
        response_delay_min_seconds: 1.5,
        response_delay_max_seconds: 3.0,
        response_delay_cache_only: false,
      },
    };

    render(
      <ProxyConfigModal
        isOpen={true}
        proxy={proxyWithDelay}
        {...mockHandlers}
      />
    );

    const toggle = screen.getByRole('checkbox', { name: /enable response delay/i });
    expect(toggle).toBeChecked();

    const minInput = screen.getByLabelText(/minimum delay/i) as HTMLInputElement;
    const maxInput = screen.getByLabelText(/maximum delay/i) as HTMLInputElement;
    const cacheOnlyCheckbox = screen.getByRole('checkbox', { name: /apply only to cache hits/i });

    expect(minInput.value).toBe('1.5');
    expect(maxInput.value).toBe('3.0');
    expect(cacheOnlyCheckbox).not.toBeChecked();
  });

  it('allows updating delay values', async () => {
    const user = userEvent.setup();
    
    render(
      <ProxyConfigModal
        isOpen={true}
        proxy={mockProxy}
        {...mockHandlers}
      />
    );

    // Enable response delay
    const toggle = screen.getByRole('checkbox', { name: /enable response delay/i });
    await user.click(toggle);

    // Update min delay
    const minInput = screen.getByLabelText(/minimum delay/i);
    await user.clear(minInput);
    await user.type(minInput, '1.0');

    // Update max delay
    const maxInput = screen.getByLabelText(/maximum delay/i);
    await user.clear(maxInput);
    await user.type(maxInput, '5.0');

    // Toggle cache-only
    const cacheOnlyCheckbox = screen.getByRole('checkbox', { name: /apply only to cache hits/i });
    await user.click(cacheOnlyCheckbox);

    expect(minInput).toHaveValue(1.0);
    expect(maxInput).toHaveValue(5.0);
    expect(cacheOnlyCheckbox).not.toBeChecked();
  });

  it('validates delay values on save', async () => {
    const user = userEvent.setup();
    
    render(
      <ProxyConfigModal
        isOpen={true}
        proxy={mockProxy}
        {...mockHandlers}
      />
    );

    // Enable response delay
    const toggle = screen.getByRole('checkbox', { name: /enable response delay/i });
    await user.click(toggle);

    // Set invalid values (min > max)
    const minInput = screen.getByLabelText(/minimum delay/i);
    const maxInput = screen.getByLabelText(/maximum delay/i);
    
    await user.clear(minInput);
    await user.type(minInput, '5.0');
    await user.clear(maxInput);
    await user.type(maxInput, '2.0');

    // Try to save
    const saveButton = screen.getByText('Save Configuration');
    await user.click(saveButton);

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/minimum.*must be less than.*maximum/i)).toBeInTheDocument();
    });

    // Should not call onSave
    expect(mockHandlers.onSave).not.toHaveBeenCalled();
  });

  it('validates negative delay values', async () => {
    const user = userEvent.setup();
    
    render(
      <ProxyConfigModal
        isOpen={true}
        proxy={mockProxy}
        {...mockHandlers}
      />
    );

    // Enable response delay
    const toggle = screen.getByRole('checkbox', { name: /enable response delay/i });
    await user.click(toggle);

    // Set negative value
    const minInput = screen.getByLabelText(/minimum delay/i);
    await user.clear(minInput);
    await user.type(minInput, '-1.0');

    // Try to save
    const saveButton = screen.getByText('Save Configuration');
    await user.click(saveButton);

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/delay.*must be.*non-negative/i)).toBeInTheDocument();
    });

    expect(mockHandlers.onSave).not.toHaveBeenCalled();
  });

  it('validates maximum delay limit', async () => {
    const user = userEvent.setup();
    
    render(
      <ProxyConfigModal
        isOpen={true}
        proxy={mockProxy}
        {...mockHandlers}
      />
    );

    // Enable response delay
    const toggle = screen.getByRole('checkbox', { name: /enable response delay/i });
    await user.click(toggle);

    // Set value above limit
    const maxInput = screen.getByLabelText(/maximum delay/i);
    await user.clear(maxInput);
    await user.type(maxInput, '35.0');

    // Try to save
    const saveButton = screen.getByText('Save Configuration');
    await user.click(saveButton);

    // Should show validation error
    await waitFor(() => {
      expect(screen.getByText(/maximum.*cannot exceed.*30.*seconds/i)).toBeInTheDocument();
    });

    expect(mockHandlers.onSave).not.toHaveBeenCalled();
  });

  it('saves valid response delay configuration', async () => {
    const user = userEvent.setup();
    
    render(
      <ProxyConfigModal
        isOpen={true}
        proxy={mockProxy}
        {...mockHandlers}
      />
    );

    // Enable response delay
    const toggle = screen.getByRole('checkbox', { name: /enable response delay/i });
    await user.click(toggle);

    // Set valid values
    const minInput = screen.getByLabelText(/minimum delay/i);
    const maxInput = screen.getByLabelText(/maximum delay/i);
    
    await user.clear(minInput);
    await user.type(minInput, '1.0');
    await user.clear(maxInput);
    await user.type(maxInput, '3.0');

    // Disable cache-only
    const cacheOnlyCheckbox = screen.getByRole('checkbox', { name: /apply only to cache hits/i });
    await user.click(cacheOnlyCheckbox);

    // Save
    const saveButton = screen.getByText('Save Configuration');
    await user.click(saveButton);

    // Should call onSave with updated config
    await waitFor(() => {
      expect(mockHandlers.onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          failure_config: expect.objectContaining({
            response_delay_enabled: true,
            response_delay_min_seconds: 1.0,
            response_delay_max_seconds: 3.0,
            response_delay_cache_only: false,
          }),
        })
      );
    });
  });

  it('shows helper text for response delay', async () => {
    const user = userEvent.setup();
    
    render(
      <ProxyConfigModal
        isOpen={true}
        proxy={mockProxy}
        {...mockHandlers}
      />
    );

    // Enable response delay
    const toggle = screen.getByRole('checkbox', { name: /enable response delay/i });
    await user.click(toggle);

    // Should show helper text
    expect(screen.getByText(/minimum delay in seconds/i)).toBeInTheDocument();
    expect(screen.getByText(/maximum delay in seconds/i)).toBeInTheDocument();
    expect(screen.getByText(/when enabled.*only cache hits.*delayed/i)).toBeInTheDocument();
  });

  it('allows zero delay values', async () => {
    const user = userEvent.setup();
    
    render(
      <ProxyConfigModal
        isOpen={true}
        proxy={mockProxy}
        {...mockHandlers}
      />
    );

    // Enable response delay
    const toggle = screen.getByRole('checkbox', { name: /enable response delay/i });
    await user.click(toggle);

    // Set zero values
    const minInput = screen.getByLabelText(/minimum delay/i);
    const maxInput = screen.getByLabelText(/maximum delay/i);
    
    await user.clear(minInput);
    await user.type(minInput, '0.0');
    await user.clear(maxInput);
    await user.type(maxInput, '0.0');

    // Save
    const saveButton = screen.getByText('Save Configuration');
    await user.click(saveButton);

    // Should save successfully
    await waitFor(() => {
      expect(mockHandlers.onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          failure_config: expect.objectContaining({
            response_delay_enabled: true,
            response_delay_min_seconds: 0.0,
            response_delay_max_seconds: 0.0,
          }),
        })
      );
    });
  });

  it('allows equal min and max values', async () => {
    const user = userEvent.setup();
    
    render(
      <ProxyConfigModal
        isOpen={true}
        proxy={mockProxy}
        {...mockHandlers}
      />
    );

    // Enable response delay
    const toggle = screen.getByRole('checkbox', { name: /enable response delay/i });
    await user.click(toggle);

    // Set equal values
    const minInput = screen.getByLabelText(/minimum delay/i);
    const maxInput = screen.getByLabelText(/maximum delay/i);
    
    await user.clear(minInput);
    await user.type(minInput, '2.5');
    await user.clear(maxInput);
    await user.type(maxInput, '2.5');

    // Save
    const saveButton = screen.getByText('Save Configuration');
    await user.click(saveButton);

    // Should save successfully
    await waitFor(() => {
      expect(mockHandlers.onSave).toHaveBeenCalledWith(
        expect.objectContaining({
          failure_config: expect.objectContaining({
            response_delay_enabled: true,
            response_delay_min_seconds: 2.5,
            response_delay_max_seconds: 2.5,
          }),
        })
      );
    });
  });
});