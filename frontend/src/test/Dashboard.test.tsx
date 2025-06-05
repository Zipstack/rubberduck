import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../contexts/AuthContext';
import Dashboard from '../pages/Dashboard';

const DashboardWrapper = () => (
  <BrowserRouter>
    <AuthProvider>
      <Dashboard />
    </AuthProvider>
  </BrowserRouter>
);

describe('Dashboard', () => {
  it('renders dashboard title', () => {
    render(<DashboardWrapper />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Monitor your LLM proxy performance')).toBeInTheDocument();
  });

  it('displays stats cards', () => {
    render(<DashboardWrapper />);
    expect(screen.getByText('Total Proxies')).toBeInTheDocument();
    expect(screen.getByText('Cache Hit Rate')).toBeInTheDocument();
    expect(screen.getByText('Error Rate')).toBeInTheDocument();
    expect(screen.getByText('Total RPM')).toBeInTheDocument();
  });

  it('shows active proxies section', () => {
    render(<DashboardWrapper />);
    expect(screen.getByText('Active Proxies')).toBeInTheDocument();
  });

  it('shows recent activity section', () => {
    render(<DashboardWrapper />);
    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
  });
});