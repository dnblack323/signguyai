/**
 * PageContext — Phase 3 Business Assistant
 *
 * Shared React context carrying "what is the user looking at right now".
 * Pages call `useSetPageContext({ page, recordType, recordId, recordLabel })`
 * on mount; the value auto-clears on unmount.
 *
 * The Business Assistant reads this so commands like "open this order" or
 * "create an order for this customer" can resolve correctly.
 */
import { createContext, useContext, useEffect, useState, useMemo, useRef, useCallback } from 'react';
import { useLocation } from 'react-router-dom';

const PageContextContext = createContext(null);

export function PageContextProvider({ children }) {
  const location = useLocation();
  // stack so nested components can push/pop context safely.
  const [stack, setStack] = useState([]);

  const pushContext = useCallback((ctx) => {
    const marker = ctx?._id || Symbol('ctx');
    setStack((prev) => [...prev, { ...ctx, _id: marker }]);
    return marker;
  }, []);

  const popContext = useCallback((marker) => {
    setStack((prev) => prev.filter((c) => c._id !== marker));
  }, []);

  const top = stack.length > 0 ? stack[stack.length - 1] : null;

  const value = useMemo(() => ({
    context: top
      ? {
          page: top.page || null,
          route: location.pathname + (location.search || ''),
          record_type: top.recordType || null,
          record_id: top.recordId || null,
          record_label: top.recordLabel || null,
        }
      : {
          page: null,
          route: location.pathname + (location.search || ''),
          record_type: null,
          record_id: null,
          record_label: null,
        },
    pushContext,
    popContext,
  }), [top, location.pathname, location.search, pushContext, popContext]);

  return (
    <PageContextContext.Provider value={value}>{children}</PageContextContext.Provider>
  );
}

/**
 * Call from a page component to declare its context. Auto-unregisters on unmount.
 * Example: useSetPageContext({ page: 'order_detail', recordType: 'order', recordId: id, recordLabel: 'ORD-0042' })
 */
export function useSetPageContext(ctx) {
  const api = useContext(PageContextContext);
  const markerRef = useRef(null);
  const serialized = JSON.stringify({
    page: ctx?.page || null,
    recordType: ctx?.recordType || null,
    recordId: ctx?.recordId || null,
    recordLabel: ctx?.recordLabel || null,
  });

  useEffect(() => {
    if (!api || !ctx?.page) return undefined;
    markerRef.current = Symbol('ctx');
    api.pushContext({ ...ctx, _id: markerRef.current });
    const m = markerRef.current;
    return () => api.popContext(m);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [serialized]);
}

export function usePageContext() {
  const api = useContext(PageContextContext);
  return api?.context || {
    page: null, route: null, record_type: null, record_id: null, record_label: null,
  };
}
