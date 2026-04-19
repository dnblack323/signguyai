import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ArrowLeft, CheckCircle2, FileUp, Loader2, Settings2, Sparkles, UploadCloud } from 'lucide-react';
import { toast } from 'sonner';
import { useAuth, Permission } from '../context/AuthContext';
import { useAICreditGuard } from '../components/credits/AICreditConfirmationDialog';
import { getAuthToken } from '../lib/authStorage';

const API_URL = process.env.REACT_APP_BACKEND_URL;
const CATEGORY_OPTIONS = [
  { value: 'vehicle_wraps', label: 'Vehicle Wraps' },
  { value: 'banners', label: 'Banners' },
  { value: 'rigid_signs', label: 'Rigid Signs' },
  { value: 'cut_vinyl', label: 'Cut Vinyl' },
  { value: 'apparel', label: 'Apparel' },
  { value: 'services', label: 'Services' },
  { value: 'custom', label: 'Custom / Miscellaneous' },
];

const formatNumber = (value) => Number(value || 0).toFixed(2);

export default function PricingSetup() {
  const { hasPermission, isOwner, isAdminOrOwner } = useAuth();
  const { runGuardedAction, dialog: creditDialog } = useAICreditGuard();
  const canView = hasPermission(Permission.SETTINGS_VIEW) || isAdminOrOwner();
  const canEdit = hasPermission(Permission.SETTINGS_EDIT) || isOwner();

  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [savingMapping, setSavingMapping] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [savingReview, setSavingReview] = useState(false);
  const [imports, setImports] = useState([]);
  const [selectedImportId, setSelectedImportId] = useState(null);
  const [selectedImport, setSelectedImport] = useState(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [mapping, setMapping] = useState({
    description_field: '',
    quantity_field: '',
    total_field: '',
    dimension_field: '',
    category_field: '',
    category_overrides: {},
  });
  const [excludedRowIds, setExcludedRowIds] = useState([]);
  const [reviewDecisions, setReviewDecisions] = useState({});

  const getToken = () => getAuthToken();

  const loadImports = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/pricing-setup/imports`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to load imports');
      const data = await response.json();
      setImports(data);
      if (data.length > 0 && !selectedImportId) {
        setSelectedImportId(data[0].id);
      }
    } catch (error) {
      toast.error('Failed to load historical imports');
    } finally {
      setLoading(false);
    }
  }, [selectedImportId]);

  const loadImportDetail = useCallback(async (importId) => {
    const token = getToken();
    if (!token || !importId) return;
    try {
      const response = await fetch(`${API_URL}/api/pricing-setup/imports/${importId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to load import');
      const data = await response.json();
      setSelectedImport(data);
      setMapping({
        description_field: data.mapping?.description_field || '',
        quantity_field: data.mapping?.quantity_field || '',
        total_field: data.mapping?.total_field || '',
        dimension_field: data.mapping?.dimension_field || '',
        category_field: data.mapping?.category_field || '',
        category_overrides: data.mapping?.category_overrides || {},
      });
      setExcludedRowIds((data.analysis_summary?.outlier_rows || []).filter((row) => row.excluded).map((row) => row.row_id));

      const nextDecisions = {};
      (data.suggestions || []).forEach((suggestion) => {
        nextDecisions[suggestion.id] = {
          status: suggestion.status || 'pending',
          final_value: suggestion.final_value ?? suggestion.suggested_value,
        };
      });
      setReviewDecisions(nextDecisions);
    } catch (error) {
      toast.error('Failed to load import detail');
    }
  }, []);

  useEffect(() => {
    loadImports();
  }, [loadImports]);

  useEffect(() => {
    if (selectedImportId) {
      loadImportDetail(selectedImportId);
    }
  }, [selectedImportId, loadImportDetail]);

  const availableColumns = useMemo(() => {
    const columns = new Set();
    (selectedImport?.files || []).forEach((file) => {
      (file.preview?.columns || []).forEach((column) => columns.add(column));
    });
    return Array.from(columns);
  }, [selectedImport]);

  const uniqueDescriptions = useMemo(() => {
    const descriptionMap = new Map();
    (selectedImport?.normalized_rows || []).forEach((row) => {
      if (!descriptionMap.has(row.description)) {
        descriptionMap.set(row.description, row.category_final);
      }
    });
    return Array.from(descriptionMap.entries()).slice(0, 12);
  }, [selectedImport]);

  const handleUpload = async () => {
    if (!selectedFiles.length) {
      toast.error('Please choose at least one invoice file');
      return;
    }
    const token = getToken();
    if (!token) return;

    const formData = new FormData();
    selectedFiles.forEach((file) => formData.append('files', file));

    setUploading(true);
    try {
      const response = await fetch(`${API_URL}/api/pricing-setup/imports`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
      }

      const data = await response.json();
      toast.success('Historical invoice files uploaded');
      setSelectedFiles([]);
      setSelectedImportId(data.id);
      await loadImports();
    } catch (error) {
      toast.error(error.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleSaveMapping = async () => {
    if (!selectedImportId) return;
    const token = getToken();
    if (!token) return;

    setSavingMapping(true);
    try {
      const response = await fetch(`${API_URL}/api/pricing-setup/imports/${selectedImportId}/mapping`, {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(mapping),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save mapping');
      }

      toast.success('Mapping saved');
      await loadImportDetail(selectedImportId);
    } catch (error) {
      toast.error(error.message || 'Failed to save mapping');
    } finally {
      setSavingMapping(false);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedImportId) return;
    const token = getToken();
    if (!token) return;

    await runGuardedAction({
      actionType: 'historical_invoice_analysis',
      featureName: 'Historical Invoice AI Analysis',
      execute: async () => {
        setAnalyzing(true);
        try {
          const response = await fetch(`${API_URL}/api/pricing-setup/imports/${selectedImportId}/analyze`, {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ excluded_row_ids: excludedRowIds }),
          });
          if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Analysis failed');
          }

          toast.success('AI pricing analysis complete');
          await loadImportDetail(selectedImportId);
          return response.json;
        } catch (error) {
          toast.error(error.message || 'Analysis failed');
          throw error;
        } finally {
          setAnalyzing(false);
        }
      }
    });
  };

  const handleSaveReview = async () => {
    if (!selectedImportId) return;
    const token = getToken();
    if (!token) return;

    setSavingReview(true);
    try {
      const decisions = Object.entries(reviewDecisions).map(([suggestionId, value]) => ({
        suggestion_id: suggestionId,
        status: value.status === 'accepted' && Number(value.final_value) !== Number((selectedImport?.suggestions || []).find((item) => item.id === suggestionId)?.suggested_value)
          ? 'edited'
          : value.status,
        final_value: Number(value.final_value),
      }));

      const response = await fetch(`${API_URL}/api/pricing-setup/imports/${selectedImportId}/review`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ decisions }),
      });
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save review');
      }

      toast.success('Accepted benchmarks saved to benchmark settings only');
      await loadImportDetail(selectedImportId);
    } catch (error) {
      toast.error(error.message || 'Failed to save review');
    } finally {
      setSavingReview(false);
    }
  };

  if (!canView) {
    return (
      <div className="max-w-4xl mx-auto">
        <Card data-testid="pricing-setup-access-denied">
          <CardHeader>
            <CardTitle>Access denied</CardTitle>
            <CardDescription>You do not have permission to view Pricing Setup.</CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6" data-testid="pricing-setup-page">
      {creditDialog}
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <Link to="/settings">
            <Button variant="outline" data-testid="pricing-setup-back-button">
              <ArrowLeft className="h-4 w-4 mr-2" /> Back to company settings
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold text-white">Historical Pricing Setup</h1>
            <p className="text-slate-300 mt-1 max-w-4xl">
              Use this page for historical invoice imports and benchmark analysis. All live pricing defaults now live in Pricing Foundation.
            </p>
          </div>
        </div>
        <Badge className="bg-emerald-100 text-emerald-800 self-start" data-testid="pricing-setup-tenant-isolation-badge">
          Tenant-isolated files, extracted rows, and AI suggestions
        </Badge>
      </div>

      <Tabs defaultValue="historical-import" className="space-y-6">
        <TabsList className="grid w-full grid-cols-2" data-testid="pricing-setup-tabs">
          <TabsTrigger value="cost-settings" data-testid="pricing-setup-tab-cost-settings">Pricing Foundation (Primary)</TabsTrigger>
          <TabsTrigger value="historical-import" data-testid="pricing-setup-tab-historical-import">Historical Invoice Import</TabsTrigger>
        </TabsList>

        <TabsContent value="cost-settings">
          <Card data-testid="pricing-setup-cost-settings-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings2 className="h-5 w-5 text-teal-400" /> Pricing Foundation
              </CardTitle>
              <CardDescription>
                Pricing Foundation is the single source of truth for defaults, materials, and pricing rules. This page is for historical imports only.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center gap-3">
              <Link to="/pricing-foundation">
                <Button data-testid="pricing-setup-open-cost-settings-button">Open Pricing Foundation</Button>
              </Link>
              <Badge variant="outline" data-testid="pricing-setup-benchmark-separation-badge">
                Historical imports only
              </Badge>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="historical-import" className="space-y-6">
          <Card data-testid="historical-import-upload-card">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UploadCloud className="h-5 w-5 text-teal-400" /> Upload historical invoices
              </CardTitle>
              <CardDescription>
                Upload PDF, CSV, or Excel invoice files. The workflow stays tenant-specific and requires review before any benchmark is saved.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Input
                type="file"
                multiple
                accept=".pdf,.csv,.xlsx,.xls"
                onChange={(event) => setSelectedFiles(Array.from(event.target.files || []))}
                disabled={!canEdit}
                data-testid="historical-import-file-input"
              />
              <div className="flex flex-wrap gap-2 text-sm text-gray-600">
                {selectedFiles.map((file) => (
                  <Badge key={`${file.name}-${file.size}`} variant="outline" data-testid="historical-import-selected-file-badge">
                    {file.name}
                  </Badge>
                ))}
              </div>
              <Button onClick={handleUpload} disabled={!canEdit || uploading || !selectedFiles.length} data-testid="historical-import-upload-button">
                {uploading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <FileUp className="h-4 w-4 mr-2" />}
                Upload files
              </Button>
            </CardContent>
          </Card>

          <div className="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
            <Card data-testid="historical-import-list-card">
              <CardHeader>
                <CardTitle>Import history</CardTitle>
                <CardDescription>Select an import session to continue review.</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="flex items-center justify-center py-10"><Loader2 className="h-5 w-5 animate-spin text-teal-500" /></div>
                ) : imports.length === 0 ? (
                  <p className="text-sm text-gray-500" data-testid="historical-import-empty-state">No imports yet.</p>
                ) : (
                  <div className="space-y-3">
                    {imports.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => setSelectedImportId(item.id)}
                        className={`w-full rounded-xl border p-3 text-left transition ${selectedImportId === item.id ? 'border-teal-400 bg-teal-500/10' : 'border-gray-200 bg-slate-900/40 hover:border-slate-500'}`}
                        data-testid={`historical-import-row-${item.id}`}
                      >
                        <div className="flex items-center justify-between gap-2">
                          <p className="font-medium text-white">{item.files?.length || 0} file(s)</p>
                          <Badge variant="outline">{item.status}</Badge>
                        </div>
                        <p className="text-xs text-slate-400 mt-2">{new Date(item.created_at).toLocaleString()}</p>
                      </button>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <div className="space-y-6">
              {selectedImport ? (
                <>
                  <Card data-testid="historical-import-detail-card">
                    <CardHeader>
                      <CardTitle>Current import session</CardTitle>
                      <CardDescription>
                        Review file structure, confirm mapping, run AI analysis, and accept or reject suggestions.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="grid gap-4 md:grid-cols-3">
                      <div className="rounded-xl border border-gray-200 bg-slate-900/40 p-4" data-testid="historical-import-files-count-card">
                        <p className="text-xs uppercase text-slate-400">Files</p>
                        <p className="text-2xl font-bold text-white mt-2">{selectedImport.files?.length || 0}</p>
                      </div>
                      <div className="rounded-xl border border-gray-200 bg-slate-900/40 p-4" data-testid="historical-import-lines-card">
                        <p className="text-xs uppercase text-slate-400">Normalized rows</p>
                        <p className="text-2xl font-bold text-white mt-2">{selectedImport.normalized_rows?.length || 0}</p>
                      </div>
                      <div className="rounded-xl border border-gray-200 bg-slate-900/40 p-4" data-testid="historical-import-suggestions-card">
                        <p className="text-xs uppercase text-slate-400">Suggestions</p>
                        <p className="text-2xl font-bold text-white mt-2">{selectedImport.suggestions?.length || 0}</p>
                      </div>
                    </CardContent>
                  </Card>

                  {availableColumns.length > 0 && (
                    <Card data-testid="historical-import-mapping-card">
                      <CardHeader>
                        <CardTitle>Field mapping review</CardTitle>
                        <CardDescription>
                          Confirm which columns represent descriptions, quantities, totals, dimensions, and optional category hints.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-5">
                        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
                          {[
                            ['description_field', 'Description field'],
                            ['quantity_field', 'Quantity field'],
                            ['total_field', 'Total field'],
                            ['dimension_field', 'Dimension/size field'],
                            ['category_field', 'Category field'],
                          ].map(([field, label]) => (
                            <div key={field} className="space-y-2">
                              <Label htmlFor={field}>{label}</Label>
                              <select
                                id={field}
                                value={mapping[field] || ''}
                                onChange={(event) => setMapping((current) => ({ ...current, [field]: event.target.value }))}
                                disabled={!canEdit}
                                className="w-full h-10 rounded-md border border-gray-200 bg-white px-3 text-sm text-gray-900"
                                data-testid={`historical-import-mapping-${field}`}
                              >
                                <option value="">Not mapped</option>
                                {availableColumns.map((column) => (
                                  <option key={column} value={column}>{column}</option>
                                ))}
                              </select>
                            </div>
                          ))}
                        </div>

                        {uniqueDescriptions.length > 0 && (
                          <div className="space-y-3">
                            <Label>Category mapping review</Label>
                            <div className="space-y-2">
                              {uniqueDescriptions.map(([description, defaultCategory]) => (
                                <div key={description} className="grid gap-3 rounded-lg border border-gray-200 p-3 md:grid-cols-[minmax(0,1fr)_220px]">
                                  <div>
                                    <p className="text-sm text-white">{description}</p>
                                    <p className="text-xs text-slate-400 mt-1">Current guess: {mapping.category_overrides?.[description] || defaultCategory}</p>
                                  </div>
                                  <select
                                    value={mapping.category_overrides?.[description] || defaultCategory}
                                    onChange={(event) => setMapping((current) => ({
                                      ...current,
                                      category_overrides: { ...current.category_overrides, [description]: event.target.value },
                                    }))}
                                    disabled={!canEdit}
                                    className="w-full h-10 rounded-md border border-gray-200 bg-white px-3 text-sm text-gray-900"
                                    data-testid={`historical-import-category-override-${description.slice(0, 20).replace(/\s+/g, '-')}`}
                                  >
                                    {CATEGORY_OPTIONS.map((option) => (
                                      <option key={option.value} value={option.value}>{option.label}</option>
                                    ))}
                                  </select>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        <Button onClick={handleSaveMapping} disabled={!canEdit || savingMapping} data-testid="historical-import-save-mapping-button">
                          {savingMapping ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <CheckCircle2 className="h-4 w-4 mr-2" />}
                          Save mapping
                        </Button>
                      </CardContent>
                    </Card>
                  )}

                  {/* Show analyze button when status is ready_for_analysis, even if rows are still being extracted */}
                  {selectedImport.status === 'ready_for_analysis' && !selectedImport.normalized_rows?.length && (
                    <Card data-testid="historical-import-ready-for-analysis-card">
                      <CardHeader>
                        <CardTitle>Ready for Analysis</CardTitle>
                        <CardDescription>
                          Your files have been uploaded. Click the button below to extract data and run AI pricing analysis.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="flex items-center gap-3 text-sm text-slate-300 p-4 rounded-lg border border-teal-500/30 bg-teal-500/10">
                          <FileUp className="h-5 w-5 text-teal-400 flex-shrink-0" />
                          <span>{selectedImport.files?.length || 0} file(s) uploaded and ready for processing</span>
                        </div>
                        <Button onClick={handleAnalyze} disabled={!canEdit || analyzing} className="bg-teal-600 hover:bg-teal-700" data-testid="historical-import-analyze-button">
                          {analyzing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Sparkles className="h-4 w-4 mr-2" />}
                          Extract & Analyze Invoices
                        </Button>
                      </CardContent>
                    </Card>
                  )}

                  {selectedImport.normalized_rows?.length > 0 && (
                    <Card data-testid="historical-import-preview-card">
                      <CardHeader>
                        <CardTitle>Extracted preview</CardTitle>
                        <CardDescription>Review normalized rows and optionally exclude flagged outliers before running AI analysis.</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {(selectedImport.analysis_summary?.outlier_rows || []).length > 0 && (
                          <div className="space-y-2" data-testid="historical-import-outliers-section">
                            <p className="text-sm text-amber-300 font-medium">Flagged outliers</p>
                            {(selectedImport.analysis_summary?.outlier_rows || []).slice(0, 8).map((row) => (
                              <label key={row.row_id} className="flex items-center justify-between gap-3 rounded-lg border border-amber-700/40 bg-amber-500/10 p-3 text-sm">
                                <span className="text-slate-200">{row.description} · ${formatNumber(row.total)}</span>
                                <input
                                  type="checkbox"
                                  checked={excludedRowIds.includes(row.row_id)}
                                  onChange={(event) => setExcludedRowIds((current) => event.target.checked ? [...current, row.row_id] : current.filter((id) => id !== row.row_id))}
                                  data-testid={`historical-import-exclude-row-${row.row_id}`}
                                />
                              </label>
                            ))}
                          </div>
                        )}

                        <div className="overflow-x-auto rounded-lg border border-gray-200">
                          <table className="w-full text-sm bg-white" data-testid="historical-import-preview-table">
                            <thead>
                              <tr className="text-left bg-gray-100 border-b border-gray-200">
                                <th className="py-2.5 px-3 font-medium text-gray-700">Description</th>
                                <th className="py-2.5 px-3 font-medium text-gray-700">Qty</th>
                                <th className="py-2.5 px-3 font-medium text-gray-700">Total</th>
                                <th className="py-2.5 px-3 font-medium text-gray-700">Sq Ft</th>
                                <th className="py-2.5 px-3 font-medium text-gray-700">Category</th>
                              </tr>
                            </thead>
                            <tbody>
                              {selectedImport.normalized_rows.slice(0, 12).map((row, idx) => (
                                <tr key={row.row_id} className={`border-b border-gray-100 ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                                  <td className="py-2 px-3 text-gray-900 font-medium">{row.description}</td>
                                  <td className="py-2 px-3 text-gray-800">{row.quantity}</td>
                                  <td className="py-2 px-3 text-gray-800 font-medium">${formatNumber(row.total)}</td>
                                  <td className="py-2 px-3 text-gray-800">{row.square_feet || '-'}</td>
                                  <td className="py-2 px-3"><span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-xs font-medium">{row.category_final}</span></td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>

                        <Button onClick={handleAnalyze} disabled={!canEdit || analyzing} data-testid="historical-import-analyze-button">
                          {analyzing ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Sparkles className="h-4 w-4 mr-2" />}
                          {selectedImport.analysis_summary ? 'Re-run AI analysis' : 'Run AI pricing analysis'}
                        </Button>
                      </CardContent>
                    </Card>
                  )}

                  {selectedImport.analysis_summary && (
                    <Card data-testid="historical-import-analysis-summary-card">
                      <CardHeader>
                        <CardTitle>Analysis dashboard</CardTitle>
                        <CardDescription>AI-assisted benchmark summary before any value is applied.</CardDescription>
                      </CardHeader>
                      <CardContent className="grid gap-4 md:grid-cols-4">
                        <div className="rounded-xl border border-gray-200 bg-white p-4">
                          <p className="text-xs uppercase text-gray-500 font-medium">Invoices analyzed</p>
                          <p className="text-2xl font-bold text-gray-900 mt-2">{selectedImport.analysis_summary.invoice_count}</p>
                        </div>
                        <div className="rounded-xl border border-gray-200 bg-white p-4">
                          <p className="text-xs uppercase text-gray-500 font-medium">Line items</p>
                          <p className="text-2xl font-bold text-gray-900 mt-2">{selectedImport.analysis_summary.line_item_count}</p>
                        </div>
                        <div className="rounded-xl border border-gray-200 bg-white p-4">
                          <p className="text-xs uppercase text-gray-500 font-medium">Categories detected</p>
                          <p className="text-2xl font-bold text-gray-900 mt-2">{selectedImport.analysis_summary.categories_detected?.length || 0}</p>
                        </div>
                        <div className="rounded-xl border border-gray-200 bg-white p-4">
                          <p className="text-xs uppercase text-gray-500 font-medium">Outliers flagged</p>
                          <p className="text-2xl font-bold text-gray-900 mt-2">{selectedImport.analysis_summary.outlier_rows?.length || 0}</p>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {selectedImport.suggestions?.length > 0 && (
                    <Card data-testid="historical-import-suggestions-review-card">
                      <CardHeader>
                        <CardTitle>Review benchmark suggestions</CardTitle>
                        <CardDescription>
                          Accept, edit, or ignore each suggestion. Accepted values save to benchmark settings only.
                        </CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        {selectedImport.suggestions.map((suggestion) => {
                          const reviewState = reviewDecisions[suggestion.id] || { status: 'pending', final_value: suggestion.final_value ?? suggestion.suggested_value };
                          return (
                            <div key={suggestion.id} className="rounded-xl border border-gray-200 bg-white p-4" data-testid={`historical-import-suggestion-${suggestion.id}`}>
                              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                                <div className="space-y-2">
                                  <div className="flex flex-wrap items-center gap-2">
                                    <p className="font-medium text-gray-900">{suggestion.category_label} · {suggestion.benchmark_label}</p>
                                    <Badge variant="outline">{suggestion.confidence}</Badge>
                                  </div>
                                  <p className="text-sm text-gray-600">Suggested: ${formatNumber(suggestion.suggested_value)}</p>
                                  {suggestion.summary && <p className="text-sm text-gray-500">{suggestion.summary}</p>}
                                  {!!suggestion.pattern_notes?.length && (
                                    <ul className="list-disc list-inside text-xs text-gray-500 space-y-1">
                                      {suggestion.pattern_notes.map((note, index) => <li key={`${suggestion.id}-${index}`}>{note}</li>)}
                                    </ul>
                                  )}
                                </div>

                                <div className="space-y-3 min-w-[260px]">
                                  <div className="space-y-2">
                                    <Label htmlFor={`suggestion-${suggestion.id}`}>Reviewed value</Label>
                                    <Input
                                      id={`suggestion-${suggestion.id}`}
                                      type="number"
                                      step="0.01"
                                      value={reviewState.final_value}
                                      onChange={(event) => setReviewDecisions((current) => ({
                                        ...current,
                                        [suggestion.id]: { ...reviewState, final_value: event.target.value },
                                      }))}
                                      data-testid={`historical-import-suggestion-value-${suggestion.id}`}
                                    />
                                  </div>
                                  <div className="flex flex-wrap gap-2">
                                    {['accepted', 'ignored'].map((status) => (
                                      <Button
                                        key={status}
                                        type="button"
                                        variant={reviewState.status === status ? 'default' : 'outline'}
                                        onClick={() => setReviewDecisions((current) => ({
                                          ...current,
                                          [suggestion.id]: { ...reviewState, status },
                                        }))}
                                        data-testid={`historical-import-suggestion-${status}-${suggestion.id}`}
                                      >
                                        {status === 'accepted' ? 'Accept' : 'Ignore'}
                                      </Button>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            </div>
                          );
                        })}

                        <Button onClick={handleSaveReview} disabled={!canEdit || savingReview} data-testid="historical-import-save-review-button">
                          {savingReview ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <CheckCircle2 className="h-4 w-4 mr-2" />}
                          Save accepted benchmarks
                        </Button>
                      </CardContent>
                    </Card>
                  )}
                </>
              ) : (
                <Card data-testid="historical-import-empty-detail-card">
                  <CardHeader>
                    <CardTitle>No import selected</CardTitle>
                    <CardDescription>Upload invoice files to begin the review workflow.</CardDescription>
                  </CardHeader>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}