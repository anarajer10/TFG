import { theme as G, fonts } from "../constants/theme";
import { Card, Pill, SectionTitle } from "../components/ui";
import { MetricBar } from "../components/shared";
import { statusMeta, imagenMeta, confianzaLabel, formatFecha } from "../utils/formatters";

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

export default function DashboardPage({ history }){
    const total = history.length;
    const falsas = history.filter(r => r.valoracion.resultado === "falsa").length;
    const verdaderas = history.filter(r => r.valoracion.resultado === "verdadera").length;
    const avgProb = total>0 ? history.reduce((s, r) => s+(r.valoracion.probabilidad ?? 0), 0)/total : 0;
    const confianzas = { Alta: 0, Media: 0, Baja: 0 };
    history.forEach(r => {
        const c = confianzaLabel(r.valoracion.probabilidad).label;
        confianzas[c]++;
    });

    return(
        <div style={{ maxWidth: 900, margin: "0 auto", padding: "40px 24px" }}>
            <div style={{ marginBottom: 28 }}>
                <h1 style={{
                    fontFamily: fonts.display, fontSize: 28, fontWeight: 800,
                    letterSpacing: "-0.03em", marginBottom: 6,
                }}>
                    Dashboard
                </h1>
                <p style={{ color: G.textSub }}>Métricas agregadas de los análisis de la sesión actual</p>
            </div>

            {total === 0 ? (
                <Card style={{ textAlign: "center", padding: "60px 24px" }}>
                    <div style={{ fontSize: 40, marginBottom: 12 }}></div>
                    <div style={{ fontFamily: fonts.display, fontWeight: 700, marginBottom: 6 }}>
                        Sin análisis aún
                    </div>
                    <div style={{ color: G.textSub, fontSize: 13 }}>
                        Analiza una noticia para ver las métricas aquí
                    </div>
                </Card>
            ):(
                <>
                    {/*Estadísticas principales*/}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 24 }}>
                        <StatCard label="Analizadas" value={total} color={G.accent} />
                        <StatCard label="Falsas" value={falsas} color={G.danger}
                            sub={`${Math.round(falsas/total*100)}% del total`} />
                        <StatCard label="Verdaderas" value={verdaderas} color={G.ok}
                            sub={`${Math.round(verdaderas/total*100)}% del total`} />
                        <StatCard label="Probabilidad media" value={`${Math.round(avgProb*100)}%`}
                            color={avgProb >= 0.5 ? G.danger: G.ok} />
                    </div>

                    {/*Distribuciones*/}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
                        <Card>
                            <SectionTitle>Distribución de resultados</SectionTitle>
                            <MetricBar label="Falsas" value={total ? falsas / total : 0} color={G.danger} />
                            <MetricBar label="Verdaderas" value={total ? verdaderas / total : 0} color={G.ok} />
                            <MetricBar label="Pendiente" value={total ? (total - falsas - verdaderas) / total : 0} color={G.warn} />
                        </Card>

                        <Card>
                            <SectionTitle>Nivel de confianza</SectionTitle>
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
                        <SectionTitle>Estado del análisis de la imagen de la noticia</SectionTitle>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
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
                        <SectionTitle>Historial de análisis</SectionTitle>
                        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                            {history.map((r, i) => {
                                const { label, color } = statusMeta(r.valoracion.resultado);
                                const conf = confianzaLabel(r.valoracion.probabilidad);
                                return(
                                    <div key={i} style={{
                                        display: "flex", alignItems: "center", gap: 12,
                                        padding: "10px 12px", borderRadius: 8,
                                        background: G.surface, border: `1px solid ${G.border}`,
                                    }}>
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