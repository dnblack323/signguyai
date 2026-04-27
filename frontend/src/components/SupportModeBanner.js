import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, X, LogOut } from 'lucide-react';
import { Button } from './ui/button';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export function SupportModeBanner({ user }) {
  const navigate = useNavigate();
  const [exiting, setExiting] = useState(false);

  // Check if user is being impersonated
  const impersonation = user?.impersonation;
  if (!impersonation?.is_impersonating) {
    return null;
  }

  const handleExitSupportMode = async () => {
    if (!confirm('Exit support mode and return to Platform Admin?')) {
      return;
    }

    setExiting(true);
    try {
      // Get the original platform admin token
      const platformAdminToken = localStorage.getItem('platform_admin_token');

      if (platformAdminToken) {
        // Restore the original token
        localStorage.setItem('token', platformAdminToken);
        localStorage.removeItem('platform_admin_token');
        localStorage.removeItem('impersonation_active');

        toast.success('Exited support mode');

        // Redirect to platform admin
        window.location.href = '/platform-admin';
      } else {
        // No saved token, need to log out
        localStorage.removeItem('token');
        localStorage.removeItem('impersonation_active');
        toast.info('Please log in as Platform Admin');
        window.location.href = '/login';
      }
    } catch (error) {
      console.error('Error exiting support mode:', error);
      toast.error('Failed to exit support mode');
      setExiting(false);
    }
  };

  return (
    <div className="fixed top-0 left-0 right-0 z-50 bg-yellow-500 text-yellow-900 shadow-lg">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="w-5 h-5" />
            <div>
              <p className="font-semibold">
                Platform Admin Support Mode Active
              </p>
              <p className="text-sm">
                Viewing as <span className="font-medium">{user.full_name}</span> ({user.email})
                {' • '}
                Platform Admin: <span className="font-medium">{impersonation.platform_admin_email}</span>
              </p>
            </div>
          </div>
          <Button
            onClick={handleExitSupportMode}
            disabled={exiting}
            variant="secondary"
            size="sm"
            className="bg-yellow-600 hover:bg-yellow-700 text-white"
          >
            <LogOut className="w-4 h-4 mr-2" />
            {exiting ? 'Exiting...' : 'Exit Support Mode'}
          </Button>
        </div>
      </div>
    </div>
  );
}
