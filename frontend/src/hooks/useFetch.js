import { useCallback, useEffect, useRef, useState } from "react";

// Charge des données et expose { data, loading, error, reload }.
export default function useFetch(fetcher, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null });
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  const load = useCallback(async () => {
    setState((s) => ({ ...s, loading: true, error: null }));
    try {
      const data = await fetcherRef.current();
      setState({ data, loading: false, error: null });
    } catch (e) {
      setState({ data: null, loading: false, error: e.message });
    }
  }, []);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load(); }, deps);
  return { ...state, reload: load };
}
