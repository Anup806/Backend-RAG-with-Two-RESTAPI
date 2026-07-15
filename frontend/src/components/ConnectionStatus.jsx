import { useEffect, useState } from 'react';
import { checkHealth } from '../api/client';

const POLL_INTERVAL_MS = 15_000;

export default function ConnectionStatus() {
  const [online, setOnline] = useState(null); // null = unknown/checking

  useEffect(() => {
    let cancelled = false;

    async function ping() {
      try {
        await checkHealth();
        if (!cancelled) setOnline(true);
      } catch {
        if (!cancelled) setOnline(false);
      }
    }

    ping();
    const timer = setInterval(ping, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, []);

  const label = online === null ? 'Checking…' : online ? 'Backend online' : 'Backend unreachable';
  const dotClass = online === null ? 'status-dot-pending' : online ? 'status-dot-online' : 'status-dot-offline';

  return (
    <span className="status-pill">
      <span className={`status-dot ${dotClass}`} />
      {label}
    </span>
  );
}
