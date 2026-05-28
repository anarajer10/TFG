import { theme as G, fonts } from "../constants/theme";
import { Card, Pill, Button, SectionTitle } from "../components/ui";
import { MetricBar, ScoreDial } from "../components/shared";
import { clamp, imagenMeta, sentimientoLabel, confianzaLabel, formatFecha } from "../utils/formatters";
import { translation } from "../constants/i18n";

export default function ResultPage({ result, onBack, lang }) {
    const { valoracion, noticia, fuente_nombre } = result;
    const t = translation[lang].result;

    const vMeta = (() => {
        const m = {
            falsa: { label: t.falsa, color: G.danger, bg: G.dangerLo, icon: "✕" },
            verdadera: { label: t.verdadera, color: G.ok, bg: G.okLo, icon: "✓" },
            pendiente: { label: t.pendiente, color: G.warn, bg: G.warnLo, icon: "?" },
        };
        const prob = parseFloat(valoracion.probabilidad);
        if (prob >= 0.4 && prob <= 0.6) return m.pendiente;
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
                            {t.confianza} {conf.label}
                        </span>
                        <span style={{ fontSize: 11, color: G.muted }}>.</span>
                        <span style={{ fontSize: 11, color: G.muted }}>{formatFecha(valoracion.fecha_analisis)}</span>
                    </div>
                </div>

                <div style={{ textAlign: "right", flexShrink: 0 }}>
                    <div style={{ fontFamily: fonts.mono, fontSize: 52, fontWeight: 700, color: vMeta.color }}>
                        {Math.round(valoracion.probabilidad * 100)}
                    </div>
                    <div style={{ color: G.textSub, fontSize: 11 }}>
                        {t.probFalsa}
                    </div>
                </div>
            </div>

            {/*Grid del análisis texto e imagen*/}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
                {/*Análisis de texto*/}
                <Card>
                    <SectionTitle>{t.textoTitle}</SectionTitle>

                    <div style={{ display: "flex", justifyContent: "space-around", marginBottom: 16 }}>
                        <ScoreDial value={sentNorm} label={t.sentimiento} />
                        <ScoreDial value={objScore} label={t.subjetividad} />
                    </div>

                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                        {valoracion.punt_sentimiento !== null && (
                            <Pill color={G.accent}>
                                {parseFloat(valoracion.punt_sentimiento) > 0.1 ? t.positivo
                                    : parseFloat(valoracion.punt_sentimiento) < -0.1 ? t.negativo
                                        : t.neutro}
                            </Pill>
                        )}
                        {valoracion.punt_objetividad !== null && (
                            <Pill color={parseFloat(valoracion.punt_objetividad) < 0.5 ? G.warn : G.ok}>
                                {t.objetividad} {Math.round(parseFloat(valoracion.punt_objetividad) * 100)}%
                            </Pill>
                        )}
                    </div>
                </Card>

                {/*Análisis de imagen*/}
                <Card>
                    <SectionTitle>{t.imagenTitle}</SectionTitle>

                    <div style={{ marginBottom: 14 }}>
                        <Pill color={imgM.color}>{imgM.icon} {imgM.label}</Pill>
                    </div>

                    {/*Barra de probabilidad falsa*/}
                    <MetricBar
                        label={t.riesgo}
                        value={valoracion.probabilidad}
                        color={vMeta.color}
                    />

                    {valoracion.estatus_analisis_imagen === "fuera_contexto" && (
                        <div style={{
                            marginTop: 10, padding: "8px 10px",
                            background: G.warnLo, borderRadius: 6,
                            fontSize: 12, color: G.warn,
                        }}>
                            {t.fueraContexto}
                        </div>
                    )}

                    {valoracion.estatus_analisis_imagen === "generada_ia" && (
                        <div style={{
                            marginTop: 10, padding: "8px 10px",
                            background: G.warnLo, borderRadius: 6,
                            fontSize: 12, color: G.warn,
                        }}>
                            {t.generadaIA}
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

            {/*Explicación automática*/}
            {valoracion.explicacion && (
                <Card style={{ marginBottom: 16 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                        <SectionTitle>{t.xaiTitle}</SectionTitle>
                        <Pill color={G.accent}>Llama 3.2</Pill>
                    </div>
                    {(() => {
                        const parts = valoracion.explicacion.split(/\*\*(.*?)\*\*/);
                        const sections = [];
                        for(let i = 1; i < parts.length; i += 2){
                            const title = parts[i].trim();
                            const body = (parts[i+1] || "").trim();
                            if (title) sections.push({title, body});
                        }
                        return sections.length > 0 ? (
                            <div>
                                {sections.map(({title, body}, i) => (
                                    <div key={i} style={{
                                        padding: "12px 0", borderBottom: i < sections.length - 1 ? `1px solid ${G.border}` : "none",
                                    }}>
                                        <div style={{ fontFamily: fonts.display, fontWeight: 700, fontSize: 11,
                                            color: G.accent, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 6,
                                        }}>
                                            {title}
                                        </div>
                                        <p style={{ color: G.textSub, fontSize: 13, lineHeight: 1.65, margin: 0}}>
                                            {body}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <p style={{ color: G.textSub, fontSize: 13, lineHeight: 1.75, margin: 0}}>
                                {valoracion.explicacion}
                            </p>
                        );
                    })()}
                    
                </Card>
            )}

            {/*Metadatos de la noticia*/}
            <Card style={{ marginBottom: 24 }}>
                <SectionTitle>{t.datosTitle}</SectionTitle>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                    {[
                        { k: t.fuente, v: fuente_nombre || "-" },
                        { k: t.categoria, v: noticia.categoria || "-" },
                        { k: t.url, v: noticia.texto_url || "-" },
                        { k: t.fechaPubli, v: formatFecha(noticia.fecha_publi) },
                        { k: t.idAnalisis, v: `#${valoracion.id}` },
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

            <Button onClick={onBack}>{t.newAnalisis}</Button>
        </div>
    );
}