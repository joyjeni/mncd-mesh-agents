export const metadata = {
  title: 'MNCD — Decentralized Context-Sharing Mesh',
  description: 'Live metrics, figures, and journal artefacts for the P2P multi-agent LLM mesh',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        {/* MathJax for rendering LaTeX formulas */}
        <script
          src="https://polyfill.io/v3/polyfill.min.js?features=es6"
          async
        />
        <script
          id="MathJax-script"
          async
          src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"
        />
      </head>
      <body style={{
        fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
        background: '#f5f7fa',
        color: '#1f2937',
        margin: 0,
      }}>
        {children}
      </body>
    </html>
  );
}
