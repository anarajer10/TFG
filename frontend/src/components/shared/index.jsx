import { fonts, theme as G } from "../../constants/theme";
import { clamp, confianzaLabel, scoreColor } from "../../utils/formatters";
import { translation } from "../../constants/i18n";
import HootLogo from '../../assets/hoot_logo.svg?react'

// Navbar
export function Navbar({ page, setPage, lang, setLang }){
    return(
        <nav style={{
            display: "flex", alignItems: "center", justifyContent: "space-between",
            padding: "0 32px", height: 56,
            background: G.surface,
            borderBottom: `1px solid ${G.border}`,
            position: "sticky", top: 0, zIndex: 100,
        }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, cursor: "pointer" }}
                onClick={() => setPage("home")}>
                <HootLogo width={34} height={34} />
                <span style={{
                    fontFamily: fonts.display, fontWeight: 800, fontSize: 18,
                    letterSpacing: "-0.02em", color: G.text,
                }}>
                    HOOT
                </span>
            </div>

            <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                {[
                    { id: "home", label: translation[lang].nav.home },
                    { id: "analyze", label: translation[lang].nav.analyze },
                    { id: "dashboard", label: translation[lang].nav.dashboard },
                    { id: "recientes", label: translation[lang].nav.recientes },
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
                <div style={{ width: 1, height: 20, background: G.border, margin: "0 8px" }} />
                {["es", "en"].map(l => (
                    <button key={l} onClick={() => setLang(l)} style={{
                        padding: "4px 10px", borderRadius: 6, border: `1px solid ${lang === l ? G.accent: G.border}`,
                        cursor: "pointer", fontFamily: fonts.mono, fontSize: 12, fontWeight: 600,
                        background: lang === l ? G.accentLo: "transparent",
                        color: lang === l ? G.accent: G.textSub,
                        transition: "all 0.15s"
                    }}>
                        {l.toUpperCase()}
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
