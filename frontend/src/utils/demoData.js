// En caso de que la API no esté disponible, una simulación de respuesta

export function buildDemoValoracion(noticiaId=1){
    const prob = parseFloat((Math.random()).toFixed(4));
    const resultado = prob >= 0.5 ? "falsa" : "verdadera";
    const estatuses = ["autentica", "fuera_contexto", "generada_ia", "pendiente"];

    return{
        id: Math.floor(Math.random()*1000),
        noticia_id: noticiaId,
        resultado,
        probabilidad: prob,
        explicacion:
        "El análisis detecta patrones lingüísticos asociados a contenido tendencioso."+
        "El texto presenta un nivel de objetividad bajo, con uso de lenguaje emocional y términos alarmistas."+
        "La imagen analizada no presenta evidencias claras de manipulación digital, aunque su coherencia "+
        "semántica con el título es limitada. En conjunto, el sistema clasifica esta noticia como"+
        `${resultado === "falsa" ? "posiblemente falsa" : "posiblemente verdadera"} con un nivel de confianza medio.`,
        punt_sentimiento: parseFloat((Math.random()*2-1).toFixed(4)),
        punt_objetividad: parseFloat((Math.random()).toFixed(4)),
        estatus_analisis_imagen: estatuses[Math.floor(Math.random()*estatuses.length)],
        fecha_analisis: new Date().toISOString(),
    };
}

// Simula la noticia que se envió para mostrar junto a la valoración
export function buildDemoNoticia(form){
    return{
        id: Math.floor(Math.random()*1000),
        titulo: form.titulo,
        descripcion: form.descripcion,
        imagen_url: form.imagen_url || null,
        texto_url: form.texto_url || "https://ejemplo.com",
        categoria: form.categoria || null,
        fecha_publi: form.fecha_publi || null,
        etiqueta: "pendiente",
        fuente_id: null,
    };
}