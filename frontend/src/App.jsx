import { useState, useEffect } from "react";
import { theme as G, googleFonts } from "./constants/theme";
import { Navbar } from "./components/shared";
import { useAnalysis } from "./hooks/useAnalysis";
import AnalyzePage from "./pages/AnalyzePage";
import ResultPage from "./pages/ResultPage";
import DashboardPage from "./pages/DashboardPage";

const globalCss = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: ${G.bg};
    color: ${G.text};
    font-family: 'Inter', sans-serif;
    font-size: 14px;
    line-height: 1.6;
    min-height: 100vh;
  }
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: ${G.surface}; }
  ::-webkit-scrollbar-thumb { background: ${G.border}; border-radius: 3px; }

  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes fadeUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: translateY(0); } }
`;

export default function App(){
  const [page, setPage] = useState("analyze");
  const { loading, result, history, analyze, clearResult } = useAnalysis();

  useEffect(() => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = googleFonts;
    document.head.appendChild(link);

    const style = document.createElement("style");
    style.textContent = globalCss;
    document.head.appendChild(style);

    return () => {
      document.head.removeChild(link);
      document.head.removeChild(style);
    };
  }, []);

  function handleNavChange(newPage){
    clearResult();
    setPage(newPage);
  }

  function handleAnalyze(formData){
    analyze(formData);
    setPage("result");
  }

  function renderPage(){
    if (page === "result" && result){
      return(
        <ResultPage
          result={result}
          onBack={() => { clearResult(); setPage("analyze"); }}
        />
      );
    }
    if (page === "dashboard"){
      return <DashboardPage history={history} />;
    }
    return <AnalyzePage onAnalyze={handleAnalyze} loading={loading} />
  }
  
  // Luego cambiar con React Router
  return(
    <div style={{ minHeight: "100vh", background: G.bg }}>
      <Navbar
        page={page === "result" ? "analyze" : page } 
        setPage={handleNavChange} 
      />
      {renderPage()}
    </div>
  );
}
