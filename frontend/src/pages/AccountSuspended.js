import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { ShieldAlert, Mail, ArrowLeft } from 'lucide-react';
import { getSuspensionInfo, clearSuspensionInfo } from '../lib/suspensionGuard';

function formatDateTime(iso) {
  if (!iso) return null;
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export default function AccountSuspended() {
  const navigate = useNavigate();
  const [info, setInfo] = useState(() => getSuspensionInfo());

  // Re-read on mount in case session storage updates after first paint.
  useEffect(() => {
    setInfo(getSuspensionInfo());
  }, []);

  const handleBackToLogin = () => {
    clearSuspensionInfo();
    navigate('/login');
  };

  const reason = info?.reason || 'No reason provided.';
  const message =
    info?.message ||
    'This account has been suspended. Please contact support to restore access.';
  const suspendedAt = formatDateTime(info?.suspended_at);

  return (
    <div
      className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 via-orange-50 to-yellow-50 p-6"
      data-testid="account-suspended-page"
    >
      <Card className="max-w-lg w-full border-red-200 shadow-lg">
        <CardContent className="pt-8 pb-8">
          <div className="flex flex-col items-center text-center">
            <div className="bg-red-100 rounded-full p-4 mb-4">
              <ShieldAlert className="w-10 h-10 text-red-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              Account Suspended
            </h1>
            <p className="text-gray-700 mb-6">{message}</p>

            <div className="w-full bg-red-50 border border-red-200 rounded-lg p-4 mb-6 text-left">
              <div className="text-xs uppercase tracking-wide text-red-700 font-semibold mb-1">
                Reason
              </div>
              <div
                className="text-gray-900"
                data-testid="account-suspended-reason"
              >
                {reason}
              </div>
              {suspendedAt && (
                <div className="text-xs text-gray-500 mt-3">
                  Suspended on {suspendedAt}
                </div>
              )}
            </div>

            <div className="flex flex-col sm:flex-row gap-3 w-full">
              <Button
                variant="outline"
                className="flex-1"
                onClick={handleBackToLogin}
                data-testid="account-suspended-back-to-login-btn"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Login
              </Button>
              <Button
                className="flex-1 bg-red-600 hover:bg-red-700"
                onClick={() =>
                  (window.location.href =
                    'mailto:support@signguy.ai?subject=Account%20Suspended')
                }
                data-testid="account-suspended-contact-support-btn"
              >
                <Mail className="w-4 h-4 mr-2" />
                Contact Support
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
