import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Textarea } from '../components/ui/textarea';
import { CheckCircle2, Circle, Save, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import { getAuthToken } from '../lib/authStorage';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function OnboardingChecklist({ tenantId }) {
  const [items, setItems] = useState([]);
  const [progress, setProgress] = useState({ total: 0, completed: 0, percentage: 0 });
  const [loading, setLoading] = useState(true);
  const [savingItemId, setSavingItemId] = useState(null);
  const [editingNotes, setEditingNotes] = useState({});

  useEffect(() => {
    if (tenantId) {
      fetchChecklist();
      fetchProgress();
    }
  }, [tenantId]);

  const fetchChecklist = async () => {
    try {
      const token = getAuthToken();
      const response = await fetch(
        `${BACKEND_URL}/api/platform-admin/tenants/${tenantId}/checklist`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch checklist');
      }

      const data = await response.json();
      setItems(data);

      // Initialize notes from existing items
      const notes = {};
      data.forEach((item) => {
        notes[item.id] = item.note || '';
      });
      setEditingNotes(notes);
    } catch (error) {
      console.error('Error fetching checklist:', error);
      toast.error('Failed to load checklist');
    } finally {
      setLoading(false);
    }
  };

  const fetchProgress = async () => {
    try {
      const token = getAuthToken();
      const response = await fetch(
        `${BACKEND_URL}/api/platform-admin/tenants/${tenantId}/checklist/progress`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch progress');
      }

      const data = await response.json();
      setProgress(data);
    } catch (error) {
      console.error('Error fetching progress:', error);
    }
  };

  const handleToggleItem = async (item) => {
    setSavingItemId(item.id);
    try {
      const token = getAuthToken();
      const response = await fetch(
        `${BACKEND_URL}/api/platform-admin/tenants/${tenantId}/checklist/${item.id}`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            completed: !item.completed,
            note: editingNotes[item.id] || null,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to update item');
      }

      const updatedItem = await response.json();

      // Update local state
      setItems((prev) =>
        prev.map((i) => (i.id === item.id ? updatedItem : i))
      );

      // Refresh progress
      fetchProgress();

      toast.success(
        updatedItem.completed ? 'Item marked as complete' : 'Item marked as incomplete'
      );
    } catch (error) {
      console.error('Error updating item:', error);
      toast.error('Failed to update item');
    } finally {
      setSavingItemId(null);
    }
  };

  const handleSaveNote = async (item) => {
    setSavingItemId(item.id);
    try {
      const token = getAuthToken();
      const response = await fetch(
        `${BACKEND_URL}/api/platform-admin/tenants/${tenantId}/checklist/${item.id}`,
        {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            completed: item.completed,
            note: editingNotes[item.id] || null,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to save note');
      }

      const updatedItem = await response.json();

      // Update local state
      setItems((prev) =>
        prev.map((i) => (i.id === item.id ? updatedItem : i))
      );

      toast.success('Note saved');
    } catch (error) {
      console.error('Error saving note:', error);
      toast.error('Failed to save note');
    } finally {
      setSavingItemId(null);
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-blue-600" />
            <span className="ml-2 text-gray-600">Loading checklist...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Progress Card */}
      <Card>
        <CardHeader>
          <CardTitle>Onboarding Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold text-gray-900">
                  {progress.completed} / {progress.total}
                </p>
                <p className="text-sm text-gray-600">Items completed</p>
              </div>
              <div className="text-right">
                <p className="text-3xl font-bold text-blue-600">
                  {progress.percentage}%
                </p>
                <p className="text-sm text-gray-600">Complete</p>
              </div>
            </div>
            
            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${progress.percentage}%` }}
              ></div>
            </div>

            {progress.percentage === 100 && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                  <p className="text-green-800 font-medium">
                    Onboarding Complete! 🎉
                  </p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Checklist Items */}
      <Card>
        <CardHeader>
          <CardTitle>Onboarding Checklist</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {items.map((item) => (
              <div
                key={item.id}
                className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start gap-3">
                  {/* Checkbox */}
                  <button
                    onClick={() => handleToggleItem(item)}
                    disabled={savingItemId === item.id}
                    className="mt-1"
                  >
                    {savingItemId === item.id ? (
                      <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                    ) : item.completed ? (
                      <CheckCircle2 className="w-5 h-5 text-green-600" />
                    ) : (
                      <Circle className="w-5 h-5 text-gray-400 hover:text-blue-600" />
                    )}
                  </button>

                  {/* Content */}
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <h4
                        className={`font-medium ${
                          item.completed
                            ? 'text-gray-500 line-through'
                            : 'text-gray-900'
                        }`}
                      >
                        {item.label}
                      </h4>
                      {item.updated_at && (
                        <span className="text-xs text-gray-500">
                          {new Date(item.updated_at).toLocaleDateString()}
                        </span>
                      )}
                    </div>

                    {item.updated_by_email && (
                      <p className="text-xs text-gray-500 mt-1">
                        Updated by: {item.updated_by_email}
                      </p>
                    )}

                    {/* Notes Section */}
                    <div className="mt-3">
                      <Textarea
                        placeholder="Add notes..."
                        value={editingNotes[item.id] || ''}
                        onChange={(e) =>
                          setEditingNotes((prev) => ({
                            ...prev,
                            [item.id]: e.target.value,
                          }))
                        }
                        className="text-sm"
                        rows={2}
                      />
                      {editingNotes[item.id] !== (item.note || '') && (
                        <Button
                          onClick={() => handleSaveNote(item)}
                          disabled={savingItemId === item.id}
                          size="sm"
                          className="mt-2"
                        >
                          <Save className="w-4 h-4 mr-2" />
                          Save Note
                        </Button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
