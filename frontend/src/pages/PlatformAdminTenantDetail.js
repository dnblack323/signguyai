import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import {
  ArrowLeft,
  Building2,
  Mail,
  Phone,
  Globe,
  MapPin,
  Users,
  LogIn,
  Shield,
  Calendar,
} from 'lucide-react';
import { toast } from 'sonner';
import { getAuthToken, setAuthToken } from '../lib/authStorage';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function PlatformAdminTenantDetail() {
  const { tenantId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tenant, setTenant] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [impersonating, setImpersonating] = useState(false);

  // Redirect if not platform admin
  useEffect(() => {
    if (user && user.role !== 'platform_admin') {
      toast.error('Access denied: Platform Admin privileges required');
      navigate('/');
    }
  }, [user, navigate]);

  // Fetch tenant details
  useEffect(() => {
    if (user?.role === 'platform_admin' && tenantId) {
      fetchTenantDetail();
    }
  }, [user, tenantId]);

  const fetchTenantDetail = async () => {
    try {
      const token = getAuthToken();
      if (!token) {
        toast.error('Not authenticated');
        navigate('/login');
        return;
      }
      
      const response = await fetch(
        `${BACKEND_URL}/api/platform-admin/tenants/${tenantId}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch tenant details');
      }

      const data = await response.json();
      setTenant(data.tenant);
      setUsers(data.users);
    } catch (error) {
      console.error('Error fetching tenant details:', error);
      toast.error('Failed to load tenant details');
    } finally {
      setLoading(false);
    }
  };

  const handleImpersonate = async (userId) => {
    if (!confirm('Are you sure you want to impersonate this user?')) {
      return;
    }

    setImpersonating(true);
    try {
      const token = getAuthToken();
      if (!token) {
        toast.error('Not authenticated');
        return;
      }
      
      const response = await fetch(
        `${BACKEND_URL}/api/platform-admin/impersonate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ target_user_id: userId }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to start impersonation');
      }

      const data = await response.json();

      // Store the original platform admin token
      localStorage.setItem('platform_admin_token', token);
      localStorage.setItem('impersonation_active', 'true');
      
      // Store the new impersonation token using authStorage
      setAuthToken(data.access_token, false);

      toast.success(
        `Now viewing as ${data.target_user.full_name} (${data.tenant.name})`
      );

      // Redirect to main dashboard
      window.location.href = '/';
    } catch (error) {
      console.error('Error starting impersonation:', error);
      toast.error('Failed to start impersonation');
      setImpersonating(false);
    }
  };

  if (user?.role !== 'platform_admin') {
    return null;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading tenant details...</p>
        </div>
      </div>
    );
  }

  if (!tenant) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Tenant not found</p>
          <Button
            onClick={() => navigate('/platform-admin')}
            className="mt-4"
          >
            Back to Platform Admin
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <Button
            variant="ghost"
            onClick={() => navigate('/platform-admin')}
            className="mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Tenant List
          </Button>
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">{tenant.name}</h1>
              <p className="text-gray-600">Tenant Details & Management</p>
            </div>
          </div>
        </div>

        {/* Tenant Overview */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Business Information</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="flex items-start gap-3">
                <Building2 className="w-5 h-5 text-gray-400 mt-1" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Business Name</p>
                  <p className="text-gray-900">{tenant.name}</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Mail className="w-5 h-5 text-gray-400 mt-1" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Owner Email</p>
                  <p className="text-gray-900">{tenant.owner_email}</p>
                </div>
              </div>

              {tenant.phone && (
                <div className="flex items-start gap-3">
                  <Phone className="w-5 h-5 text-gray-400 mt-1" />
                  <div>
                    <p className="text-sm font-medium text-gray-600">Phone</p>
                    <p className="text-gray-900">{tenant.phone}</p>
                  </div>
                </div>
              )}

              {tenant.website && (
                <div className="flex items-start gap-3">
                  <Globe className="w-5 h-5 text-gray-400 mt-1" />
                  <div>
                    <p className="text-sm font-medium text-gray-600">Website</p>
                    <a
                      href={tenant.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      {tenant.website}
                    </a>
                  </div>
                </div>
              )}

              {(tenant.address || tenant.city || tenant.state) && (
                <div className="flex items-start gap-3">
                  <MapPin className="w-5 h-5 text-gray-400 mt-1" />
                  <div>
                    <p className="text-sm font-medium text-gray-600">Address</p>
                    <p className="text-gray-900">
                      {tenant.address && <>{tenant.address}<br /></>}
                      {tenant.city && tenant.state && `${tenant.city}, ${tenant.state}`}
                    </p>
                  </div>
                </div>
              )}

              <div className="flex items-start gap-3">
                <Calendar className="w-5 h-5 text-gray-400 mt-1" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Plan</p>
                  <p className="text-gray-900 capitalize">
                    {tenant.plan.replace(/_/g, ' ')}
                  </p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <Calendar className="w-5 h-5 text-gray-400 mt-1" />
                <div>
                  <p className="text-sm font-medium text-gray-600">Created</p>
                  <p className="text-gray-900">
                    {new Date(tenant.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Users List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              Users ({users.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {users.length === 0 ? (
              <p className="text-gray-600 text-center py-8">No users found</p>
            ) : (
              <div className="space-y-2">
                {users.map((u) => (
                  <div
                    key={u.id}
                    className="flex items-center justify-between p-4 border rounded-lg"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900">{u.full_name}</h3>
                        <span
                          className={`text-xs px-2 py-1 rounded-full font-medium ${
                            u.role === 'owner'
                              ? 'bg-purple-100 text-purple-800'
                              : u.role === 'admin'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {u.role}
                        </span>
                        {!u.is_active && (
                          <span className="text-xs px-2 py-1 rounded-full font-medium bg-red-100 text-red-800">
                            Inactive
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600">{u.email}</p>
                    </div>
                    <Button
                      onClick={() => handleImpersonate(u.id)}
                      disabled={impersonating || !u.is_active}
                      variant="outline"
                      size="sm"
                      className="ml-4"
                    >
                      <LogIn className="w-4 h-4 mr-2" />
                      {impersonating ? 'Starting...' : 'Impersonate'}
                    </Button>
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
