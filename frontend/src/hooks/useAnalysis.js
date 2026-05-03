import { useState } from "react";
import { analizarNoticia } from "../services/api";
import { buildDemoValoracion, buildDemoNoticia } from "../utils/demoData";

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
        };

        try{
            const valoracion = await analizarNoticia(noticiaCreate);
            console.log("Recibido de backend", valoracion); //quitar
            const entry = {valoracion, noticia: noticiaCreate};
            setResult(entry);
            setHistory(prev => [entry, ...prev]);
        }catch(err){
            console.error("Error de la API:", err);
            //console.log("API no disponible, usando modo demo: ", err.message);
            // El modo demo genera datos simulados para seguir desarrollando el frontend
            //const noticia = buildDemoNoticia(noticiaCreate);
            //const valoracion = buildDemoValoracion(noticia.id);
            //const entry = {valoracion, noticia};
            //setResult(entry);
            //setHistory(prev => [entry, ...prev]);
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