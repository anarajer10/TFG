import { useState, useEffect } from "react";
import { theme as G, googleFonts } from "./constants/theme";
import { Navbar } from "./components/shared";
import { useAnalysis } from "./hooks/useAnalysis";
import AnalyzePage from "./pages/AnalyzePage";
import ResultPage from "./pages/ResultPage";
import DashboardPage from "./pages/DashboardPage";
import HomePage from "./pages/HomePage";
import RecentPage from "./pages/RecentPage";

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
  const [page, setPage] = useState(() => window.location.hash.replace('#', '') || 'home');
  const [lang, setLang] = useState("es");
  const [ selectedResult, setSelectedResult] = useState(null);
  const { loading, error, result, history, analyze, clearResult } = useAnalysis();

  useEffect(() => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = googleFonts;
    document.head.appendChild(link);

    const style = document.createElement("style");
    style.textContent = globalCss;
    document.head.appendChild(style);

    const onHash = () => {
      const h = window.location.hash.replace('#', '') || 'home';
      setPage(h);
    };
    window.addEventListener('hashchange', onHash);
    return () => {
      document.head.removeChild(link);
      document.head.removeChild(style);
      window.removeEventListener('hashchange', onHash);
    };
  }, []);

  function handleNavChange(newPage){
    clearResult();
    window.location.hash = newPage;
    setPage(newPage);
  }

  function handleAnalyze(formData){
    analyze({...formData, lang});
    window.location.hash = 'result';
    setPage("result");
  }

  function handleSelectResult(r){
    setSelectedResult(r);
    window.location.hash = 'result';
    setPage("result");
  }
  
  // Luego cambiar con React Router
  return(
    <div style={{ minHeight: "100vh", background: G.bg }}>
      <Navbar
        page={page === "result" ? "analyze" : page } 
        setPage={handleNavChange} 
        lang={lang}
        setLang={setLang}
      />
      {page === "result" && (selectedResult || result) ? (
        <ResultPage
          result={selectedResult || result}
          onBack={() => { clearResult(); setSelectedResult(null); window.Location.hash = 'analyze'; setPage("analyze"); }}
          lang={lang}
        />
      ) : page === "dashboard" ? (
          <DashboardPage history={history} lang={lang} onSelect={handleSelectResult}/>
      ) : page === "recientes" ? (
          <RecentPage onSelect={handleSelectResult} lang={lang} />
      ) : page === "home" ? (
          <HomePage setPage={setPage} lang={lang} />
      ) : (
          <AnalyzePage onAnalyze={handleAnalyze} loading={loading} error={error} lang={lang} />
      )}
    </div>
  );
}
