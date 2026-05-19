import { useState, useEffect } from "react";
import { theme as G, fonts } from "../constants/theme";
import { Card, Pill, SectionTitle } from "../components/ui";
import { MetricBar } from "../components/shared";
import { statusMeta, imagenMeta, confianzaLabel, formatFecha } from "../utils/formatters";
import { getMetricas } from "../services/api";
import { translation } from "../constants/translations";

function DonutRing({ value, color, label }){
    const r = 30, c = 2*Math.PI*r;
    const dash = Math.min(value, 1)*c;
    return(
        <div style={{ textAlign: "center" }}>
            <svg width={80} viewBox="0 0 80 80">
                <circle cx="40" cy="40" r={r} fill="none" stroke={G.border} strokeWidth="8" />
                <circle cx="40" cy="40" r={r} fill="none" stroke={color} strokeWidth="8" 
                    strokeDasharray={`${dash} ${c}`} strokeLinecap="round" transform="rotate(-90 40 40)" />
                <text x="40" y="45" textAnchor="middle" fontSize="15" fontWeight="700" fill={color} fontFamily="monospace">
                    {Math.round(value*100)}%
                </text>
            </svg>
            <div style={{ fontSize: 11, color: G.textSub, marginTop: 4 }}>{label}</div>
        </div>
    );
}

function StatCard({ label, value, color, sub }) {
    return(
        <Card style={{ textAlign: "center" }}>
            <div style={{
                fontFamily: fonts.mono, fontSize: 36, fontWeight: 700,
                color, marginBottom: 4,
            }}>
                {value}
            </div>
            <div style={{ fontFamily: fonts.display, fontSize: 13, fontWeight: 600, marginBottom: 2}}>
                {label}
            </div>
            {sub && <div style={{ color: G.textSub, fontSize: 11 }}>{sub}</div>}
        </Card>
    );
}

