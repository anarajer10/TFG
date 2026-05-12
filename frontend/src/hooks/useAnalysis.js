import { useState } from "react";
import { analizarNoticia } from "../services/api";

export function useAnalysis(){
    const [loading, setLoading] = useState(false);
    const [error, setError]     = useState(null);
    const [result, setResult]   = useState(null);
    const [history, setHistory] = useState([]);

    async function analyze(formData){
        setError(null);
        setLoading(true);

        // noticiaCreate, con los campos que espera el backend
        const noticiaCreate = {
            titulo:         formData.titulo.trim(),
            descripcion:    formData.descripcion.trim(),
            texto_url:      formData.texto_url.trim() || `https://sin-url-${Date.now()}.com`,
            imagen_url:     formData.imagen_url?.trim() || null,
            categoria:      formData.categoria?.trim() || null,
            fecha_publi:    formData.fecha_publi || null,
            fuente_id:      null,
            etiqueta:       "pendiente",
            fuente_nombre:  formData.fuente_nombre?.trim() || null,
        };

        try{
            const resultado = await analizarNoticia(noticiaCreate);
            const entry = {
                valoracion: resultado.valoracion,
                noticia: resultado.noticia,
                fuente_nombre: resultado.fuente_nombre,
            };
            setResult(entry);
            setHistory(prev => [entry, ...prev]);
        }catch(err){
            console.error("Error de la API:", err);
            let msg = err.message;
            if (err.name === "AbortError") // timeout
                msg = "La solicitud ha tardado demasiado, inténtalo otra vez.";
            else if (err.message === "Failed to fetch") // Cuando el backend está caído
                msg = "No se ha podido conectar con el servidor, comprueba que el backend esté conectado."
            setError(err.message);
        }finally{
            setLoading(false);
        }
    }

    function clearResult(){
        setResult(null);
        setError(null);
    }

    return {loading, error, result, history, analyze, clearResult};
}