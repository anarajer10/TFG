import json
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

morado = LinearSegmentedColormap.from_list("morado", ["#FFFFFF", "#281C78"])

def plot_confusion(matriz, titulo, nombre_archivo):
    cm = np.array(matriz)
    etiquetas = ["Verdadera (0)", "Falsa (1)"]

    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap=morado, xticklabels=etiquetas,
                yticklabels=etiquetas, ax=ax, cbar=False, linewidths=0.5, vmin=0, vmax=90)
    ax.set_xlabel("Predicción")
    ax.set_ylabel("Clase real")
    ax.set_title(titulo)
    plt.tight_layout()
    plt.savefig(nombre_archivo, dpi=150, bbox_inches="tight")
    plt.close()

with open("metricas_es.json") as f:
    es = json.load(f)
with open("metricas_en.json") as f:
    en = json.load(f)

plot_confusion(es["matriz_confusion"], "Modelo español (con LinearSVC)", "confusion_es.png")
plot_confusion(en["matriz_confusion"], "Modelo inglés (con LogisticRegression)", "confusion_en.png")