import { useCallback, useEffect, useRef, useState } from "react";

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

  useEffect(() => { load(); }, deps);
  return { ...state, reload: load };
}
