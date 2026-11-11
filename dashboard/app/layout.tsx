export const metadata = {
  title: 'MNCD · ACRS objective O4: certified execution',
  description:
    'Byzantine-tolerant coordination for certified execution, evaluated on AppWorld with open-weight models; earlier peer-to-peer mesh results included.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        {/* MathJax renders the formulas in the "Mathematical core" section. Pinned version from jsDelivr.
            The former polyfill.io script was removed: that domain was taken over in 2024 and served malicious code. */}
        <script
          id="MathJax-script"
          async
          src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js"
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
