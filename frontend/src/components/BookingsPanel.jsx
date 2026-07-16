import { useCallback, useEffect, useState } from 'react';
import { getBookings, deleteBookingsBySession } from '../api/client';

// The backend deletes bookings by session_id, not by individual booking id
// (DELETE /chat/bookings/{session_id} removes every booking tied to that session).
// Grouping the UI by session makes the delete action honest about what it removes,
// instead of a per-row delete button that would silently take out sibling rows too.
function groupBySession(bookings) {
  const map = new Map();
  for (const b of bookings) {
    if (!map.has(b.session_id)) map.set(b.session_id, []);
    map.get(b.session_id).push(b);
  }
  return Array.from(map.entries());
}

export default function BookingsPanel() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(() => {
    setLoading(true);
    getBookings()
      .then((data) => setBookings(data.bookings))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleDeleteSession(sessionId) {
    try {
      await deleteBookingsBySession(sessionId);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  const groups = groupBySession(bookings);

  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Interview Bookings</h2>
        <button type="button" onClick={load}>Refresh</button>
      </div>

      {loading && <p className="empty-state">Loading…</p>}
      {error && <p className="error-text">{error}</p>}
      {!loading && groups.length === 0 && <p className="empty-state">No bookings yet.</p>}

      <div className="bookings-table">
        {groups.map(([sessionId, group]) => (
          <div className="booking-group" key={sessionId}>
            <div className="booking-group-header">
              <span className="session-pill">Session: {sessionId}</span>
              <button type="button" onClick={() => handleDeleteSession(sessionId)}>
                Delete all ({group.length})
              </button>
            </div>
            {group.map((b) => (
              <div className="booking-row" key={b.id}>
                <div>
                  <strong>{b.name}</strong>
                  <span className="booking-meta">{b.email}</span>
                </div>
                <span>{b.date} · {b.time}</span>
              </div>
            ))}
          </div>
        ))}
      </div>
    </section>
  );
}
