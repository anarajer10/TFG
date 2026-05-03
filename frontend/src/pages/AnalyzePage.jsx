import { useState } from "react";
import { theme as G, fonts } from "../constants/theme";
import { Input, Button, Spinner, Card } from "../components/ui";

export default function AnalyzePage({ onAnalyze, loading }) {
    const [form, setForm] = useState({
        titulo: "",
        descripcion: "",
        texto_url: "",
        imagen_url: "",
        categoria: "",
        fecha_publi: "",
    });
    const [errors, setErrors] = useState({});

    function set(field) {
        return (value) => setForm(prev => ({ ...prev, [field]: value }));
    }

    function validate() {
        const e = {};
        if (!form.titulo.trim()) e.titulo = "El titulo de la noticia es obligatorio";
        if (!form.descripcion.trim()) e.descripcion = "La descripcion de la noticia es obligatoria";
        setErrors(e);
        return Object.keys(e).length === 0;
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
                    Introduce los datos de la noticia para poder realizar un análisis
                </p>
            </div>

            {/*Formulario (a lo mejor se modifica)*/}
            <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
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

                <Input
                    label="URL de la noticia"
                    placeholder="https://..."
                    value={form.texto_url}
                    onChange={set("texto_url")}
                />

                <Input
                    label="URL de la imagen de la noticia"
                    placeholder="https://..."
                    value={form.imagen_url}
                    onChange={set("imagen_url")}
                />

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

                <Button
                    onClick={handleSubmit}
                    disabled={loading}
                    style={{ width: "100%", padding: "13px", fontSize: 15, marginTop: 8 }}>
                    {loading ? <><Spinner size={18} /> Analizando...</> : "Analizar noticia"}
                </Button>
            </div>

            {/*Nota modo demo*/}
            <Card style={{ marginTop: 24, padding: "12px 16px" }}>
                <p style={{ color: G.muted, fontSize: 12 }}>
                    <span style={{ color: G.accent, fontFamily: fonts.mono }}>Modo demo</span>
                    {" "} activo cuando el backend no está disponible. Los resultados son simulados
                </p>
            </Card>
        </div>
    );
}