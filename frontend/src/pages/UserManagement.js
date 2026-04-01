import { useState, useEffect, useCallback } from 'react';
import { useAuth, UserRole, Permission } from '../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { 
  Dialog, DialogContent, DialogHeader, DialogTitle, 
  DialogDescription, DialogFooter 
} from '../components/ui/dialog';
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from '../components/ui/select';
import { toast } from 'sonner';
import { 
  Users, Key, UserCheck, UserX, Search, Shield, Loader2, 
  Crown, UserCog, User as UserIcon, Plus, AlertTriangle, Eye, Edit3, Trash2, MoreHorizontal
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '../components/ui/dropdown-menu';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Role badge component
const RoleBadge = ({ role }) => {
  const roleConfig = {
    owner: { 
      label: 'Owner', 
      icon: Crown, 
      className: 'bg-amber-500/15 text-amber-600 border-amber-500/30' 
    },
    admin: { 
      label: 'Admin', 
      icon: UserCog, 
      className: 'bg-blue-500/15 text-blue-600 border-blue-500/30' 
    },
    staff: { 
      label: 'Staff', 
      icon: UserIcon, 
      className: 'bg-gray-500/15 text-gray-600 border-gray-500/30' 
    },
  };

  const config = roleConfig[role] || roleConfig.staff;
  const Icon = config.icon;

  return (
    <Badge variant="outline" className={`${config.className} gap-1`}>
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  );
};

export default function UserManagement() {
  const { token, user: currentUser, hasPermission, isOwner } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Reset password dialog
  const [resetDialog, setResetDialog] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [resetting, setResetting] = useState(false);
  
  // Role change dialog
  const [roleDialog, setRoleDialog] = useState(false);
  const [selectedRole, setSelectedRole] = useState('');
  const [changingRole, setChangingRole] = useState(false);
  
  // Create user dialog
  const [createDialog, setCreateDialog] = useState(false);
  const [newUserData, setNewUserData] = useState({
    email: '',
    password: '',
    full_name: '',
    company_name: '',
    role: 'staff'
  });
  const [creating, setCreating] = useState(false);

  // Check permissions
  const canViewUsers = hasPermission(Permission.USERS_VIEW);
  const canEditUsers = hasPermission(Permission.USERS_EDIT);
  const canCreateUsers = hasPermission(Permission.USERS_CREATE);
  const canManageRoles = hasPermission(Permission.USERS_MANAGE_ROLES);

  const fetchUsers = useCallback(async () => {
    if (!canViewUsers) {
      setLoading(false);
      return;
    }
    
    try {
      const response = await fetch(`${API_URL}/api/admin/users`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      } else if (response.status === 403) {
        toast.error('Permission denied');
      }
    } catch (err) {
      console.error('Failed to fetch users:', err);
    } finally {
      setLoading(false);
    }
  }, [token, canViewUsers]);

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

  const handleChangeRole = async () => {
    if (!selectedRole) return;
    
    setChangingRole(true);
    try {
      const response = await fetch(`${API_URL}/api/admin/users/${selectedUser.id}/role`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ role: selectedRole })
      });

      if (response.ok) {
        toast.success(`Role updated to ${selectedRole}`);
        setRoleDialog(false);
        setSelectedUser(null);
        setSelectedRole('');
        fetchUsers();
      } else {
        const data = await response.json();
        toast.error(data.detail || 'Failed to change role');
      }
    } catch (err) {
      toast.error('Network error. Please try again.');
    } finally {
      setChangingRole(false);
    }
  };

  const handleCreateUser = async () => {
    if (!newUserData.email || !newUserData.password || !newUserData.full_name) {
      toast.error('Please fill in all required fields');
      return;
    }
    if (newUserData.password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    setCreating(true);
    try {
      const response = await fetch(`${API_URL}/api/admin/users/create`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: newUserData.email,
          password: newUserData.password,
          full_name: newUserData.full_name,
          company_name: newUserData.company_name || null,
          role: newUserData.role
        })
      });

      if (response.ok) {
        toast.success('User created successfully');
        setCreateDialog(false);
        setNewUserData({ email: '', password: '', full_name: '', company_name: '', role: 'staff' });
        fetchUsers();
      } else {
        const data = await response.json();
        toast.error(data.detail || 'Failed to create user');
      }
    } catch (err) {
      toast.error('Network error. Please try again.');
    } finally {
      setCreating(false);
    }
  };

  const filteredUsers = users.filter(u => 
    u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
    u.full_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (u.company_name && u.company_name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  // Permission denied view
  if (!canViewUsers) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <AlertTriangle className="h-12 w-12 mb-4" className="text-amber-600" />
        <h2 className="text-xl font-semibold mb-2" className="text-gray-900">Access Denied</h2>
        <p className="text-gray-500">You don't have permission to view user management.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-heading uppercase tracking-tight text-white">
            User Management
          </h1>
          <p className="text-slate-300 mt-1">
            Manage user accounts, roles, and permissions for this tenant only
          </p>
        </div>
        {canCreateUsers && (
          <Button
            onClick={() => setCreateDialog(true)}
            className="text-white"
            className="bg-violet-600 hover:bg-violet-700"
            data-testid="create-user-btn"
          >
            <Plus className="h-4 w-4 mr-2" /> Add User
          </Button>
        )}
      </div>

      {/* Search */}
      <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4" className="text-gray-500" />
            <Input
              placeholder="Search users by name, email, or company..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
              style={{ backgroundColor: '#FFFFFF', borderColor: '#D7DCE2', color: '#1A1A1A' }}
              data-testid="user-search-input"
            />
          </div>
        </CardContent>
      </Card>

      {/* Users List */}
      <Card className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2" className="text-gray-900">
            <Users className="h-5 w-5" className="text-violet-600" />
            Users ({filteredUsers.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" className="text-violet-600" />
            </div>
          ) : filteredUsers.length === 0 ? (
            <p className="text-center py-8" className="text-gray-500">No users found</p>
          ) : (
            <div className="space-y-3">
              {filteredUsers.map((user) => (
                <div
                  key={user.id}
                  className="flex items-center justify-between p-4 rounded-lg"
                  style={{ backgroundColor: '#F5F7FA', border: '1px solid #D7DCE2' }}
                  data-testid={`user-row-${user.id}`}
                >
                  <div className="flex items-center gap-4">
                    <div 
                      className="w-10 h-10 rounded-full flex items-center justify-center"
                      style={{ backgroundColor: 'rgba(47, 139, 251, 0.1)', border: '1px solid rgba(47, 139, 251, 0.3)' }}
                    >
                      <span className="text-violet-600" className="font-medium">
                        {user.full_name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium" className="text-gray-900">{user.full_name}</span>
                        <RoleBadge role={user.role} />
                        {user.id === currentUser?.id && (
                          <Badge style={{ backgroundColor: 'rgba(47, 139, 251, 0.15)', color: '#2F8BFB' }}>You</Badge>
                        )}
                        {!user.is_active && (
                          <Badge style={{ backgroundColor: 'rgba(239, 68, 68, 0.15)', color: '#dc2626' }}>Disabled</Badge>
                        )}
                      </div>
                      <p className="text-sm" className="text-gray-500">{user.email}</p>
                      {user.company_name && (
                        <p className="text-xs" className="text-gray-500">{user.company_name}</p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 flex-wrap">
                    {/* View Icon - Always visible */}
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 text-blue-500 hover:text-blue-600 hover:bg-blue-50"
                      onClick={() => {
                        setSelectedUser(user);
                        // Show user details - could open a view dialog
                        toast.info(`${user.full_name} - ${user.email} - Role: ${user.role}`);
                      }}
                      title="View User"
                      data-testid={`view-user-btn-${user.id}`}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                    
                    {user.id !== currentUser?.id && (
                      <>
                        {/* Actions Dropdown */}
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm" className="h-8 w-8 p-0 text-gray-500 hover:text-gray-700">
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            {/* Role Change - Owner only */}
                            {canManageRoles && (
                              <DropdownMenuItem
                                onClick={() => {
                                  setSelectedUser(user);
                                  setSelectedRole(user.role);
                                  setRoleDialog(true);
                                }}
                              >
                                <Shield className="h-4 w-4 mr-2" />
                                Change Role
                              </DropdownMenuItem>
                            )}
                            
                            {/* Password Reset */}
                            {canEditUsers && (
                              <DropdownMenuItem
                                onClick={() => {
                                  setSelectedUser(user);
                                  setResetDialog(true);
                                }}
                              >
                                <Key className="h-4 w-4 mr-2" />
                                Reset Password
                              </DropdownMenuItem>
                            )}
                            
                            <DropdownMenuSeparator />
                            
                            {/* Enable/Disable */}
                            {canEditUsers && (
                              <DropdownMenuItem
                                onClick={() => handleToggleStatus(user, !user.is_active)}
                                className={user.is_active ? 'text-red-600' : 'text-green-600'}
                              >
                                {user.is_active ? (
                                  <>
                                    <UserX className="h-4 w-4 mr-2" />
                                    Disable User
                                  </>
                                ) : (
                                  <>
                                    <UserCheck className="h-4 w-4 mr-2" />
                                    Enable User
                                  </>
                                )}
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
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
        <DialogContent className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" className="text-gray-900">
              <Key className="h-5 w-5" className="text-violet-600" />
              Reset Password
            </DialogTitle>
            <DialogDescription className="text-gray-500">
              Set a new password for {selectedUser?.full_name} ({selectedUser?.email})
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-gray-900">New Password</Label>
              <Input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Minimum 6 characters"
                style={{ backgroundColor: '#FFFFFF', borderColor: '#D7DCE2', color: '#1A1A1A' }}
                data-testid="new-password-input"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-gray-900">Confirm Password</Label>
              <Input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter password"
                style={{ backgroundColor: '#FFFFFF', borderColor: '#D7DCE2', color: '#1A1A1A' }}
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
              style={{ borderColor: '#D7DCE2', color: '#1A1A1A' }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleResetPassword}
              disabled={resetting || !newPassword || !confirmPassword}
              className="text-white"
              className="bg-violet-600 hover:bg-violet-700"
              data-testid="confirm-reset-btn"
            >
              {resetting ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Reset Password
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Change Role Dialog */}
      <Dialog open={roleDialog} onOpenChange={setRoleDialog}>
        <DialogContent className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" className="text-gray-900">
              <Shield className="h-5 w-5" className="text-violet-600" />
              Change User Role
            </DialogTitle>
            <DialogDescription className="text-gray-500">
              Update the role for {selectedUser?.full_name}
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            <Label className="text-gray-900" className="mb-2 block">Select Role</Label>
            <Select value={selectedRole} onValueChange={setSelectedRole}>
              <SelectTrigger 
                style={{ backgroundColor: '#FFFFFF', borderColor: '#D7DCE2', color: '#1A1A1A' }}
                data-testid="role-select"
              >
                <SelectValue placeholder="Select a role" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="owner">
                  <div className="flex items-center gap-2">
                    <Crown className="h-4 w-4 text-amber-500" />
                    Owner - Full access to everything
                  </div>
                </SelectItem>
                <SelectItem value="admin">
                  <div className="flex items-center gap-2">
                    <UserCog className="h-4 w-4 text-blue-500" />
                    Admin - Manage operations, view-only financials
                  </div>
                </SelectItem>
                <SelectItem value="staff">
                  <div className="flex items-center gap-2">
                    <UserIcon className="h-4 w-4 text-gray-500" />
                    Staff - Limited access, own time clock only
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
            
            <div className="mt-4 p-3 rounded-lg" style={{ backgroundColor: '#F5F7FA', border: '1px solid #D7DCE2' }}>
              <p className="text-sm font-medium mb-2" className="text-gray-900">Role Permissions:</p>
              {selectedRole === 'owner' && (
                <ul className="text-xs space-y-1" className="text-gray-500">
                  <li>• Full access to all modules</li>
                  <li>• Manage users and roles</li>
                  <li>• View and edit all financial data</li>
                  <li>• Configure system settings</li>
                </ul>
              )}
              {selectedRole === 'admin' && (
                <ul className="text-xs space-y-1" className="text-gray-500">
                  <li>• Full access to customers, quotes, jobs, invoices</li>
                  <li>• Manage all time clock entries</li>
                  <li>• Edit payroll hours, time entries, and transactions</li>
                  <li>• View users (no role management)</li>
                </ul>
              )}
              {selectedRole === 'staff' && (
                <ul className="text-xs space-y-1" className="text-gray-500">
                  <li>• View customers, quotes, jobs</li>
                  <li>• Clock in/out (own entries only)</li>
                  <li>• Use AI tools</li>
                  <li>• No access to invoices, payroll, financials</li>
                </ul>
              )}
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setRoleDialog(false);
                setSelectedRole('');
              }}
              style={{ borderColor: '#D7DCE2', color: '#1A1A1A' }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleChangeRole}
              disabled={changingRole || !selectedRole}
              className="text-white"
              className="bg-violet-600 hover:bg-violet-700"
              data-testid="confirm-role-btn"
            >
              {changingRole ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Update Role
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create User Dialog */}
      <Dialog open={createDialog} onOpenChange={setCreateDialog}>
        <DialogContent className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2" className="text-gray-900">
              <Plus className="h-5 w-5" className="text-violet-600" />
              Create New User
            </DialogTitle>
            <DialogDescription className="text-gray-500">
              Add a new user to the system
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-gray-900">Full Name *</Label>
              <Input
                value={newUserData.full_name}
                onChange={(e) => setNewUserData({...newUserData, full_name: e.target.value})}
                placeholder="John Smith"
                style={{ backgroundColor: '#FFFFFF', borderColor: '#D7DCE2', color: '#1A1A1A' }}
                data-testid="create-fullname-input"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-gray-900">Email *</Label>
              <Input
                type="email"
                value={newUserData.email}
                onChange={(e) => setNewUserData({...newUserData, email: e.target.value})}
                placeholder="john@example.com"
                style={{ backgroundColor: '#FFFFFF', borderColor: '#D7DCE2', color: '#1A1A1A' }}
                data-testid="create-email-input"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-gray-900">Password *</Label>
              <Input
                type="password"
                value={newUserData.password}
                onChange={(e) => setNewUserData({...newUserData, password: e.target.value})}
                placeholder="Minimum 6 characters"
                style={{ backgroundColor: '#FFFFFF', borderColor: '#D7DCE2', color: '#1A1A1A' }}
                data-testid="create-password-input"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-gray-900">Company Name</Label>
              <Input
                value={newUserData.company_name}
                onChange={(e) => setNewUserData({...newUserData, company_name: e.target.value})}
                placeholder="Optional"
                style={{ backgroundColor: '#FFFFFF', borderColor: '#D7DCE2', color: '#1A1A1A' }}
                data-testid="create-company-input"
              />
            </div>
            <div className="space-y-2">
              <Label className="text-gray-900">Role</Label>
              <Select 
                value={newUserData.role} 
                onValueChange={(value) => setNewUserData({...newUserData, role: value})}
              >
                <SelectTrigger style={{ backgroundColor: '#FFFFFF', borderColor: '#D7DCE2', color: '#1A1A1A' }}>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {isOwner() && <SelectItem value="owner">Owner</SelectItem>}
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="staff">Staff</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setCreateDialog(false);
                setNewUserData({ email: '', password: '', full_name: '', company_name: '', role: 'staff' });
              }}
              style={{ borderColor: '#D7DCE2', color: '#1A1A1A' }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateUser}
              disabled={creating}
              className="text-white"
              className="bg-violet-600 hover:bg-violet-700"
              data-testid="confirm-create-btn"
            >
              {creating ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Create User
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