export default function DashboardPage({ history, onSelect, lang }){
    const total = history.length;
    const falsas = history.filter(r => r.valoracion.resultado === "falsa").length;
    const verdaderas = history.filter(r => r.valoracion.resultado === "verdadera").length;
    const avgProb = total>0 ? history.reduce((s, r) => s+(r.valoracion.probabilidad ?? 0), 0)/total : 0;
    const confianzas = { Alta: 0, Media: 0, Baja: 0 };
    history.forEach(r => {
        const c = confianzaLabel(r.valoracion.probabilidad).label;
        confianzas[c]++;
    });
    const [metricas, setMetricas] = useState(null);
    useEffect(() => {
        getMetricas().then(setMetricas).catch(() => {});
    }, []);
    const t = translation[lang].dashboard;

    return(
        <div style={{ maxWidth: 1200, margin: "0 auto", padding: "40px 24px" }}>
            <div style={{ marginBottom: 28 }}>
                <h1 style={{
                    fontFamily: fonts.display, fontSize: 28, fontWeight: 800,
                    letterSpacing: "-0.03em", marginBottom: 6,
                }}>
                    {t.title}
                </h1>
                <p style={{ color: G.textSub }}>{t.subtitle}</p>
            </div>

            {metricas && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 24 }}>
                    {[
                        { lang: "es", titulo: t.modeloES },
                        { lang: "en", titulo: t.modeloEN },
                    ].map(({ lang, titulo }) => {
                        const m = metricas[lang];
                        if (!m) return null;
                        return (
                            <Card key={lang}>
                                <div style={{ marginBottom: 12 }}>
                                    <div style={{ fontFamily: fonts.display, fontWeight: 700, fontSize: 13, marginBottom: 2 }}>
                                        {titulo} - {m.modelo}
                                    </div>
                                    <div style={{ color: G.textSub, fontSize: 11 }}>
                                        {m.total_muestras.toLocaleString()} {t.muestras} · F1 cv: {(m.cv_f1_media*100).toFixed(1)}% ± {(m.cv_f1_std*100).toFixed(1)}%
                                    </div>
                                </div>
                                <MetricBar label="Accuracy" value={m.accuracy} color={G.accent} />
                                <MetricBar label="F1 - Noticias falsas" value={m.f1_falsa} color={G.danger} />
                                <MetricBar label="F1 - Noticias verdaderas" value={m.f1_real} color={G.ok} />
                                <MetricBar label="ROC-AUC" value={m.roc_auc} color={G.warn} />
                            </Card>
                        );
                    })}
                </div>
            )}

            {total === 0 ? (
                <Card style={{ textAlign: "center", padding: "60px 24px" }}>
                    <div style={{ fontSize: 40, marginBottom: 12 }}></div>
                    <div style={{ fontFamily: fonts.display, fontWeight: 700, marginBottom: 6 }}>
                        {t.empty}
                    </div>
                    <div style={{ color: G.textSub, fontSize: 13 }}>
                        {t.emptySubtitle}
                    </div>
                </Card>
            ):(
                <>
                    {/*Estadísticas principales*/}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 24 }}>
                        <StatCard label={t.analizadas} value={total} color={G.accent} />
                        <StatCard label={t.falsas} value={falsas} color={G.danger}
                            sub={`${Math.round(falsas/total*100)}% del total`} />
                        <StatCard label={t.verdaderas} value={verdaderas} color={G.ok}
                            sub={`${Math.round(verdaderas/total*100)}% del total`} />
                        <StatCard label={t.probMedia} value={`${Math.round(avgProb*100)}%`}
                            color={avgProb >= 0.5 ? G.danger: G.ok} />
                    </div>

                    {/*Distribuciones*/}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
                        <Card>
                            <SectionTitle>{t.distResultados}</SectionTitle>
                            <div style={{ display: "flex", justifyContent: "space-around", padding: "16px 0" }}>
                                <DonutRing label={t.falsas} value={total ? falsas / total : 0} color={G.danger} />
                                <DonutRing label={t.verdaderas} value={total ? verdaderas / total : 0} color={G.ok} />
                                <DonutRing label={t.pendiente} value={total ? (total - falsas - verdaderas) / total : 0} color={G.warn} />
                            </div>
                        </Card>

                        <Card>
                            <SectionTitle>{t.nivelConfianza}</SectionTitle>
                            {Object.entries(confianzas).map(([lbl, cnt]) => {
                                const cols = { Alta: G.ok, Media: G.warn, Baja: G.danger };
                                return(
                                    <MetricBar
                                        key={lbl}
                                        label={lbl}
                                        value={total ? cnt / total : 0}
                                        color={cols[lbl]}
                                    />
                                );
                            })}
                        </Card>
                    </div>

                    {/*Estado imágenes*/}
                    <Card style={{ marginBottom: 16 }}>
                        <SectionTitle>{t.estadoImagen}</SectionTitle>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
                            {["autentica", "fuera_contexto", "generada_ia", "pendiente"].map(st => {
                                const cnt = history.filter(r => r.valoracion.estatus_analisis_imagen === st).length;
                                const meta = imagenMeta(st);
                                return(
                                    <div key={st} style={{
                                        padding: "12px", borderRadius: 8,
                                        background: G.surface, border: `1px solid ${G.border}`,
                                        textAlign: "center",
                                    }}>
                                        <div style={{ fontFamily: fonts.mono, fontSize: 24, color: meta.color, marginBottom: 4 }}>
                                            {cnt}
                                        </div>
                                        <div style={{ fontSize: 11, color: G.textSub }}>{meta.label}</div>
                                    </div>
                                );
                            })}
                        </div>
                    </Card>

                    {/*Historial*/}
                    <Card>
                        <SectionTitle>{t.historial}</SectionTitle>
                        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                            {history.map((r, i) => {
                                const { label, color } = statusMeta(r.valoracion.resultado);
                                const conf = confianzaLabel(r.valoracion.probabilidad);
                                return(
                                    <div key={i} onClick={() => onSelect(r)} style={{
                                        display: "flex", alignItems: "center", gap: 12,
                                        padding: "10px 12px", borderRadius: 8,
                                        background: G.surface, border: `1px solid ${G.border}`,
                                        cursor: "pointer", transition: "border-color 0.15s",
                                    }}
                                    onMouseEnter={e => e.currentTarget.style.borderColor = G.accent}
                                    onMouseLeave={e => e.currentTarget.style.borderColor = G.border}
                                    >
                                        <div style={{
                                            width: 8, height: 8, borderRadius: "50%",
                                            background: color, flexShrink: 0,
                                        }} />
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <div style={{
                                                fontSize: 13, fontWeight: 500,
                                                overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                                            }}>
                                                {r.noticia.titulo}
                                            </div>
                                            <div style={{ color: G.muted, fontSize: 11 }}>
                                                {formatFecha(r.valoracion.fecha_analisis)}
                                                {r.noticia.categoria && `· ${r.noticia.categoria}`}
                                            </div>
                                        </div>
                                        <Pill color={conf.color}>{conf.label}</Pill>
                                        <Pill color={color}>{label}</Pill>
                                        <span style={{
                                            fontFamily: fonts.mono, color, fontSize: 13,
                                            minWidth: 40, textAlign: "right",
                                        }}>
                                            {Math.round(r.valoracion.probabilidad*100)}%
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    </Card>
                </>
            )}
        </div>
    );

}