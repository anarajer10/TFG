import { useState } from "react";
import { theme as G, fonts } from "../constants/theme";
import { Input, Button, Spinner } from "../components/ui";
import { extraerNoticia } from "../services/api";

export default function AnalyzePage({ onAnalyze, loading, error }) {
    const [form, setForm] = useState({
        texto_url: "",
        titulo: "",
        descripcion: "",
        imagen_url: "",
        categoria: "",
        fecha_publi: "",
        fuente_nombre: "",
    });
    const [errors, setErrors] = useState({});
    const [extraiendo, setExtraiendo] = useState(false);
    const [errorExtraccion, setErrorExtraccion] = useState(null);

    function set(field) {
        return (value) => setForm(prev => ({ ...prev, [field]: value }));
    }

    function validate() {
        const e = {};
        if (!form.titulo.trim()) e.titulo = "El título de la noticia es obligatorio";
        else if (form.titulo.trim().length < 10) e.titulo = "El título debe tener al menos 10 caracteres";

        if (!form.descripcion.trim()) e.descripcion = "La descripción de la noticia es obligatoria";
        else if (form.descripcion.trim().length < 50) e.descripcion = "La descripción debe tener al menos 50 caracteres";

        setErrors(e);
        return Object.keys(e).length === 0;
    }

    async function handleExtraer(){
        if (!form.texto_url.trim()) return;
        setExtraiendo(true);
        setErrorExtraccion(null);
        try{
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
            setErrorExtraccion("No se ha podido extraer automáticamente, necesita rellenar los campos manualmente.");
        } finally {
            setExtraiendo(false);
        }
    }

    function handleSubmit() {
        if (!validate()) return;
        onAnalyze(form);
    }

    return (
        <div style={{ maxWidth: 680, margin: "0 auto", padding: "40px 24px" }}>
            {/*Cabecera*/}
            <div style={{ marginBottom: 32 }}>
                <h1 style={{
                    fontFamily: fonts.display, fontSize: 28, fontWeight: 800,
                    letterSpacing: "-0.03em", marginBottom: 6,
                }}>
                    Analizar noticia
                </h1>
                <p style={{ color: G.textSub, fontSize: 14 }}>
                    Pega la URL de la noticia para extraer los datos automáticamente, o introdúcelos manualmente
                </p>
            </div>

            {/*Formulario*/}
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

                {/*URL con el botón de extracción*/}
                <div>
                    <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
                        <div style={{ flex: 1 }}>
                            <Input
                                label="URL de la noticia"
                                placeholder="https://..."
                                value={form.texto_url}
                                onChange={set("texto_url")}
                            />
                        </div>
                        <Button
                            onClick={handleExtraer}
                            disabled={extraiendo || !form.texto_url.trim()}
                            style={{ whiteSpace: "nowrap", padding: "10px 16px"}}>
                            {extraiendo ? <><Spinner size={14}/> Extrayendo información de la noticia</>: "Extraer datos"}
                        </Button>
                    </div>
                    {errorExtraccion && (
                        <p style={{ color: G.warn, fontSize: 12, marginTop: 4}}>
                            {errorExtraccion}
                        </p>
                    )}
                </div>

                {/*Título*/}
                <div>
                    <Input
                        label="Título"
                        required
                        placeholder="Titular de la noticia"
                        value={form.titulo}
                        onChange={set("titulo")}
                    />
                    {errors.titulo && <p style={{ color: G.danger, fontSize: 12, marginTop: 4 }}>{errors.titulo}</p>}
                </div>

                {/*Descripción*/}
                <div>
                    <Input
                        label="Cuerpo / descripción"
                        required
                        multiline
                        placeholder="Descripción de la noticia"
                        value={form.descripcion}
                        onChange={set("descripcion")}
                    />
                    {errors.descripcion && <p style={{ color: G.danger, fontSize: 12, marginTop: 4 }}>{errors.descripcion}</p>}
                </div>

                {/*URL imagen y la fuente*/}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <Input
                        label="URL de la imagen"
                        placeholder="https://..."
                        value={form.imagen_url}
                        onChange={set("imagen_url")}
                    />
                    <Input
                        label="Fuente"
                        placeholder="RTVE, Snopes, ..."
                        value={form.fuente_nombre}
                        onChange={set("fuente_nombre")}
                    />
                </div>

                {/* Categoría y fecha*/}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <Input
                        label="Categoría"
                        placeholder="Noticias o Fact-checker"
                        value={form.categoria}
                        onChange={set("categoria")}
                    />
                    <Input
                        label="Fecha de publicación"
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
                    {loading ? <><Spinner size={18} /> Analizando...</> : "Analizar noticia"}
                </Button>
            </div>
        </div>
    );
}