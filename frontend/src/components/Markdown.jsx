import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

// Replace bare [S1], [S2] tokens in text nodes with a citation chip.
function renderText(children) {
  if (typeof children === "string") {
    const parts = children.split(/(\[S\d+\])/g);
    return parts.map((p, i) =>
      /^\[S\d+\]$/.test(p) ? (
        <span key={i} className="cite-chip">{p}</span>
      ) : (
        <span key={i}>{p}</span>
      )
    );
  }
  return children;
}

export default function Markdown({ children }) {
  return (
    <div className="md">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p:  ({ children }) => <p>{renderText(children)}</p>,
          li: ({ children }) => <li>{renderText(children)}</li>,
        }}
      >
        {children || ""}
      </ReactMarkdown>
    </div>
  );
}
