import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/**
 * Markdown with inline [S#] citation pills. Post-processes the rendered text
 * nodes to replace bare [S1], [S2] sequences with a highlighted chip.
 */
function renderText(children) {
  if (typeof children === "string") {
    const parts = children.split(/(\[S\d+\])/g);
    return parts.map((p, i) => {
      if (/^\[S\d+\]$/.test(p)) {
        return (
          <span key={i} className="cite-chip">
            {p}
          </span>
        );
      }
      return <span key={i}>{p}</span>;
    });
  }
  return children;
}

export default function Markdown({ children }) {
  return (
    <div className="md">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ children }) => <p>{renderText(children)}</p>,
          li: ({ children }) => <li>{renderText(children)}</li>,
        }}
      >
        {children || ""}
      </ReactMarkdown>
    </div>
  );
}
