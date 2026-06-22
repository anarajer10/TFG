import { useState, useEffect } from "react";
import { getNoticia } from "./services/api";
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
  :focus-visible { outline: 2px solid ${G.accent}; outline-offset: 3px; border-radius: 4px; }
  `;

// Componente raíz que gestiona el enrutamiento por hash de URL y el estado global de sesión
export default function App(){
  const parseHash = () => {
    const hash = window.location.hash.replace('#', '') || 'home';
    const [p, id] = hash.split('/');
    return { page: p || 'home', id: id ? parseInt(id): null };
  };
  const [page, setPage] = useState(() => parseHash().page);
  const [urlId, setUrlId] = useState(() => parseHash().id)
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
      const { page: p, id } = parseHash();
      setPage(p);
      setUrlId(id);
    };
    window.addEventListener('hashchange', onHash);
    return () => {
      document.head.removeChild(link);
      document.head.removeChild(style);
      window.removeEventListener('hashchange', onHash);
    };
  }, []);

  useEffect(() => {
    if (urlId && !selectedResult && !result) {
      getNoticia(urlId).then(data => setSelectedResult(data))
      .catch(() => { setUrlId(null); setPage('home'); })
    }
  }, [urlId])

  function handleNavChange(newPage){
    clearResult();
    setSelectedResult(null);
    window.location.hash = newPage;
    setPage(newPage);
  }

  // Lanza el análisis y navega a #result mientras el hook useAnalysis procesa la petición
  function handleAnalyze(formData){
    analyze({...formData, lang});
    window.location.hash = 'result';
    setPage("result");
  }

  // Navega al resultado de una noticia ya analizada (desde el historial en Dashboard o en Recientes)
  function handleSelectResult(r){
    setSelectedResult(r);
    window.location.hash = `result/${r.valoracion.noticia_id}`;
    setPage("result");
  }
  
  return(
    <div style={{ minHeight: "100vh", background: G.bg, minWidth: "fit-content" }}>
      <Navbar
        page={page === "result" ? "analyze" : page } 
        setPage={handleNavChange} 
        lang={lang}
        setLang={(l) => {setLang(l); document.documentElement.lang = l; }}
      />
      {page === "result" && (selectedResult || result) ? (
        <ResultPage
          result={selectedResult || result}
          onBack={() => { clearResult(); setSelectedResult(null); window.location.hash = 'analyze'; setPage("analyze"); }}
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
