import { fonts, theme as G } from "../../constants/theme";
import { clamp, confianzaLabel, scoreColor } from "../../utils/formatters";

// Navbar
export function Navbar({ page, setPage }){
    return(
        <nav style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "0 32px", height: 56,
            background: G.surface,
            borderBottom: `1px solid ${G.border}`,
            position: "sticky", top: 0, zIndex: 100,
        }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{
                    width: 28, height: 28, borderRadius: 6,
                    background: G.accent,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontFamily: fonts.display, fontWeight: 800, fontSize: 13, color: "#fff",
                }}>Detector de fake news</div>
                <span style={{ fontFamily: fonts.display, fontWeight: 700, fontSize: 15, letterSpacing: "-0.02em" }}>
                    Fake news detector
                </span>
            </div>

            <div style={{ display: "flex", gap: 4 }}>
                {[
                    { id: "analyze", label: "Analizar" },
                    { id: "dashboard", label: "Dashboard" },
                ].map(({ id, label }) => (
                    <button key={id} onClick={() => setPage(id)} style={{
                        padding: "6px 16px", borderRadius: 8, border: "none", cursor: "pointer",
                        fontFamily: fonts.body, fontSize: 13, fontWeight: 500,
                        background: page === id ? G.accentLo: "transparent",
                        color: page === id ? G.accent: "textSub",
                        transition: "all 0.15s",
                    }}>
                        {label}
                    </button>
                ))}
            </div>
        </nav>
    );
}

// MetricBar
export function MetricBar({ label, value, color, showPct = true }){
    const pct = clamp(value, 0, 1)*100;
    return(
        <div style={{ marginBottom: 10 }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ color: G.textSub, fontSize: 12 }}>{label}</span>
                {showPct && (
                    <span style={{ color, fontSize: 12, fontFamily: fonts.mono }}>
                        {pct.toFixed(0)}%
                    </span>
                )}
            </div>
            <div style={{ background: G.border, borderRadius: 99, height: 5, overflow: "hidden" }}>
                <div style={{
                    height: "100%", borderRadius: 99,
                    background: color,
                    width: `${pct}%`,
                    transition: "width 0.8s cubic-bezier(.4,0,.2,1)",
                }} />
            </div>
        </div>
    );
}

// ScoreDial
export function ScoreDial({ value, label }){
    const c = scoreColor(value);
    const r = 36, cx = 44, cy = 44;
    const circ = 2*Math.PI*r;
    const dash = clamp(value, 0, 1)*circ;

    return(
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
            <svg width={88} height={88}>
                <circle cx={cx} cy={cy} r={r} fill="none" stroke={G.border} strokeWidth={6} />
                <circle
                    cx={cx} cy={cy} r={r} fill="none" stroke={c} strokeWidth={6}
                    strokeDasharray={`${dash} ${circ}`}
                    strokeLinecap="round"
                    transform={`rotate(-90 ${cx} ${cy})`}
                    style={{ transition: "stroke-dasharray 0.9s cubic-bezier(.4,0,.2,1)" }}
                />
                <text x={cx} y={cy+5} textAnchor="middle"
                    fill={c} fontSize={16} fontWeight={700} fontFamily={fonts.mono}>
                        {Math.round(value*100)}
                </text>
            </svg>
            <span style={{ color: G.textSub, fontSize: 11, textAlign: "center" }}>{label}</span>
        </div>
    );
}

// Header del veredicto (una barra superior con el resultado)
export function VeredictoHeader({ valoracion, titulo }){
    const metaMap = {
        falsa: {label: "NOTICIA FALSA", color: G.danger, bg: G.dangerLo, icon: "✕"},
        verdadera: {label: "NOTICIA VERDADERA", color: G.ok, bg: G.okLo, icon: "✓"},
        pendiente: {label: "INDETERMINADO", color: G.warn, bg: G.warnLo, icon: "?"},
    };
    const meta = metaMap[valoracion.resultado] ?? metaMap.pendiente;
    const conf = confianzaLabel(valoracion.probabilidad);

    return(
        <div style={{
            background: meta.bg,
            border: `1px solid ${meta.color}44`,
            borderRadius: 16, padding: "24px 28px",
            display: "flex", alignItems: "center", gap: 20,
            marginBottom: 24,
        }}>
            <div style={{
                width: 52, height: 52, borderRadius: "50%",
                background: meta.color+"33", border: `2px solid ${meta.color}`,
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 22, color: meta.color, fontWeight: 700,
                fontFamily: fonts.display, flexShrink: 0,
            }}>
                {meta.icon}
            </div>

            <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                    fontFamily: fonts.display, fontSize: 20, fontWeight: 800,
                    color: meta.color, letterSpacing: "-0.02em",
                }}>
                    {meta.label}
                </div>
                <div style={{ 
                    color: G.textSub, fontSize: 13, marginTop: 2,
                    overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" 
                }}>
                    {titulo}
                </div>
                <div style={{ marginTop: 6 }}>
                    <span style={{ fontSize: 11, color: conf.color, fontFamily: fonts.mono }}>
                        Confianza {conf.label}
                    </span>
                </div>
            </div>

            <div style={{ textAlign: "right", flexShrink: 0 }}>
                <div style={{
                    fontFamily: fonts.mono, fontSize: 36, fontWeight: 700, color: meta.color,
                }}>
                    {Math.round(valoracion.probabilidad*100)}
                </div>
                <div style={{ color: G.textSub, fontSize: 11 }}>% probabilidad falsa</div>
            </div>
        </div>
    );
}