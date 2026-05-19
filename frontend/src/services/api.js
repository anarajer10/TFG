// Todas las llamadas al backend van aquí
// La URL base se lee de la variable de entorno VITE_API_BASE (en el .env)

const API_BASE = import.meta.env.VITE_API_BASE;

async function request(path, options = {}, timeout = 300000){
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout); // 5 min d timeout (los 300000 ms)
    const isBodyRequest = ["POST", "PUT", "PATCH"].includes(options.method?.toUpperCase());
    try{
        const res = await fetch(`${API_BASE}${path}`, {
            headers: isBodyRequest ? {"Content-Type": "application/json"} : {},
            signal: controller.signal,
            ...options,
        });
        clearTimeout(timeoutId);

        if(!res.ok){
            const detail = await res.json().catch(() => ({}));
            throw new Error(detail?.detail ?? `Error ${res.status}`);
        }

        return res.json();
    } catch (err){
        clearTimeout(timeoutId);
        throw err;
    }
}

// POST /analizar
export async function analizarNoticia(noticiaCreate){
    return request("/analizar", {
        method: "POST",
        body: JSON.stringify(noticiaCreate),
    });
}

// GET /extraer
export async function extraerNoticia(url){
    return request(`/extraer?url=${encodeURIComponent(url)}`, {}, 30000); // 30 segundos
}

// GET /noticias
export async function getNoticias({offset=0, limit=100} = {}){
    return request(`/noticias?offset=${offset}&limit=${limit}`);
}

// GET /noticias/:id
export async function getNoticia(id){
    return request(`/noticias/${id}`);
}

// GET /noticias/recientes
export async function getRecientes(limit=20, lang=null){
    const params = new URLSearchParams({limit});
    if (lang) params.append("lang", lang);
    return request(`/noticias/recientes?${params}`);
}

// GET /metricas
export async function getMetricas(){
    return request("/metricas");
}