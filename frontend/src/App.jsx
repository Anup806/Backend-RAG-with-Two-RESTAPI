const apiCards = [
  {
    title: 'Document Ingestion API',
    description: 'Upload PDFs or TXT files, chunk text, embed it, and store vectors in Qdrant.',
    path: 'POST /ingest/upload',
  },
  {
    title: 'Conversational RAG API',
    description: 'Ask questions over the indexed documents and keep multi-turn chat memory in Redis.',
    path: 'POST /chat/message',
  },
  {
    title: 'Booking Workflow',
    description: 'Detect interview booking details, persist them in SQLite, and return confirmations.',
    path: 'GET /chat/bookings',
  },
];

const stack = ['FastAPI', 'Qdrant', 'Redis', 'SQLite', 'Sentence Transformers', 'Groq'];

export default function App() {
  return (
    <main className="page-shell">
      <section className="hero">
        <div className="eyebrow">Backend-RAG-with-Two-RESTAPI</div>
        <h1>Two APIs, one backend, and a frontend shell ready for expansion.</h1>
        <p>
          This layout separates the FastAPI backend from the UI so the project can grow into a clean
          full-stack RAG system without tangling deployment concerns.
        </p>

        <div className="hero-actions">
          <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer">
            Open API docs
          </a>
          <span>Backend: localhost:8000</span>
          <span>Frontend: localhost:3000</span>
        </div>

        <div className="stack-row">
          {stack.map((item) => (
            <span key={item}>{item}</span>
          ))}
        </div>
      </section>

      <section className="card-grid" aria-label="API overview">
        {apiCards.map((card) => (
          <article className="api-card" key={card.title}>
            <p className="path">{card.path}</p>
            <h2>{card.title}</h2>
            <p>{card.description}</p>
          </article>
        ))}
      </section>
    </main>
  );
}