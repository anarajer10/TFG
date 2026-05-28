import { useState } from "react";
import { theme as G, fonts } from "../constants/theme";
import { Input, Button, Spinner } from "../components/ui";
import { extraerNoticia } from "../services/api";
import ComicHoot from "../assets/comicHoot.svg?react";
import ComicHoot2 from "../assets/comicHoot2.svg?react";
import { translation } from "../constants/i18n";

export default function AnalyzePage({ onAnalyze, loading, error, lang }) {
    const [form, setForm] = useState({
        texto_url: "",
        titulo: "",
        descripcion: "",
        imagen_url: "",
        categoria: "",
        fecha_publi: "",
        fuente_nombre: "",
    });
    const t = translation[lang].analyze;
    const [errors, setErrors] = useState({});
    const [extraiendo, setExtraiendo] = useState(false);
    const [errorExtraccion, setErrorExtraccion] = useState(null);

    function set(field) {
        return (value) => setForm(prev => ({ ...prev, [field]: value }));
    }

    function validate() {
        const e = {};
        if (!form.titulo.trim()) e.titulo = t.errorTitulo;
        else if (form.titulo.trim().length < 10) e.titulo = t.errorTituloMin;

        if (!form.descripcion.trim()) e.descripcion = t.errorDescripcion;
        else if (form.descripcion.trim().length < 50) e.descripcion = t.errorDescripcionMin;

        setErrors(e);
        return Object.keys(e).length === 0;
    }

    async function handleExtraer() {
        if (!form.texto_url.trim()) return;
        setExtraiendo(true);
        setErrorExtraccion(null);
        try {
            const datos = await extraerNoticia(form.texto_url);
            setForm(prev => ({
                ...prev,
                titulo: datos.titulo || prev.titulo,
                descripcion: datos.descripcion || prev.descripcion,
                imagen_url: datos.imagen_url || prev.imagen_url,
                fecha_publi: datos.fecha_publi ? datos.fecha_publi.slice(0, 16) : prev.fecha_publi,
                fuente_nombre: datos.fuente_nombre || prev.fuente_nombre,
            }));
        } catch (err) {
            console.error("Error en la extración de los datos", err)
            setErrorExtraccion(t.extractError);
        } finally {
            setExtraiendo(false);
        }
    }

    function handleSubmit() {
        if (!validate()) return;
        onAnalyze(form);
    }

    return (
        <div style={{ maxWidth: 760, margin: "0 auto", padding: "40px 24px", position: "relative" }}>
            {loading && (
                <div style={{
                    position: "fixed", bottom: 32, right: 32, background: G.surface, border: `1px solid ${G.accent}66`,
                    borderRadius: 14, padding: "18px 24px", display: "flex", alignItems: "center", gap: 14,
                    boxShadow: "0 9px 32px rgba(238, 154, 255, 0.4)", zIndex: 100, minWidth: 220,
                }}>
                    <Spinner size={22} />
                    <div>
                        <p style={{ fontFamily: fonts.display, fontWeight: 700, fontSize: 14, color: G.text }}>
                            {t.analyzing}
                        </p>
                        <p style={{ color: G.textSub, fontSize: 12 }}>
                            {t.analyzingSubtitle}
                        </p>
                    </div>
                </div>
            )}
            <div style={{ position: "fixed", left: "calc(50% - 430px)", top: "15%", width: 2, height: "60vh", background: `linear-gradient(to bottom, transparent, ${G.accent}44, transparent)`, pointerEvents: "none" }} />
            <div style={{ position: "fixed", right: "calc(50% - 430px)", top: "15%", width: 2, height: "60vh", background: `linear-gradient(to bottom, transparent, ${G.accent}44, transparent)`, pointerEvents: "none" }} />
            <ComicHoot style={{ position: "fixed", left: "calc(50% - 650px)", top: "15%", width: "auto", height: "75vh", opacity: 0.3, pointerEvents: "none" }} />
            <ComicHoot2 style={{ position: "fixed", right: "calc(50% - 650px)", top: "15%", width: "auto", height: "75vh", opacity: 0.3, pointerEvents: "none" }} />
            
            {/*Cabecera*/}
            <div style={{ marginBottom: 32 }}>
                <h1 style={{
                    fontFamily: fonts.display, fontSize: 28, fontWeight: 800,
                    letterSpacing: "-0.03em", marginBottom: 6, color: G.text,
                }}>
                    {t.title}
                </h1>
                <p style={{ color: G.textSub, fontSize: 14 }}>
                    {t.subtitle}
                </p>
            </div>

            {/*Formulario*/}
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

                <div style={{ fontSize: 12, fontFamily: fonts.mono, color: G.accent, letterSpacing: "0.12em", textTransform: "uppercase" }}>
                    {lang === "en" ? "Source" : "Fuente"}
                </div>

                {/*URL con el botón de extracción*/}
                <div>
                    <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
                        <div style={{ flex: 1 }}>
                            <Input
                                label={t.urlLabel}
                                placeholder="https://..."
                                value={form.texto_url}
                                onChange={set("texto_url")}
                            />
                        </div>
                        <Button
                            onClick={handleExtraer}
                            disabled={extraiendo || !form.texto_url.trim()}
                            style={{ whiteSpace: "nowrap", padding: "10px 16px" }}>
                            {extraiendo ? <><Spinner size={14} /> {t.extracting}</> : t.extractBoton}
                        </Button>
                    </div>
                    {errorExtraccion && (
                        <p style={{ color: G.warn, fontSize: 12, marginTop: 4 }}>
                            {errorExtraccion}
                        </p>
                    )}
                </div>

                <div style={{ fontSize: 12, fontFamily: fonts.mono, color: G.accent, letterSpacing: "0.12em", textTransform: "uppercase" }}>
                    {lang === "en" ? "Content" : "Contenido"}
                </div>

                {/*Título*/}
                <div>
                    <Input
                        label={t.tituloLabel}
                        required
                        placeholder={t.tituloPlaceholder}
                        value={form.titulo}
                        onChange={set("titulo")}
                    />
                    {errors.titulo && <p style={{ color: G.danger, fontSize: 12, marginTop: 4 }}>{errors.titulo}</p>}
                </div>

                {/*Descripción*/}
                <div>
                    <Input
                        label={t.descripcionLabel}
                        required
                        multiline
                        placeholder={t.descripcionPlaceholder}
                        value={form.descripcion}
                        onChange={set("descripcion")}
                    />
                    {errors.descripcion && <p style={{ color: G.danger, fontSize: 12, marginTop: 4 }}>{errors.descripcion}</p>}
                </div>

                <div style={{ fontSize: 12, fontFamily: fonts.mono, color: G.accent, letterSpacing: "0.12em", textTransform: "uppercase" }}>
                    {lang === "en" ? "Metadata" : "Metadatos"}
                </div>

                {/*URL imagen y la fuente*/}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <div>
                        <Input
                            label={t.imagenLabel}
                            placeholder="https://..."
                            value={form.imagen_url}
                            onChange={set("imagen_url")}
                        />
                        {form.imagen_url && (
                            <img src={form.imagen_url} alt=""
                                style={{ width: "100%", height: 120, objectFit: "cover", borderRadius: 8, border: `1px solid ${G.border}`, marginTop: 8 }}
                                onError={e => { e.target.style.display = "none"; }} />
                        )}
                    </div>
                    <Input
                        label={t.fuenteLabel}
                        placeholder="RTVE, Snopes, ..."
                        value={form.fuente_nombre}
                        onChange={set("fuente_nombre")}
                    />

                </div>

                {/* Categoría y fecha*/}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <Input
                        label={t.categoriaLabel}
                        placeholder={t.categoriaPlaceholder}
                        value={form.categoria}
                        onChange={set("categoria")}
                    />
                    <Input
                        label={t.fechaLabel}
                        type="datetime-local"
                        value={form.fecha_publi}
                        onChange={set("fecha_publi")}
                    />
                </div>

                {error && <p style={{ color: G.danger, fontSize: 13, marginTop: 4 }}>{error}</p>}
                <Button
                    onClick={handleSubmit}
                    disabled={loading}
                    style={{ width: "100%", padding: "13px", fontSize: 15, marginTop: 8 }}>
                    {loading ? <><Spinner size={18} /> {t.analyzing}</> : t.analyzeBoton}
                </Button>
            </div>
        </div>
    );
}