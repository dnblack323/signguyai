/**
 * Global banner displayed at the top of every page.
 * Renders an Announcement (info / warning / critical) and a Maintenance Mode notice.
 *
 * Reads from public endpoints — no auth required, so it shows up on /login too.
 */

import { useEffect, useState, useCallback } from 'react';
import { X, AlertTriangle, AlertCircle, Info, Wrench } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const SEVERITY_STYLES = {
  info: {
    bg: 'bg-blue-600',
    text: 'text-white',
    Icon: Info,
  },
  warning: {
    bg: 'bg-amber-500',
    text: 'text-white',
    Icon: AlertTriangle,
  },
  critical: {
    bg: 'bg-red-600',
    text: 'text-white',
    Icon: AlertCircle,
  },
};

const dismissedKey = (updatedAt) => `announcement_dismissed:${updatedAt || ''}`;

export default function GlobalBanner() {
  const [announcement, setAnnouncement] = useState(null);
  const [maintenance, setMaintenance] = useState(null);
  const [dismissed, setDismissed] = useState(false);

  const fetchSettings = useCallback(async () => {
    try {
      const [aRes, mRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/platform/announcement`),
        fetch(`${BACKEND_URL}/api/platform/maintenance`),
      ]);
      if (aRes.ok) {
        const d = await aRes.json();
        setAnnouncement(d.announcement || null);
        try {
          const k = dismissedKey(d.announcement?.updated_at);
          setDismissed(localStorage.getItem(k) === '1');
        } catch {
          /* ignore */
        }
      }
      if (mRes.ok) {
        const d = await mRes.json();
        setMaintenance(d.maintenance && d.maintenance.enabled ? d.maintenance : null);
      }
    } catch {
      /* silent — banner is best-effort */
    }
  }, []);

  useEffect(() => {
    fetchSettings();
    // Re-poll every 60 seconds so an admin enabling maintenance is reflected quickly
    const i = setInterval(fetchSettings, 60_000);
    return () => clearInterval(i);
  }, [fetchSettings]);

  if (!announcement && !maintenance) return null;

  const handleDismiss = () => {
    try {
      const k = dismissedKey(announcement?.updated_at);
      localStorage.setItem(k, '1');
    } catch {
      /* ignore */
    }
    setDismissed(true);
  };

  return (
    <div className="sticky top-0 z-[60]" data-testid="global-banner">
      {maintenance && (
        <div
          className="bg-rose-700 text-white px-4 py-2 text-sm flex items-center gap-2 justify-center"
          data-testid="global-banner-maintenance"
        >
          <Wrench className="w-4 h-4 shrink-0" />
          <span className="font-medium">Maintenance mode:</span>
          <span>{maintenance.message || "We're doing scheduled maintenance — please try again shortly."}</span>
        </div>
      )}
      {announcement && !dismissed && (() => {
        const sev = SEVERITY_STYLES[announcement.severity] || SEVERITY_STYLES.info;
        const Icon = sev.Icon;
        return (
          <div
            className={`${sev.bg} ${sev.text} px-4 py-2 text-sm flex items-center gap-2 justify-center`}
            data-testid="global-banner-announcement"
          >
            <Icon className="w-4 h-4 shrink-0" />
            <span data-testid="global-banner-announcement-message">
              {announcement.message}
            </span>
            {announcement.dismissable && (
              <button
                type="button"
                onClick={handleDismiss}
                className="ml-3 opacity-80 hover:opacity-100"
                aria-label="Dismiss"
                data-testid="global-banner-dismiss-btn"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        );
      })()}
    </div>
  );
}
