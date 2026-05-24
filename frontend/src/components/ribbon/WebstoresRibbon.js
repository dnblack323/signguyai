/**
 * Phase 2 — Webstores module ribbon.
 *
 * Office-style command bar that becomes the primary navigation surface
 * whenever the user is inside the Webstores module. Each group has 1-2
 * primary actions (icon + label + group caption below).
 *
 * Design rules respected from Phase 2 brief:
 *   - Re-uses existing routes only; does not invent backend features.
 *   - Drives the Webstores page activeTab via the `?tab=` query string so
 *     the underlying Webstores.js state stays in sync with the ribbon.
 *   - Create action signals the page via `?new=true` (already in use).
 *   - Targets with no destination yet are rendered disabled.
 */
import { useNavigate, useLocation } from 'react-router-dom';
import {
  LayoutDashboard, Plus, Store, Package, ShoppingCart,
  ClipboardList, Users, Wallet, BarChart3, Settings,
} from 'lucide-react';
import { cn } from '../../lib/utils';

const RibbonButton = ({
  icon: Icon, label, onClick, active = false, disabled = false, testId,
}) => (
  <button
    type="button"
    onClick={disabled ? undefined : onClick}
    disabled={disabled}
    className={cn(
      'flex flex-col items-center justify-center gap-1 px-3 py-1.5 rounded-md min-w-[68px] transition-colors',
      active
        ? 'bg-blue-100 text-blue-700 ring-1 ring-blue-200'
        : disabled
          ? 'text-gray-400 cursor-not-allowed'
          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100',
    )}
    data-testid={testId}
    aria-pressed={active}
  >
    <Icon className={cn('h-5 w-5', active ? 'text-blue-600' : disabled ? 'text-gray-300' : 'text-gray-500')} />
    <span className="text-[11px] leading-none font-medium">{label}</span>
  </button>
);

const RibbonGroup = ({ title, children, testId }) => (
  <div className="flex flex-col items-stretch px-2 first:pl-3 last:pr-3" data-testid={testId}>
    <div className="flex items-center gap-1 flex-1">
      {children}
    </div>
    <div className="text-[10px] uppercase tracking-wide text-gray-400 text-center mt-0.5">
      {title}
    </div>
  </div>
);

const GroupSeparator = () => (
  <div className="w-px self-stretch bg-gray-200 mx-1 my-1" aria-hidden="true" />
);

export const WebstoresRibbon = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const currentTab = searchParams.get('tab') || (location.pathname.startsWith('/products') ? 'products' : 'stores');
  const isOnWebstores = location.pathname.startsWith('/webstores');
  const isOnProducts = location.pathname.startsWith('/products');

  // Switch the inline tab inside /webstores by updating the URL query.
  const setWebstoresTab = (tabValue) => {
    if (!isOnWebstores) {
      navigate(`/webstores?tab=${tabValue}`);
      return;
    }
    const next = new URLSearchParams(location.search);
    next.set('tab', tabValue);
    next.delete('new');
    navigate(`${location.pathname}?${next.toString()}`, { replace: false });
  };

  const openCreateDialog = () => {
    if (!isOnWebstores) {
      navigate('/webstores?new=true');
      return;
    }
    const next = new URLSearchParams(location.search);
    next.set('new', 'true');
    navigate(`${location.pathname}?${next.toString()}`, { replace: false });
  };

  return (
    <div
      className="h-14 flex items-stretch px-3 bg-white border-b border-gray-100 overflow-x-auto scrollbar-none"
      data-testid="webstores-ribbon"
      role="toolbar"
      aria-label="Webstores command ribbon"
    >
      <RibbonGroup title="Dashboard" testId="webstores-ribbon-group-dashboard">
        <RibbonButton
          icon={LayoutDashboard}
          label="Overview"
          onClick={() => setWebstoresTab('stores')}
          active={isOnWebstores && currentTab === 'stores'}
          testId="webstores-ribbon-dashboard"
        />
      </RibbonGroup>

      <GroupSeparator />

      <RibbonGroup title="Create / Setup" testId="webstores-ribbon-group-create">
        <RibbonButton
          icon={Plus}
          label="New Store"
          onClick={openCreateDialog}
          testId="webstores-ribbon-create"
        />
      </RibbonGroup>

      <GroupSeparator />

      <RibbonGroup title="Manage Stores" testId="webstores-ribbon-group-stores">
        <RibbonButton
          icon={Store}
          label="All Stores"
          onClick={() => setWebstoresTab('stores')}
          active={isOnWebstores && currentTab === 'stores'}
          testId="webstores-ribbon-stores"
        />
      </RibbonGroup>

      <GroupSeparator />

      <RibbonGroup title="Products" testId="webstores-ribbon-group-products">
        <RibbonButton
          icon={Package}
          label="Catalog"
          onClick={() => navigate('/products')}
          active={isOnProducts}
          testId="webstores-ribbon-products"
        />
      </RibbonGroup>

      <GroupSeparator />

      <RibbonGroup title="Orders" testId="webstores-ribbon-group-orders">
        <RibbonButton
          icon={ShoppingCart}
          label="Webstore Orders"
          onClick={() => setWebstoresTab('orders')}
          active={isOnWebstores && currentTab === 'orders'}
          testId="webstores-ribbon-orders"
        />
      </RibbonGroup>

      <GroupSeparator />

      <RibbonGroup title="Questionnaires" testId="webstores-ribbon-group-questionnaires">
        <RibbonButton
          icon={ClipboardList}
          label="Forms"
          onClick={() => navigate('/questionnaires')}
          testId="webstores-ribbon-questionnaires"
        />
      </RibbonGroup>

      <GroupSeparator />

      <RibbonGroup title="Owner Portal" testId="webstores-ribbon-group-owner-portal">
        <RibbonButton
          icon={Users}
          label="Open Portal"
          onClick={() => window.open('/owner-portal', '_blank', 'noopener')}
          testId="webstores-ribbon-owner-portal"
        />
      </RibbonGroup>

      <GroupSeparator />

      <RibbonGroup title="Payments / Payouts" testId="webstores-ribbon-group-payments">
        <RibbonButton
          icon={Wallet}
          label="Payments"
          onClick={() => navigate('/admin/payments')}
          testId="webstores-ribbon-payments"
        />
      </RibbonGroup>

      <GroupSeparator />

      <RibbonGroup title="Analytics" testId="webstores-ribbon-group-analytics">
        <RibbonButton
          icon={BarChart3}
          label="Profit & Margin"
          onClick={() => navigate('/reports/profit-margin')}
          testId="webstores-ribbon-analytics"
        />
      </RibbonGroup>

      <GroupSeparator />

      <RibbonGroup title="Tools / Settings" testId="webstores-ribbon-group-tools">
        <RibbonButton
          icon={Settings}
          label="Settings"
          onClick={() => navigate('/settings')}
          testId="webstores-ribbon-tools"
        />
      </RibbonGroup>
    </div>
  );
};

export default WebstoresRibbon;
