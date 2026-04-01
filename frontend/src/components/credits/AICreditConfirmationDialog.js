import { useEffect, useMemo, useRef, useState } from 'react';
import { AlertTriangle, Coins, Loader2, Sparkles } from 'lucide-react';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '../ui/dialog';
import { Button } from '../ui/button';
import { Checkbox } from '../ui/checkbox';
import { Label } from '../ui/label';
import { Badge } from '../ui/badge';
import { getAuthToken } from '../../lib/authStorage';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const useAICreditGuard = () => {
  const [dialogState, setDialogState] = useState({ open: false, mode: 'confirm', data: null });
  const [savingPreference, setSavingPreference] = useState(false);
  const [rememberPreference, setRememberPreference] = useState(false);
  const executeRef = useRef(null);
  const contextRef = useRef(null);
  const pendingPromiseRef = useRef(null);

  const fetchPreflight = async ({ actionType, creditsRequired }) => {
    const token = getAuthToken();
    const response = await fetch(`${API_URL}/api/credits/preflight`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ action_type: actionType, credits_required: creditsRequired }),
    });
    return response.json();
  };

  const savePreference = async (actionType, cost, currentPreferences) => {
    const token = getAuthToken();
    const acknowledged = { ...(currentPreferences?.acknowledged_costs || {}), [actionType]: cost };
    await fetch(`${API_URL}/api/credits/preferences`, {
      method: 'PUT',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        hide_ai_credit_popup: true,
        acknowledged_costs: acknowledged,
      }),
    });
  };

  const runGuardedAction = async ({ actionType, featureName, creditsRequired, execute }) => {
    const preflight = await fetchPreflight({ actionType, creditsRequired });
    const enough = preflight?.sufficient_credits;

    if (!enough) {
      setDialogState({
        open: true,
        mode: 'insufficient',
        data: { ...preflight, featureName },
      });
      return null;
    }

    if (preflight?.should_show_popup) {
      return new Promise((resolve, reject) => {
        executeRef.current = execute;
        contextRef.current = { actionType, featureName, preflight };
        pendingPromiseRef.current = { resolve, reject };
        setRememberPreference(false);
        setDialogState({
          open: true,
          mode: 'confirm',
          data: { ...preflight, featureName },
        });
      });
    }

    const result = await execute();
    window.dispatchEvent(new Event('creditsRefresh'));
    return result;
  };

  const handleConfirm = async () => {
    if (!executeRef.current || !contextRef.current) {
      setDialogState({ open: false, mode: 'confirm', data: null });
      return;
    }

    const { actionType, preflight } = contextRef.current;
    setSavingPreference(true);
    try {
      if (rememberPreference) {
        await savePreference(actionType, preflight.credit_cost, preflight.preferences);
      }
      setDialogState({ open: false, mode: 'confirm', data: null });
      const result = await executeRef.current();
      window.dispatchEvent(new Event('creditsRefresh'));
      pendingPromiseRef.current?.resolve?.(result);
    } catch (error) {
      pendingPromiseRef.current?.reject?.(error);
      throw error;
    } finally {
      setSavingPreference(false);
      executeRef.current = null;
      contextRef.current = null;
      pendingPromiseRef.current = null;
      setRememberPreference(false);
    }
  };

  const handleClose = () => {
    pendingPromiseRef.current?.resolve?.(null);
    setDialogState({ open: false, mode: 'confirm', data: null });
    executeRef.current = null;
    contextRef.current = null;
    pendingPromiseRef.current = null;
    setRememberPreference(false);
  };

  const dialog = (
    <AICreditConfirmationDialog
      open={dialogState.open}
      mode={dialogState.mode}
      data={dialogState.data}
      rememberPreference={rememberPreference}
      setRememberPreference={setRememberPreference}
      savingPreference={savingPreference}
      onConfirm={handleConfirm}
      onClose={handleClose}
    />
  );

  return { runGuardedAction, dialog };
};

