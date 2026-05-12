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
                        color: page === id ? G.accent: G.textSub,
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

