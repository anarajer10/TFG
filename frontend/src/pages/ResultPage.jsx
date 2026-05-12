import { theme as G, fonts } from "../constants/theme";
import { Card, Pill, Button, SectionTitle } from "../components/ui";
import { MetricBar, ScoreDial } from "../components/shared";
import { clamp, imagenMeta, sentimientoLabel, confianzaLabel, formatFecha } from "../utils/formatters";

export default function ResultPage({ result, onBack }) {
    const { valoracion, noticia, fuente_nombre } = result;

    const vMeta = (() => {
        const m = {
            falsa: { label: "NOTICIA FALSA", color: G.danger, bg: G.dangerLo, icon: "✕" },
            verdadera: { label: "NOTICIA VERDADERA", color: G.ok, bg: G.okLo, icon: "✓" },
            pendiente: { label: "INDETERMINADO", color: G.warn, bg: G.warnLo, icon: "?" },
        };
        return m[valoracion.resultado] ?? m.pendiente;
    })();

    const conf = confianzaLabel(valoracion.probabilidad);
    const imgM = imagenMeta(valoracion.estatus_analisis_imagen);

    // normlaización a [0,1] de punt_sentimiento
    const sentNorm = clamp((parseFloat(valoracion.punt_sentimiento) + 1) / 2, 0, 1);
    const objScore = clamp(1 - parseFloat(valoracion.punt_objetividad ?? 0), 0, 1);

    return (
        <div style={{ maxWidth: 820, margin: "0 auto", padding: "36px 24px" }}>
            {/*Veredicto*/}
            <div style={{
                background: vMeta.bg, border: `1px solid ${vMeta.color}44`,
                borderRadius: 16, padding: "24px 28px",
                display: "flex", alignItems: "center", gap: 20,
                marginBottom: 24,
            }}>
                <div style={{
                    width: 52, height: 52, borderRadius: "50%",
                    background: vMeta.color + "33", border: `2px solid ${vMeta.color}`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 22, color: vMeta.color, fontFamily: fonts.display, fontWeight: 700,
                    flexShrink: 0,
                }}>
                    {vMeta.icon}
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{
                        fontFamily: fonts.display, fontSize: 20, fontWeight: 800,
                        color: vMeta.color, letterSpacing: "-0.02em",
                    }}>
                        {vMeta.label}
                    </div>
                    <div style={{
                        color: G.textSub, fontSize: 13, marginTop: 2,
                        overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                    }}>
                        {noticia.titulo}
                    </div>
                    <div style={{ marginTop: 6, display: "flex", gap: 8 }}>
                        <span style={{ fontSize: 11, color: conf.color, fontFamily: fonts.mono }}>
                            Confianza {conf.label}
                        </span>
                        <span style={{ fontSize: 11, color: G.muted }}>.</span>
                        <span style={{ fontSize: 11, color: G.muted }}>{formatFecha(valoracion.fecha_analisis)}</span>
                    </div>
                </div>

                <div style={{ textAlign: "right", flexShrink: 0 }}>
                    <div style={{ fontFamily: fonts.mono, fontSize: 40, fontWeight: 700, color: vMeta.color }}>
                        {Math.round(valoracion.probabilidad * 100)}
                    </div>
                    <div style={{ color: G.textSub, fontSize: 11 }}>
                        % probabilidad falsa
                    </div>
                </div>
            </div>

            {/*Grid del análisis texto e imagen*/}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
                {/*Análisis de texto*/}
                <Card>
                    <SectionTitle>Análisis de texto</SectionTitle>

                    <div style={{ display: "flex", justifyContent: "space-around", marginBottom: 16 }}>
                        <ScoreDial value={sentNorm} label="Sentimiento" />
                        <ScoreDial value={objScore} label="Subjetividad" />
                    </div>

                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                        {valoracion.punt_sentimiento !== null && (
                            <Pill color={G.accent}>
                                {parseFloat(valoracion.punt_sentimiento) > 0.1 ? "Positivo"
                                    : parseFloat(valoracion.punt_sentimiento) < -0.1 ? "Negativo"
                                        : "Neutro"}
                            </Pill>
                        )}
                        {valoracion.punt_objetividad !== null && (
                            <Pill color={parseFloat(valoracion.punt_objetividad) < 0.5 ? G.warn : G.ok}>
                                Objetividad {Math.round(parseFloat(valoracion.punt_objetividad) * 100)}%
                            </Pill>
                        )}
                    </div>
                </Card>

                {/*Análisis de imagen*/}
                <Card>
                    <SectionTitle>Análisis de imagen</SectionTitle>

                    <div style={{ marginBottom: 14 }}>
                        <Pill color={imgM.color}>{imgM.icon} {imgM.label}</Pill>
                    </div>

                    {/*Barra de probabilidad falsa*/}
                    <MetricBar
                        label="Riesgo general"
                        value={valoracion.probabilidad}
                        color={vMeta.color}
                    />

                    {valoracion.estatus_analisis_imagen === "fuera_contexto" && (
                        <div style={{
                            marginTop: 10, padding: "8px 10px",
                            background: G.warnLo, borderRadius: 6,
                            fontSize: 12, color: G.warn,
                        }}>
                            Imagen posiblemente fuera de contexto
                        </div>
                    )}

                    {valoracion.estatus_analisis_imagen === "generada_ia" && (
                        <div style={{
                            marginTop: 10, padding: "8px 10px",
                            background: G.warnLo, borderRadius: 6,
                            fontSize: 12, color: G.warn,
                        }}>
                            Imagen clasificada como generada con IA
                        </div>
                    )}

                    {noticia.imagen_url && (
                        <img
                            src={noticia.imagen_url}
                            alt="Imagen de la noticia"
                            style={{
                                width: "100%", marginTop: 12, borderRadius: 8,
                                border: `1px solid ${G.border}`, objectFit: "cover", maxHeight: 120,
                            }}
                            onError={e => { e.target.style.display = "none"; }}
                        />
                    )}
                </Card>
            </div>

            {/*Explicación XAI*/}
            {valoracion.explicacion && (
                <Card style={{ marginBottom: 16 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                        <SectionTitle>Explicación XAI</SectionTitle>
                        <Pill color={G.accent}>Llama 3.2</Pill>
                    </div>
                    <p style={{ color: G.textSub, fontSize: 13, lineHeight: 1.75 }}>
                        {valoracion.explicacion}
                    </p>
                </Card>
            )}

            {/*Metadatos de la noticia*/}
            <Card style={{ marginBottom: 24 }}>
                <SectionTitle>Datos de la noticia</SectionTitle>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                    {[
                        { k: "Fuente", v: fuente_nombre || "-"},
                        { k: "Categoría", v: noticia.categoria || "-" },
                        { k: "URL", v: noticia.texto_url || "-" },
                        { k: "Fecha publicación", v: formatFecha(noticia.fecha_publi) },
                        { k: "id análisis", v: `#${valoracion.id}` },
                    ].map(({ k, v }) => (
                        <div key={k} style={{ padding: "8px 0", borderBottom: `1px solid ${G.border}`, minWidth: 0 }}>
                            <div style={{ color: G.muted, fontSize: 11, textTransform: "uppercase", letterSpacing: "0.05em" }}>{k}</div>
                            <div style={{
                                fontFamily: fonts.mono, fontSize: 12, marginTop: 2,
                                overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                            }}>{v}</div>
                        </div>
                    ))}
                </div>
            </Card>

            <Button variant="ghost" onClick={onBack}>Nuevo análisis</Button>
        </div>
    );
}