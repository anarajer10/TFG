// Todas las llamadas al backend van aquí
// La URL base se lee de la variable de entorno VITE_API_BASE (en el .env)

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function request(path, options = {}){
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 min d timeout
    
    try{
        const res = await fetch(`${API_BASE}${path}`, {
            headers: {"Content-Type": "application/json"},
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

// GET /noticias
export async function getNoticias({offset=0, limit=100} = {}){
    return request(`/noticias?offset=${offset}&limit=${limit}`);
}

// GET /noticias/:id
export async function getNoticia(id){
    return request(`/noticias/${id}`);
}