import { useState, useEffect } from 'react';
import { Settings, Plus, Trash2, GripVertical, Save, RotateCcw, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Switch } from '../components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${localStorage.getItem('auth_token')}`, 'Content-Type': 'application/json' });

const DEPARTMENTS = [
  { value: 'design', label: 'Design' }, { value: 'print', label: 'Print' }, { value: 'cut_trim', label: 'Cut / Trim' },
  { value: 'lamination', label: 'Lamination' }, { value: 'weed_mask', label: 'Weed / Mask' }, { value: 'sewing_finishing', label: 'Sewing / Finishing' },
  { value: 'assembly', label: 'Assembly' }, { value: 'apparel', label: 'Apparel' }, { value: 'wrap_prep', label: 'Wrap Prep' },
  { value: 'install', label: 'Install' }, { value: 'qc_review', label: 'QC / Review' }, { value: 'packaging', label: 'Packaging' }, { value: 'delivery', label: 'Delivery' },
];

const CATEGORY_LABELS = {
  rigid_signs: 'Rigid Signs', banners: 'Banners', cut_vinyl: 'Cut Vinyl / Lettering',
  vehicle_wrap: 'Vehicle Wrap / Lettering', apparel: 'Apparel', promo_misc: 'Promotional / Misc',
};

export default function WorkflowTemplateManager() {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState('');
  const [expanded, setExpanded] = useState(null);
  const [editingStages, setEditingStages] = useState({});

  const load = async () => {
    try {
      const res = await axios.get(`${API}/workflow-templates`, { headers: hdr() });
      setTemplates(res.data);
      const stagesMap = {};
      res.data.forEach(t => { stagesMap[t.id] = [...t.stages]; });
      setEditingStages(stagesMap);
    } catch { toast.error('Failed to load templates'); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const toggleExpand = (id) => setExpanded(expanded === id ? null : id);

  const updateStage = (templateId, stageIdx, field, value) => {
    setEditingStages(prev => {
      const stages = [...(prev[templateId] || [])];
      stages[stageIdx] = { ...stages[stageIdx], [field]: value };
      return { ...prev, [templateId]: stages };
    });
  };

  const addStage = (templateId) => {
    setEditingStages(prev => {
      const stages = [...(prev[templateId] || [])];
      const seq = stages.length > 0 ? Math.max(...stages.map(s => s.sequence || 0)) + 1 : 1;
      stages.push({ name: 'New Stage', department: 'assembly', sequence: seq, required: true, qc_required: false, depends_on_proof: false });
      return { ...prev, [templateId]: stages };
    });
  };

  const removeStage = (templateId, stageIdx) => {
    setEditingStages(prev => {
      const stages = [...(prev[templateId] || [])].filter((_, i) => i !== stageIdx);
      return { ...prev, [templateId]: stages };
    });
  };

  const moveStage = (templateId, stageIdx, direction) => {
    setEditingStages(prev => {
      const stages = [...(prev[templateId] || [])];
      const targetIdx = stageIdx + direction;
      if (targetIdx < 0 || targetIdx >= stages.length) return prev;
      [stages[stageIdx], stages[targetIdx]] = [stages[targetIdx], stages[stageIdx]];
      stages.forEach((s, i) => { s.sequence = i + 1; });
      return { ...prev, [templateId]: stages };
    });
  };

  const saveTemplate = async (templateId) => {
    setSaving(templateId);
    try {
      const stages = (editingStages[templateId] || []).map((s, i) => ({ ...s, sequence: i + 1 }));
      await axios.put(`${API}/workflow-templates/${templateId}`, { stages }, { headers: hdr() });
      toast.success('Template saved');
      load();
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed to save'); }
    finally { setSaving(''); }
  };

  const reseedDefaults = async () => {
    if (!window.confirm('Reset all templates to defaults? Custom changes will be lost.')) return;
    setSaving('reseed');
    try {
      await axios.post(`${API}/workflow-templates/seed-defaults`, {}, { headers: hdr() });
      toast.success('Templates reset to defaults');
      load();
    } catch { toast.error('Failed to reset'); }
    finally { setSaving(''); }
  };

  if (loading) return <div className="flex items-center justify-center py-20"><Loader2 className="w-8 h-8 animate-spin text-violet-500" /></div>;

  return (
    <div className="space-y-5" data-testid="workflow-template-manager">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white font-heading flex items-center gap-3"><Settings className="w-8 h-8 text-violet-400" /> Workflow Templates</h1>
          <p className="text-slate-400 text-sm mt-1">Configure production stages for each item category</p>
        </div>
        <Button variant="outline" onClick={reseedDefaults} disabled={saving === 'reseed'} className="gap-2 text-gray-700">
          {saving === 'reseed' ? <Loader2 className="w-4 h-4 animate-spin" /> : <RotateCcw className="w-4 h-4" />} Reset to Defaults
        </Button>
      </div>

      <div className="space-y-3">
        {templates.map(template => {
          const stages = editingStages[template.id] || template.stages || [];
          const isExpanded = expanded === template.id;

          return (
            <Card key={template.id} className="bg-white border-gray-200" data-testid={`template-${template.category}`}>
              <CardContent className="p-0">
                <button onClick={() => toggleExpand(template.id)} className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-violet-500/10 flex items-center justify-center">
                      <Settings className="w-5 h-5 text-violet-400" />
                    </div>
                    <div>
                      <p className="text-gray-900 font-medium">{CATEGORY_LABELS[template.category] || template.template_name}</p>
                      <p className="text-xs text-gray-500">{stages.length} stages | {stages.filter(s => s.required).length} required</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {template.is_default && <Badge variant="outline" className="text-xs text-gray-500">Default</Badge>}
                    {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-500" /> : <ChevronDown className="w-5 h-5 text-gray-500" />}
                  </div>
                </button>

                {isExpanded && (
                  <div className="border-t border-gray-200 p-4 space-y-3">
                    {stages.map((stage, idx) => (
                      <div key={idx} className="flex items-center gap-2 bg-gray-50 rounded-lg p-3" data-testid={`stage-${idx}`}>
                        <div className="flex flex-col gap-0.5">
                          <button onClick={() => moveStage(template.id, idx, -1)} disabled={idx === 0} className="text-gray-500 hover:text-gray-900 disabled:opacity-20"><ChevronUp className="w-3 h-3" /></button>
                          <button onClick={() => moveStage(template.id, idx, 1)} disabled={idx === stages.length - 1} className="text-gray-500 hover:text-gray-900 disabled:opacity-20"><ChevronDown className="w-3 h-3" /></button>
                        </div>
                        <span className="text-xs font-mono text-gray-500 w-6">{idx + 1}</span>
                        <Input value={stage.name} onChange={e => updateStage(template.id, idx, 'name', e.target.value)} className="bg-gray-50 border-gray-300 text-gray-900 h-8 text-sm flex-1" />
                        <Select value={stage.department} onValueChange={v => updateStage(template.id, idx, 'department', v)}>
                          <SelectTrigger className="bg-gray-50 border-gray-300 text-gray-900 h-8 text-xs w-32"><SelectValue /></SelectTrigger>
                          <SelectContent>{DEPARTMENTS.map(d => <SelectItem key={d.value} value={d.value}>{d.label}</SelectItem>)}</SelectContent>
                        </Select>
                        <div className="flex items-center gap-1" title="Required"><Switch checked={stage.required} onCheckedChange={v => updateStage(template.id, idx, 'required', v)} /></div>
                        <div className="flex items-center gap-1" title="QC"><Switch checked={stage.qc_required} onCheckedChange={v => updateStage(template.id, idx, 'qc_required', v)} /></div>
                        <button onClick={() => removeStage(template.id, idx)} className="text-red-400 hover:text-red-300 p-1"><Trash2 className="w-4 h-4" /></button>
                      </div>
                    ))}

                    <div className="flex items-center gap-4 text-xs text-gray-500 px-3">
                      <span>Toggles: Required | QC</span>
                    </div>

                    <div className="flex gap-2 pt-2">
                      <Button variant="outline" size="sm" onClick={() => addStage(template.id)} className="gap-1 text-gray-700"><Plus className="w-3 h-3" /> Add Stage</Button>
                      <Button size="sm" className="bg-violet-600 hover:bg-violet-700 text-gray-900 gap-1" onClick={() => saveTemplate(template.id)} disabled={saving === template.id}>
                        {saving === template.id ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />} Save
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
