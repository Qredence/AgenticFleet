import React from "react";

// Basic component to render custom content from Chainlit
const CustomRenderer = (props) => {
  // Props will contain the 'content' dictionary sent from cl.Custom
  const { content } = props;

  console.log("CustomRenderer received content:", content);

  // Simple rendering based on content type (can be expanded)
  let renderedContent;
  if (content && content.type === "article") {
    // Placeholder for rendering markdown article - could use a library like react-markdown
    renderedContent = (
      <div
        style={{
          border: "1px solid #eee",
          borderRadius: "5px",
          padding: "15px",
          margin: "10px 0",
          backgroundColor: "#f9f9f9",
          whiteSpace: "pre-wrap",
        }}
      >
        <h4
          style={{
            marginTop: 0,
            borderBottom: "1px solid #ddd",
            paddingBottom: "5px",
          }}
        >
          Article
        </h4>
        <pre style={{ fontFamily: "inherit", fontSize: "inherit" }}>
          {content.data || "No article data provided."}
        </pre>
      </div>
    );
  } else if (content && content.type === "rich_code") {
    // Placeholder for rendering code - could use a library like react-syntax-highlighter
    const language = content.language || "text";
    renderedContent = (
      <div
        style={{
          border: "1px solid #ddd",
          borderRadius: "5px",
          padding: "15px",
          margin: "10px 0",
          backgroundColor: "#2d2d2d",
          color: "#f1f1f1",
        }}
      >
        <h4
          style={{
            marginTop: 0,
            borderBottom: "1px solid #555",
            paddingBottom: "5px",
          }}
        >
          Code Block ({language})
        </h4>
        <pre>
          <code>{content.data || "No code data provided."}</code>
        </pre>
      </div>
    );
  } else {
    renderedContent = (
      <div
        style={{ border: "1px solid red", padding: "10px", margin: "10px 0" }}
      >
        <h4>Unknown Custom Content Type</h4>
        <pre>{JSON.stringify(content, null, 2)}</pre>
      </div>
    );
  }

  return renderedContent;
};

// Chainlit expects the component to be registered globally.
// We assume Chainlit loads this file and makes the component available.
// If using a bundler, you might need: window.CustomRenderer = CustomRenderer;
// For simple cases, Chainlit might pick up the default export if the file path matches the component name expected.
// Let's assume Chainlit can find 'CustomRenderer' from 'custom_renderer.js' for now.
// We might need to adjust registration based on how Chainlit loads custom JS.
export default CustomRenderer;
