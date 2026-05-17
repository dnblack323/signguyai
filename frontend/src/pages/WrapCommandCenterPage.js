// Phase 1: Wrap Command Center page.
// Composes the reusable wrap components into a single workspace tied to a
// specific order item. Phase 1 uses placeholder data when backend fields
// are not yet populated, but pulls real order/item/customer values when
// available so the screen feels real to the user.

import { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Loader2 } from 'lucide-react';

import WrapCommandHeader from '../components/wrap/WrapCommandHeader';
import WrapStatusBar from '../components/wrap/WrapStatusBar';
import WrapTabNavigation from '../components/wrap/WrapTabNavigation';
import WrapSidebar from '../components/wrap/WrapSidebar';

import OverviewTab from '../components/wrap/tabs/OverviewTab';
import VehicleInfoTab from '../components/wrap/tabs/VehicleInfoTab';
import MeasurementsTab from '../components/wrap/tabs/MeasurementsTab';
import PricingTab from '../components/wrap/tabs/PricingTab';
import DesignTab from '../components/wrap/tabs/DesignTab';
import ContractTab from '../components/wrap/tabs/ContractTab';
import InspectionTab from '../components/wrap/tabs/InspectionTab';
import ProductionTab from '../components/wrap/tabs/ProductionTab';
import InstallTab from '../components/wrap/tabs/InstallTab';
import PhotosFilesTab from '../components/wrap/tabs/PhotosFilesTab';
import AftercareTab from '../components/wrap/tabs/AftercareTab';
import AIAssistantTab from '../components/wrap/tabs/AIAssistantTab';

import { PLACEHOLDER_HEADER, isWrapCategory } from '../components/wrap/constants';
import { getAuthToken } from '../lib/authStorage';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const hdr = () => ({ Authorization: `Bearer ${getAuthToken()}`, 'Content-Type': 'application/json' });

function deriveHeader(order, item, customer) {
  if (!order && !item) return PLACEHOLDER_HEADER;
  const snapshot = item?.pricing_snapshot;
  const quoted = snapshot?.active_price || item?.estimated_price || PLACEHOLDER_HEADER.quoted_price;
  const specs = item?.specs || {};
  const vehicle = [specs.vehicle_year, specs.vehicle_make, specs.vehicle_model]
    .filter(Boolean)
    .join(' ') || PLACEHOLDER_HEADER.vehicle;
  return {
    order_number: order?.order_number ? `Order #${order.order_number}` : PLACEHOLDER_HEADER.order_number,
    customer_name: customer?.name || order?.customer_name || PLACEHOLDER_HEADER.customer_name,
    business_name: customer?.company || order?.customer_company || '',
    item_name: item?.item_name || PLACEHOLDER_HEADER.item_name,
    vehicle,
    wrap_type: specs.wrap_type || item?.item_category?.replace(/_/g, ' ') || PLACEHOLDER_HEADER.wrap_type,
    status: PLACEHOLDER_HEADER.status,
    quoted_price: quoted,
    deposit_status: PLACEHOLDER_HEADER.deposit_status,
    balance_due: quoted,
  };
}

export default function WrapCommandCenterPage() {
  const { orderId, itemId } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [order, setOrder] = useState(null);
  const [item, setItem] = useState(null);
  const [customer, setCustomer] = useState(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const res = await axios.get(`${API}/orders/${orderId}`, { headers: hdr() });
        if (cancelled) return;
        const o = res.data || null;
        setOrder(o);
        const tickets = o?.job_tickets || [];
        const matched = tickets.find((t) => t.id === itemId) || null;
        setItem(matched);
        if (o?.customer_id) {
          try {
            const cr = await axios.get(`${API}/customers/${o.customer_id}`, { headers: hdr() });
            if (!cancelled) setCustomer(cr.data || null);
          } catch (_) {
            // customer fetch is best-effort; placeholder/order fallback is fine
          }
        }
      } catch (_) {
        // network/auth failure — fall back to placeholder UI so users still see structure
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    if (orderId) load();
    return () => { cancelled = true; };
  }, [orderId, itemId]);

  const header = useMemo(() => deriveHeader(order, item, customer), [order, item, customer]);

  // If we successfully loaded an item and it's not a wrap category, gently
  // redirect the user back to the order detail to avoid showing a wrap
  // workspace for a non-wrap line item.
  useEffect(() => {
    if (!loading && item && !isWrapCategory(item.item_category)) {
      navigate(`/orders/${orderId}`, { replace: true });
    }
  }, [loading, item, orderId, navigate]);

  const renderTab = () => {
    switch (tab) {
      case 'overview':     return <OverviewTab header={header} />;
      case 'vehicle':      return <VehicleInfoTab />;
      case 'measurements': return <MeasurementsTab />;
      case 'pricing':      return <PricingTab header={header} />;
      case 'design':       return <DesignTab />;
      case 'contract':     return <ContractTab />;
      case 'inspection':   return <InspectionTab />;
      case 'production':   return <ProductionTab />;
      case 'install':      return <InstallTab />;
      case 'photos':       return <PhotosFilesTab />;
      case 'aftercare':    return <AftercareTab />;
      case 'ai':           return <AIAssistantTab onJumpToTab={setTab} />;
      default:             return <OverviewTab header={header} />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20" data-testid="wrap-cc-loading">
        <Loader2 className="w-8 h-8 animate-spin text-violet-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50" data-testid="wrap-command-center-page">
      <WrapCommandHeader orderId={orderId} header={header} />
      <div className="px-4 sm:px-6 pt-3">
        <WrapStatusBar currentStatus={header.status} testId="wrap-cc-status-bar" />
      </div>
      <WrapTabNavigation activeTab={tab} onChange={setTab} />
      <div className="px-4 sm:px-6 py-4">
        <div className="grid grid-cols-1 xl:grid-cols-[1fr_320px] gap-4">
          <div data-testid="wrap-cc-tab-content">
            {renderTab()}
          </div>
          <div className="hidden xl:block">
            <WrapSidebar header={header} />
          </div>
        </div>
      </div>
    </div>
  );
}
