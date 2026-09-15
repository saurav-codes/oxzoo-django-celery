import { useEffect, useState } from "react";

// One template literal on purpose: the full string must survive minification
// as one contiguous piece so the deploy gate can grep the built bundle.
const greeting = `hello world oxzoo-django-celery_${import.meta.env.GREETING_TAG}`;

export default function App() {
  const [api, setApi] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let alive = true;
    fetch("/api/greeting")
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        if (alive) setApi(data);
      })
      .catch((err) => {
        if (alive) setError(`api error: ${err.message}`);
      });
    return () => {
      alive = false;
    };
  }, []);

  return (
    <main>
      <h1>oxzoo-django-celery</h1>
      <p className="line">build-time: {greeting}</p>
      <p className="line">
        {error ?? (api ? `api: ${JSON.stringify(api)}` : "loading...")}
      </p>
    </main>
  );
}
