import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Search, Users, ChevronRight, Shield, ScrollText } from 'lucide-react';
import { toast } from 'sonner';
import { getAuthToken } from '../lib/authStorage';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function PlatformAdmin() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tenants, setTenants] = useState([]);
  const [filteredTenants, setFilteredTenants] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  // Redirect if not platform admin
  useEffect(() => {
    if (user && user.role !== 'platform_admin') {
      toast.error('Access denied: Platform Admin privileges required');
      navigate('/');
    }
  }, [user, navigate]);

  // Fetch tenants
  useEffect(() => {
    if (user?.role === 'platform_admin') {
      fetchTenants();
    }
  }, [user]);

  // Filter tenants based on search
  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredTenants(tenants);
    } else {
      const query = searchQuery.toLowerCase();
      const filtered = tenants.filter(
        (t) =>
          t.name.toLowerCase().includes(query) ||
          t.owner_email.toLowerCase().includes(query)
      );
      setFilteredTenants(filtered);
    }
  }, [searchQuery, tenants]);

  const fetchTenants = async () => {
    try {
      const token = getAuthToken();
      if (!token) {
        toast.error('Not authenticated');
        navigate('/login');
        return;
      }
      
      const response = await fetch(`${BACKEND_URL}/api/platform-admin/tenants`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch tenants');
      }

      const data = await response.json();
      setTenants(data);
      setFilteredTenants(data);
    } catch (error) {
      console.error('Error fetching tenants:', error);
      toast.error('Failed to load tenants');
    } finally {
      setLoading(false);
    }
  };

  if (user?.role !== 'platform_admin') {
    return null;
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-start justify-between gap-4 flex-wrap">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Shield className="w-8 h-8 text-blue-600" />
              <h1 className="text-3xl font-bold text-gray-900">Platform Admin</h1>
            </div>
            <p className="text-gray-600">
              Manage tenant accounts and provide support access
            </p>
          </div>
          <Button
            variant="outline"
            onClick={() => navigate('/platform-admin/audit-log')}
            data-testid="platform-admin-audit-log-btn"
          >
            <ScrollText className="w-4 h-4 mr-1" />
            View Audit Log
          </Button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Tenants</p>
                  <p className="text-2xl font-bold text-gray-900">{tenants.length}</p>
                </div>
                <Users className="w-8 h-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Active Accounts</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {tenants.filter((t) => t.plan !== 'free_trial').length}
                  </p>
                </div>
                <Users className="w-8 h-8 text-green-600" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">Total Users</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {tenants.reduce((sum, t) => sum + t.user_count, 0)}
                  </p>
                </div>
                <Users className="w-8 h-8 text-purple-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <Input
                type="text"
                placeholder="Search by business name or owner email..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </CardContent>
        </Card>

        {/* Tenant List */}
        <Card>
          <CardHeader>
            <CardTitle>Tenant Accounts</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                <p className="mt-4 text-gray-600">Loading tenants...</p>
              </div>
            ) : filteredTenants.length === 0 ? (
              <div className="text-center py-8">
                <Users className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No tenants found</p>
              </div>
            ) : (
              <div className="space-y-2">
                {filteredTenants.map((tenant) => (
                  <div
                    key={tenant.id}
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors cursor-pointer"
                    onClick={() => navigate(`/platform-admin/tenants/${tenant.id}`)}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <h3 className="font-semibold text-gray-900">{tenant.name}</h3>
                        {tenant.is_active === false && (
                          <span
                            className="inline-flex items-center text-xs font-semibold px-2 py-0.5 rounded-full bg-red-100 text-red-900 border border-red-200"
                            data-testid={`tenant-list-suspended-badge-${tenant.id}`}
                          >
                            Suspended
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600">{tenant.owner_email}</p>
                      {tenant.is_active === false && tenant.suspension_reason && (
                        <p className="text-xs text-red-700 mt-1">
                          Reason: {tenant.suspension_reason}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-700 capitalize">
                          {tenant.plan.replace(/_/g, ' ')}
                        </p>
                        <p className="text-xs text-gray-500">{tenant.user_count} users</p>
                      </div>
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
