import { useState, useEffect } from "react";
import { theme as G, fonts } from "../constants/theme";
import { Pill } from "../components/ui"
import { statusMeta, confianzaLabel, formatFecha } from "../utils/formatters";
import { getRecientes } from "../services/api";
import { translation } from "../constants/translations";

function NewsCard({ r, onClick }) {
    const { color, label } = statusMeta(r.valoracion.resultado);
    const conf = confianzaLabel(r.valoracion.probabilidad);
    const [hovered, setHovered] = useState(false);

    return (
        <div onClick={onClick}
            onMouseEnter={() => setHovered(true)}
            onMouseLeave={() => setHovered(false)}
            style={{
                background: G.surface, borderRadius: 14,
                border: `1px solid ${hovered ? G.accent : G.border}`,
                overflow: "hidden", cursor: "pointer",
                transition: "border-color 0.15s, transform 0.15s",
                transform: hovered ? "translateY(-2px)" : "none",
                display: "flex", flexDirection: "column",
            }}
        >
            <div style={{ position: "relative", height: 160, background: G.card, flexShrink: 0 }}>
                {r.noticia.imagen_url ? (
                    <img src={r.noticia.imagen_url} alt=""
                        style={{ width: "100%", height: "100%", objectFit: "cover" }}
                        onError={e => { e.target.style.display = "none"; }} />
                ) : (
                    <div style={{
                        width: "100%", height: "100%", display: "flex", alignItems: "center",
                        justifyContent: "center", fontSize: 32, color: G.border,
                    }}></div>
                )}
                <div style={{
                    position: "absolute", top: 10, left: 10, background: color, borderRadius: 6,
                    padding: "3px 10px", fontFamily: fonts.display, fontWeight: 700, fontSize: 11,
                    color: "#fff", letterSpacing: "0.04em",
                }}>
                    {label}
                </div>
            </div>

            <div style={{ padding: "14px 16px", flex: 1, display: "flex", flexDirection: "column", gap: 8 }}>
                <div style={{
                    fontFamily: fonts.display, fontWeight: 700, fontSize: 14, color: G.text, lineHeight: 1.4,
                    display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden",
                }}>
                    {r.noticia.titulo}
                </div>
                <div style={{ marginTop: "auto", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ color: G.muted, fontSize: 11 }}>
                        {r.fuente_nombre && <span style={{ marginRight: 8 }}>{r.fuente_nombre}</span>}
                        {formatFecha(r.valoracion.fecha_analisis)}
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                        <Pill color={conf.color}>{conf.label}</Pill>
                        <span style={{ fontFamily: fonts.mono, fontSize: 12, fontWeight: 700, color }}>
                            {Math.round(r.valoracion.probabilidad * 100)}%
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function RecentPage({ onSelect, lang }) {
    const t = translation[lang].recientes;
    const [noticias, setNoticias] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filtroLang, setFiltroLang] = useState(null);

    function cargar(l = filtroLang) {
        setLoading(true);
        getRecientes(20, l).then(data => { setNoticias(data); setError(null); })
            .catch(() => setError(t.error)).finally(() => setLoading(false));
    }

    useEffect(() => { cargar(); }, []);

    if (loading) return (
        <div style={{ textAlign: "center", padding: "80px 24px", color: G.textSub }}>
            {t.loading}
        </div>
    );

    return (
        <div style={{ maxWidth: 1100, margin: "0 auto", padding: "40px 24px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 28 }}>
                <div>
                    <h1 style={{
                        fontFamily: fonts.display, fontSize: 28, fontWeight: 800,
                        letterSpacing: "-0.03em", marginBottom: 6,
                    }}>
                        {t.title}
                    </h1>
                    <p style={{ color: G.textSub }}>
                        {t.subtitle}
                    </p>
                </div>
                <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <div style={{ display: "flex", gap: 6 }}>
                        {[
                            { v: null, label: "Todos" },
                            { v: "es", label: "ES" },
                            { v: "en", label: "EN" },
                        ].map(({ v, label}) => (
                            <button key={label} onClick={() => { setFiltroLang(v); cargar(v); }} style={{
                                padding: "6px 14px", borderRadius: 6, cursor: "pointer", fontFamily: fonts.mono,
                                fontSize: 12, fontWeight: 600, border: `1px solid ${filtroLang === v ? G.accent: G.border}`,
                                background: filtroLang === v ? G.accentLo: "transparent", color: filtroLang === v ? G.accent: G.textSub,
                            }}>
                                {label}
                            </button>
                        ))}
                    </div>
                    <button onClick={() => cargar()} style={{
                        background: G.accentLo, border: `1px solid ${G.accent}44`,
                        borderRadius: 8, padding: "8px 16px", cursor: "pointer",
                        fontFamily: fonts.body, fontSize: 13, color: G.accent,
                    }}>
                        {t.refresh}
                    </button>
                </div>
            </div>

            {error && <div style={{ color: G.danger, fontSize: 13, marginBottom: 16 }}>{error}</div>}

            {noticias.length === 0 ? (
                <div style={{ textAlign: "center", padding: "80px 24px", color: G.textSub }}>
                    <div style={{ fontFamily: fonts.display, fontWeight: 700, marginBottom: 6 }}>{t.empty}</div>
                    <div style={{ fontSize: 13 }}>{t.emptySubtitle}</div>
                </div>
            ) : (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 20, }}>
                    {noticias.map((r, i) => (
                        <NewsCard key={i} r={r} onClick={() => onSelect(r)} />
                    ))}
                </div>
            )}
        </div>
    );
}