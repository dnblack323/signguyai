import { useState, useEffect, useCallback } from 'react';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { toast } from 'sonner';
import {
  Download, Upload, Shield, Clock, AlertTriangle,
  CheckCircle2, FileJson, Loader2, ArrowLeft
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function BackupRestore() {
  const { api } = useApp();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [backupStatus, setBackupStatus] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [restoreFile, setRestoreFile] = useState(null);
  const [restorePreview, setRestorePreview] = useState(null);
  const [previewing, setPreviewing] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [confirmRestore, setConfirmRestore] = useState(false);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await api.get('/backup/status');
      setBackupStatus(res.data);
    } catch (error) {
      console.error('Failed to fetch backup status:', error);
    }
  }, [api]);

  useEffect(() => { fetchStatus(); }, [fetchStatus]);

  const handleExport = async () => {
    setExporting(true);
    try {
      const res = await api.get('/backup/export');
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      const date = new Date().toISOString().split('T')[0];
      a.href = url;
      a.download = `signguy-backup-${date}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success(`Backup downloaded — ${res.data.summary?.total_records || 0} records`);
      fetchStatus();
    } catch (err) {
      toast.error('Failed to create backup');
    } finally {
      setExporting(false);
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.name.endsWith('.json')) {
      toast.error('Please select a .json backup file');
      return;
    }
    setRestoreFile(file);
    setRestorePreview(null);
    setConfirmRestore(false);
  };

  const handlePreview = async () => {
    if (!restoreFile) return;
    setPreviewing(true);
    try {
      const formData = new FormData();
      formData.append('file', restoreFile);
      const res = await api.post('/backup/preview-restore', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setRestorePreview(res.data);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Invalid backup file');
    } finally {
      setPreviewing(false);
    }
  };

  const handleRestore = async () => {
    if (!restoreFile) return;
    setRestoring(true);
    try {
      const formData = new FormData();
      formData.append('file', restoreFile);
      const res = await api.post('/backup/restore', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      toast.success(res.data.message);
      setRestoreFile(null);
      setRestorePreview(null);
      setConfirmRestore(false);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Restore failed');
    } finally {
      setRestoring(false);
    }
  };

  if (user?.role !== 'owner') {
    return (
      <div className="p-8 text-center text-gray-400">
        <Shield className="w-12 h-12 mx-auto mb-4 text-gray-600" />
        <p>Only the account owner can manage backups.</p>
      </div>
    );
  }

  const lastBackup = backupStatus?.last_backup_at
    ? new Date(backupStatus.last_backup_at).toLocaleDateString('en-US', {
        year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit'
      })
    : 'Never';

  const collectionLabels = {
    customers: 'Customers',
    jobs: 'Orders',
    job_items: 'Order Line Items',
    job_activities: 'Order Activities',
    job_notes: 'Order Notes',
    invoices: 'Invoices',
    quotes: 'Quotes',
    products: 'Products',
    webstores_v2: 'Webstores',
    webstore_products: 'Webstore Products',
    webstore_orders_v2: 'Webstore Orders',
    documents: 'Documents',
    tasks: 'Tasks',
    employees: 'Employees',
    promo_codes: 'Promo Codes',
    production_timelines: 'Production Timelines',
    conversations: 'Conversations',
    timelogs: 'Time Logs',
    payments: 'Payments',
    payment_transactions: 'Payment Transactions',
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" onClick={() => navigate('/settings')} data-testid="back-to-settings">
          <ArrowLeft className="h-5 w-5 text-white" />
        </Button>
        <div>
          <h1 className="text-2xl font-bold text-white">Data Backup & Restore</h1>
          <p className="text-gray-400 text-sm">Download your data or restore from a previous backup</p>
        </div>
      </div>

      {/* Backup Status */}
      <Card className="bg-[#111826] border-gray-700">
        <CardContent className="p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Clock className="w-5 h-5 text-gray-400" />
            <div>
              <p className="text-sm text-gray-300">Last backup: <span className="text-white font-medium">{lastBackup}</span></p>
              {backupStatus?.needs_reminder && (
                <p className="text-xs text-amber-400 flex items-center gap-1 mt-1">
                  <AlertTriangle className="w-3 h-3" />
                  It's been over a week since your last backup
                </p>
              )}
            </div>
          </div>
          <Badge className={backupStatus?.needs_reminder ? 'bg-amber-500/20 text-amber-400' : 'bg-green-500/20 text-green-400'}>
            {backupStatus?.needs_reminder ? 'Backup Recommended' : 'Up to Date'}
          </Badge>
        </CardContent>
      </Card>

      {/* Export Section */}
      <Card className="bg-[#111826] border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Download className="w-5 h-5 text-blue-400" />
            Download Backup
          </CardTitle>
          <CardDescription>
            Export all your data as a JSON file. Includes customers, jobs, invoices, quotes, products, webstores, and more. Does not include images or uploaded files.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            onClick={handleExport}
            disabled={exporting}
            className="bg-blue-600 hover:bg-blue-700"
            data-testid="download-backup-btn"
          >
            {exporting ? (
              <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Creating Backup...</>
            ) : (
              <><FileJson className="w-4 h-4 mr-2" /> Download Backup</>
            )}
          </Button>
          <p className="text-xs text-gray-500 mt-3">
            Store this file somewhere safe. You can use it to restore your data if anything goes wrong.
          </p>
        </CardContent>
      </Card>

      {/* Restore Section */}
      <Card className="bg-[#111826] border-gray-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Upload className="w-5 h-5 text-amber-400" />
            Restore from Backup
          </CardTitle>
          <CardDescription>
            Upload a previously downloaded backup file to restore your data. This will replace all current data with the backup.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* File Input */}
          <div>
            <label className="block">
              <input
                type="file"
                accept=".json"
                onChange={handleFileSelect}
                className="block w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-medium file:bg-gray-700 file:text-gray-200 hover:file:bg-gray-600 cursor-pointer"
                data-testid="restore-file-input"
              />
            </label>
          </div>

          {/* Preview Button */}
          {restoreFile && !restorePreview && (
            <Button
              onClick={handlePreview}
              disabled={previewing}
              variant="outline"
              data-testid="preview-restore-btn"
            >
              {previewing ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Analyzing...</>
              ) : (
                'Preview Restore'
              )}
            </Button>
          )}

          {/* Preview Results */}
          {restorePreview && (
            <div className="p-4 bg-[#0B0F17] rounded-lg border border-gray-600 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-white font-medium">Backup Summary</h4>
                <Badge className="bg-blue-500/20 text-blue-400">
                  {restorePreview.total_records} total records
                </Badge>
              </div>
              <p className="text-xs text-gray-500">
                Created: {restorePreview.created_at ? new Date(restorePreview.created_at).toLocaleString() : 'Unknown'}
              </p>

              <div className="grid grid-cols-2 gap-2 text-sm">
                {Object.entries(restorePreview.collections).map(([col, data]) => (
                  <div key={col} className="flex justify-between text-gray-400 p-2 bg-[#111826] rounded">
                    <span>{collectionLabels[col] || col}</span>
                    <span className="text-white font-medium">{data.backup_count}</span>
                  </div>
                ))}
              </div>

              {/* Warning */}
              <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
                <p className="text-sm text-red-400 flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                  This will <strong>replace all existing data</strong> with the backup. This cannot be undone. Make sure you have a current backup before restoring.
                </p>
              </div>

              {/* Confirm Checkbox */}
              <label className="flex items-center gap-2 cursor-pointer" data-testid="confirm-restore-check">
                <input
                  type="checkbox"
                  checked={confirmRestore}
                  onChange={(e) => setConfirmRestore(e.target.checked)}
                  className="rounded border-gray-600"
                />
                <span className="text-sm text-gray-300">I understand this will replace all my current data</span>
              </label>

              {/* Restore Button */}
              <Button
                onClick={handleRestore}
                disabled={!confirmRestore || restoring}
                className="bg-red-600 hover:bg-red-700 disabled:opacity-50"
                data-testid="restore-data-btn"
              >
                {restoring ? (
                  <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Restoring...</>
                ) : (
                  <><Upload className="w-4 h-4 mr-2" /> Restore Data</>
                )}
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info */}
      <Card className="bg-[#0B0F17] border-gray-700">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Shield className="w-5 h-5 text-gray-500 shrink-0 mt-0.5" />
            <div className="text-xs text-gray-500 space-y-1">
              <p>Backups include: Customers, Jobs, Invoices, Quotes, Products, Webstores, Orders, Documents, Tasks, Employees, Promo Codes, Timelines, Conversations, Time Logs, and Payments.</p>
              <p>Backups do <strong>not</strong> include: Uploaded images, logos, file attachments, or account passwords.</p>
              <p>We recommend downloading a backup at least once a week.</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
