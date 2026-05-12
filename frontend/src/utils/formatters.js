import { theme as G } from "../constants/theme";

export const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

// Colores según el score de riesgo
export function scoreColor(v){
    if (v >= 0.7) return G.danger;
    if (v >= 0.4) return G.warn;
    return G.ok;
}

// Metadatos visuales según EtiquetaEnum del backend
export function statusMeta(resultado){
    const map = {
        falsa: {label: "NOTICIA FALSA", color: G.danger, bg: G.dangerLo, icon: "✕"},
        verdadera: {label: "NOTICIA VERDADERA", color: G.ok, bg: G.okLo, icon: "✓"},
        pendiente: {label: "INDETERMINADO", color: G.warn, bg: G.warnLo, icon: "?"},
    };
    return map[resultado] ?? map.pendiente;
}

// Metadatos visuales según ImagenEnum del backend
export function imagenMeta(estatus){
    const map = {
        autentica: {label: "Imagen auténtica", color: G.ok, icon: "✓"},
        fuera_contexto: {label: "Fuera de contexto", color: G.warn, icon: "?"},
        generada_ia: {label: "Generada por IA", color: G.danger, icon: "✕"},
        pendiente: {label: "Sin analizar", color: G.muted, icon: "-"},
    };
    return map[estatus] ?? { label: estatus, color: G.muted, icon: "-" };
}

// mapeo sentimiento con pySentimiento en español
export const sentimientoLabel = {
    POS: "Positivo",
    NEG: "Negativo",
    NEU: "Neutro",
};

// nivel de confianza legible
export function confianzaLabel(probabilidad){
    const d = Math.abs(probabilidad-0.5);
    if (d >= 0.35) return { label: "Alta", color: G.ok };
    if (d >= 0.15) return { label: "Media", color: G.warn };
    return { label: "Baja", color: G.danger };
}

// Formato de fecha
export function formatFecha(isoString){
    if (!isoString) return "-";
    return new Date(isoString).toLocaleString("es-ES", {
        day: "2-digit", month: "2-digit", year: "numeric",
        hour: "2-digit", minute: "2-digit",
    });
}