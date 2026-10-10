import { useEffect, useRef } from "react";
import mermaid from "mermaid";

mermaid.initialize({
  startOnLoad: false,
  theme: "default",
  securityLevel: "loose",
  flowchart: { useMaxWidth: true, htmlLabels: true },
});

let counter = 0;

export default function MermaidDiagram({ chart }: { chart: string }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current || !chart.trim()) return;
    const id = `mmd-${++counter}`;
    let cancelled = false;
    mermaid
      .render(id, chart)
      .then(({ svg }) => {
        if (!cancelled && ref.current) {
          ref.current.innerHTML = svg;
        }
      })
      .catch(() => {
        if (ref.current) {
          ref.current.innerHTML = `<pre class="text-xs text-red-600">${chart
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")}</pre>`;
        }
      });
    return () => {
      cancelled = true;
    };
  }, [chart]);

  return <div className="mermaid" ref={ref} />;
}
