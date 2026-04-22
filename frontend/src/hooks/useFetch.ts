import { useCallback, useEffect, useState } from 'react';
import { getErrorMessage } from '../services/api';

export function useFetch<T>(loader: () => Promise<T>, dependencies: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await loader();
      setData(result);
    } catch (fetchError) {
      setError(getErrorMessage(fetchError));
    } finally {
      setLoading(false);
    }
  }, dependencies);

  useEffect(() => {
    void refetch();
  }, [refetch]);

  return { data, loading, error, refetch };
}