export const AICreditConfirmationDialog = ({
  open,
  mode,
  data,
  rememberPreference,
  setRememberPreference,
  savingPreference,
  onConfirm,
  onClose,
}) => {
  const total = data?.total_credits || 0;
  const reasons = data?.popup_reasons || [];

  const warningBadges = useMemo(() => {
    const map = {
      cost_changed: 'Cost changed',
      low_balance: 'Low balance',
      purchased_credits_needed: 'Will use purchased credits',
      high_cost_action: 'High-cost action',
      preference_off: 'Confirmation enabled',
    };
    return reasons.map((reason) => map[reason] || reason);
  }, [reasons]);

  return (
    <Dialog open={open} onOpenChange={(nextOpen) => !nextOpen && onClose()}>
      <DialogContent data-testid="ai-credit-confirmation-dialog">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {mode === 'insufficient' ? <AlertTriangle className="h-5 w-5 text-amber-500" /> : <Sparkles className="h-5 w-5 text-purple-500" />}
            {mode === 'insufficient' ? 'Not enough AI credits' : 'Confirm AI credit usage'}
          </DialogTitle>
          <DialogDescription>
            {mode === 'insufficient'
              ? 'This AI action is blocked until more credits are available.'
              : 'Review the credit cost before continuing.'}
          </DialogDescription>
        </DialogHeader>

        {data && (
          <div className="space-y-4">
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-sm text-slate-500">Action</p>
              <p className="text-base font-semibold text-slate-900 mt-1">{data.featureName || data.action_type}</p>
              <p className="text-sm text-slate-700 mt-3">This action will use <span className="font-semibold">{data.credit_cost}</span> AI credit{data.credit_cost === 1 ? '' : 's'}.</p>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="rounded-lg border p-3" data-testid="ai-credit-monthly-balance">
                <p className="text-xs uppercase text-slate-500">Monthly</p>
                <p className="text-xl font-bold text-slate-900 mt-1">{data.monthly_credits}</p>
              </div>
              <div className="rounded-lg border p-3" data-testid="ai-credit-purchased-balance">
                <p className="text-xs uppercase text-slate-500">Purchased</p>
                <p className="text-xl font-bold text-slate-900 mt-1">{data.purchased_credits}</p>
              </div>
              <div className="rounded-lg border p-3" data-testid="ai-credit-total-balance">
                <p className="text-xs uppercase text-slate-500">Total</p>
                <p className="text-xl font-bold text-slate-900 mt-1">{total}</p>
              </div>
            </div>

            {warningBadges.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {warningBadges.map((badge) => <Badge key={badge} variant="outline">{badge}</Badge>)}
              </div>
            )}

            {mode !== 'insufficient' && (
              <div className="flex items-start gap-3 rounded-lg border border-slate-200 p-3">
                <Checkbox id="hide-ai-credit-popup-checkbox" checked={rememberPreference} onCheckedChange={setRememberPreference} data-testid="hide-ai-credit-popup-checkbox" />
                <div>
                  <Label htmlFor="hide-ai-credit-popup-checkbox">Do not show this message again</Label>
                  <p className="text-xs text-slate-500 mt-1">The popup will still reappear for high-cost actions, low-balance warnings, cost changes, or when purchased credits will be used.</p>
                </div>
              </div>
            )}

            {mode === 'insufficient' && (
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                Required: {data.credit_cost} • Available: {data.monthly_credits} monthly, {data.purchased_credits} purchased
              </div>
            )}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          {mode === 'insufficient' ? (
            <Button onClick={() => { onClose(); window.location.href = '/settings'; }} className="bg-blue-600 hover:bg-blue-700" data-testid="ai-credit-buy-more-button">
              <Coins className="h-4 w-4 mr-2" /> Buy Credits
            </Button>
          ) : (
            <Button onClick={onConfirm} disabled={savingPreference} className="bg-purple-600 hover:bg-purple-700" data-testid="ai-credit-continue-button">
              {savingPreference ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
              Continue
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
