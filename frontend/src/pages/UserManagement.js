import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '../components/ui/dialog';
import { Alert, AlertDescription } from '../components/ui/alert';
import { toast } from 'sonner';
import { Users, Key, UserCheck, UserX, Search, Shield, Loader2 } from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function UserManagement() {
  const { token, user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Reset password dialog
  const [resetDialog, setResetDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [resetting, setResetting] = useState(false);

  const fetchUsers = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/admin/users`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      }
    } catch (err) {
      console.error('Failed to fetch users:', err);
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleResetPassword = async () => {
    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    setResetting(true);
    try {
      const response = await fetch(`${API_URL}/api/admin/users/${selectedUser.id}/reset-password`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ new_password: newPassword })
      });

      if (response.ok) {
        toast.success(`Password reset for ${selectedUser.email}`);
        setResetDialog(false);
        setNewPassword('');
        setConfirmPassword('');
        setSelectedUser(null);
      } else {
        const data = await response.json();
        toast.error(data.detail || 'Failed to reset password');
      }
    } catch (err) {
      toast.error('Network error. Please try again.');
    } finally {
      setResetting(false);
    }
  };

  const handleToggleStatus = async (user, newStatus) => {
    try {
      const response = await fetch(`${API_URL}/api/admin/users/${user.id}/status?is_active=${newStatus}`, {
        method: 'PUT',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        toast.success(`User ${newStatus ? 'enabled' : 'disabled'}`);
        fetchUsers();
      } else {
        const data = await response.json();
        toast.error(data.detail || 'Failed to update user status');
      }
    } catch (err) {
      toast.error('Network error. Please try again.');
    }
  };

  const filteredUsers = users.filter(u => 
    u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (u.company_name && u.company_name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-primary)]">User Management</h1>
          <p className="text-[var(--text-secondary)] mt-1">Manage user accounts and reset passwords</p>
        </div>
      </div>

      {/* Search */}
      <Card className="bg-[var(--card-bg)] border-[var(--card-border)]">
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-secondary)]" />
            <Input
              placeholder="Search users by name, email, or company..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-[var(--input-bg)] border-[var(--input-border)] text-[var(--text-primary)]"
              data-testid="user-search-input"
            />
          </div>
        </CardContent>
      </Card>

      {/* Users List */}
      <Card className="bg-[var(--card-bg)] border-[var(--card-border)]">
        <CardHeader>
          <CardTitle className="text-[var(--text-primary)] flex items-center gap-2">
            <Users className="h-5 w-5 text-teal-500" />
            Users ({filteredUsers.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
            </div>
          ) : filteredUsers.length === 0 ? (
            <p className="text-center py-8 text-[var(--text-secondary)]">No users found</p>
          ) : (
            <div className="space-y-3">
              {filteredUsers.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between p-4 rounded-lg bg-[var(--bg-secondary)] border border-[var(--card-border)]"
                  data-testid={`user-row-${user.id}`}
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-full bg-teal-500/20 border border-teal-500/30 flex items-center justify-center">
                      <span className="text-teal-400 font-medium">
                        {user.full_name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-[var(--text-primary)]">{user.full_name}</span>
                        {user.id === currentUser?.id && (
                          <Badge className="bg-teal-500/20 text-teal-400 border-teal-500/30">You</Badge>
                        )}
                        {!user.is_active && (
                          <Badge variant="destructive" className="bg-red-500/20 text-red-400 border-red-500/30">Disabled</Badge>
                        )}
                      </div>
                      <p className="text-sm text-[var(--text-secondary)]">{user.email}</p>
                      {user.company_name && (
                        <p className="text-xs text-[var(--text-secondary)]">{user.company_name}</p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    {user.id !== currentUser?.id && (
                      <>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            setSelectedUser(user);
                            setResetDialog(true);
                          }}
                          className="border-[var(--card-border)] text-[var(--text-primary)]"
                          data-testid={`reset-password-btn-${user.id}`}
                        >
                          <Key className="h-4 w-4 mr-1" />
                          Reset Password
                        </Button>
                        <Button
                          variant={user.is_active ? "destructive" : "default"}
                          size="sm"
                          onClick={() => handleToggleStatus(user, !user.is_active)}
                          className={user.is_active ? "bg-red-500/20 text-red-400 hover:bg-red-500/30" : "bg-green-500/20 text-green-400 hover:bg-green-500/30"}
                          data-testid={`toggle-status-btn-${user.id}`}
                        >
                          {user.is_active ? (
                            <>
                              <UserX className="h-4 w-4 mr-1" />
                              Disable
                            </>
                          ) : (
                            <>
                              <UserCheck className="h-4 w-4 mr-1" />
                              Enable
                            </>
                          )}
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Reset Password Dialog */}
      <Dialog open={resetDialog} onOpenChange={setResetDialog}>
        <DialogContent className="bg-[var(--card-bg)] border-[var(--card-border)]">
          <DialogHeader>
            <DialogTitle className="text-[var(--text-primary)] flex items-center gap-2">
              <Shield className="h-5 w-5 text-teal-500" />
              Reset Password
            </DialogTitle>
            <DialogDescription className="text-[var(--text-secondary)]">
              Set a new password for {selectedUser?.full_name} ({selectedUser?.email})
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-[var(--text-primary)]">New Password</Label>
              <Input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Minimum 6 characters"
                className="bg-[var(--input-bg)] border-[var(--input-border)] text-[var(--text-primary)]"
                data-testid="new-password-input"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-[var(--text-primary)]">Confirm Password</Label>
              <Input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter password"
                className="bg-[var(--input-bg)] border-[var(--input-border)] text-[var(--text-primary)]"
                data-testid="confirm-password-input"
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setResetDialog(false);
                setNewPassword('');
                setConfirmPassword('');
              }}
              className="border-[var(--card-border)] text-[var(--text-primary)]"
            >
              Cancel
            </Button>
            <Button
              onClick={handleResetPassword}
              disabled={resetting || !newPassword || !confirmPassword}
              className="bg-teal-500 hover:bg-teal-600 text-white"
              data-testid="confirm-reset-btn"
            >
              {resetting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Reset Password
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
