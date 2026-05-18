"""
=============================================================================
 CASO PRACTICO — Prediccion de diagnostico de cancer
 UAX · Ingenieria Matematica · Inteligencia Artificial · 2025/26
-----------------------------------------------------------------------------
 PIPELINE COMPLETO en un unico archivo.

 Uso:
     python cancer_pipeline.py

 Lo que hace:
     1. Carga los 6 CSV originales y los une por paciente_id.
     2. Realiza el EDA con figuras.
     3. Selecciona features con justificacion (excluye leakage + constantes).
     4. Construye 2 features compuestas: n_mutaciones, n_comorbilidades.
     5. Preprocesa (encoding + scaler + split estratificado 64/16/20).
     6. Entrena 4 modelos ML clasicos (LogReg, RF, HistGB, XGBoost).
     7. Entrena la Red Neuronal MLP con regularizacion y threshold tuning.
     8. Genera la comparativa global con ranking final y curvas.
     9. Persiste todos los artefactos: tablas, figuras y modelos.

 Salidas:
     data/      datasets unificados y matrices preprocesadas
     figs/      24 figuras en PNG (EDA + resultados)
     tables/    21 tablas en CSV/JSON con todas las metricas
     models/    6 modelos serializados (preprocessor + 4 ML + MLP)

 Reproducibilidad:
     SEED = 42 fijo en Python, NumPy, PyTorch y PYTHONHASHSEED.
     torch.backends.cudnn.deterministic = True

 Dependencias:
     pip install pandas scikit-learn matplotlib seaborn xgboost torch joblib scipy
=============================================================================
"""

# =============================================================================
# CONFIGURACION GLOBAL Y SEMILLAS
# =============================================================================
import os
import json
import time
import random
import warnings
from pathlib import Path

SEED = 42
os.environ["PYTHONHASHSEED"] = str(SEED)
random.seed(SEED)

import numpy as np
np.random.seed(SEED)

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib

from scipy.stats import spearmanr, pointbiserialr

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OrdinalEncoder, OneHotEncoder
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                             f1_score, roc_auc_score, average_precision_score,
                             confusion_matrix, roc_curve, precision_recall_curve,
                             brier_score_loss)
from sklearn.calibration import calibration_curve
from sklearn.utils.class_weight import compute_class_weight
from sklearn.feature_selection import mutual_info_classif

from xgboost import XGBClassifier

# PyTorch se importa de forma diferida dentro de la Fase 5 para que el
# script pueda ejecutar las fases 1-4 y 6 sin tenerlo instalado (util si solo
# se quieren regenerar las figuras de ML clasicos desde el cache).

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)   # silencia 'invalid value in divide' (alcohol tiene std=0)

sns.set_theme(style="whitegrid", context="notebook")
plt.rcParams["figure.dpi"]    = 110
plt.rcParams["savefig.dpi"]   = 150
plt.rcParams["savefig.bbox"]  = "tight"

# Directorios del proyecto (relativos a este script)
ROOT       = Path(__file__).resolve().parent
DATA_DIR   = ROOT / "data"
FIGS_DIR   = ROOT / "figs"
TABLES_DIR = ROOT / "tables"
MODELS_DIR = ROOT / "models"
for d in (FIGS_DIR, TABLES_DIR, MODELS_DIR):
    d.mkdir(parents=True, exist_ok=True)


def section(title):
    """Imprime un encabezado de seccion grande para separar fases en logs."""
    print("\n" + "=" * 78)
    print(f" {title}")
    print("=" * 78)


# =============================================================================
# FASE 1 — CARGA DE LOS 6 CSV, MERGE Y EDA
# =============================================================================
def fase_1_carga_y_eda():
    section("FASE 1 — Carga, merge y analisis exploratorio")

    # Los 6 CSV traen BOM UTF-8 (todos menos uno), por eso utf-8-sig
    archivos = {
        "bioquimicos":      "CASOCANCER_01_BIOQUIMICOS.csv",
        "clinicos":         "CASOCANCER_02_CLINICOS.csv",
        "geneticos":        "CASOCANCER_03_GENETICOS.csv",
        "economicos":       "CASOCANCER_03_ECONOMICOS.csv",
        "generales":        "CASOCANCER_05_GENERALES.csv",
        "sociodemograficos":"CASOCANCER_06_SOCIODEMOGRAFICOS.csv",
    }

    dfs = {}
    resumen = []
    for nombre, fichero in archivos.items():
        df = pd.read_csv(DATA_DIR / fichero, encoding="utf-8-sig")
        df.columns = df.columns.str.strip()
        # Conversion forzada de costes europeos ("6377,03" → float).
        # No nos fiamos del dtype reportado por pandas; comprobamos por nombre.
        for col in ["coste_total", "coste_farmaco"]:
            if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].astype(str).str.replace(",", ".").astype(float)
        dfs[nombre] = df
        resumen.append({
            "coleccion": nombre, "n_filas": len(df), "n_columnas": df.shape[1],
            "columnas": ", ".join(df.columns),
        })
        print(f"  · {fichero:40s}  shape={df.shape}")

    pd.DataFrame(resumen).to_csv(TABLES_DIR / "00_resumen_colecciones.csv", index=False)

    # MERGE por paciente_id
    df = (dfs["bioquimicos"]
            .merge(dfs["clinicos"],          on="paciente_id")
            .merge(dfs["geneticos"],         on="paciente_id")
            .merge(dfs["economicos"],        on="paciente_id")
            .merge(dfs["generales"],         on="paciente_id")
            .merge(dfs["sociodemograficos"], on="paciente_id"))

    assert len(df) == 50001,                   "El merge perdio pacientes"
    assert df["paciente_id"].nunique() == 50001, "paciente_id no es unico"
    assert df.isnull().sum().sum() == 0,       "Hay valores nulos"

    df.to_csv(DATA_DIR / "df_merged.csv", index=False)
    print(f"\n  Dataset unificado: {df.shape}  ·  sin nulos  ·  paciente_id unico")
    print(f"  Prevalencia cancer: {df['cancer'].mean()*100:.2f} %  "
          f"(ratio {(df['cancer']==0).sum() / (df['cancer']==1).sum():.2f}:1)")

    # ----- Figura 01: distribucion del target -----
    fig, ax = plt.subplots(figsize=(7, 5))
    counts = df["cancer"].value_counts().sort_index()
    colors = ["#2E86AB", "#E63946"]
    bars = ax.bar(["Sin cancer (0)", "Cancer (1)"], counts.values,
                  color=colors, edgecolor="black")
    for bar, val, pct in zip(bars, counts.values, counts.values / counts.sum() * 100):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 500,
                f"{val:,}\n({pct:.2f} %)", ha="center", fontsize=11, fontweight="bold")
    ax.set_ylabel("Numero de pacientes")
    ax.set_title("Distribucion del target — desbalance 4,18 : 1")
    ax.set_ylim(0, counts.max() * 1.13)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "01_distribucion_cancer.png")
    plt.close()

    # ----- Figura 02: boxplots de bioquimicos por clase -----
    bio_cols = ["glucosa","colesterol","trigliceridos","hemoglobina","leucocitos","plaquetas","creatinina"]
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    for ax, col in zip(axes.flatten(), bio_cols):
        sns.boxplot(data=df, x="cancer", y=col, ax=ax,
                    palette=["#2E86AB", "#E63946"], showfliers=False)
        ax.set_title(col); ax.set_xlabel(""); ax.set_ylabel("")
    axes.flatten()[-1].axis("off")
    plt.suptitle("Variables bioquimicas por clase (sin outliers)", fontsize=14, y=1.01)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "02_boxplots_numericas_por_clase.png")
    plt.close()

    # ----- Figura 03: heatmap de correlacion -----
    numeric = df.select_dtypes(include=[np.number]).columns.tolist()
    corr = df[numeric].corr()
    fig, ax = plt.subplots(figsize=(13, 11))
    sns.heatmap(corr, annot=False, cmap="RdBu_r", center=0, vmin=-1, vmax=1,
                square=True, cbar_kws={"shrink": 0.8})
    ax.set_title("Matriz de correlacion de Pearson (todas las numericas)")
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "03_correlation_heatmap.png")
    plt.close()

    # ----- Figura 04: prevalencia por categorica -----
    cat_cols = ["actividad_fisica","nivel_educativo","nivel_ingresos","zona","estado_civil","tipo_seguro"]
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    for ax, col in zip(axes.flatten(), cat_cols):
        tasa = df.groupby(col)["cancer"].mean().sort_values()
        tasa.plot(kind="barh", ax=ax, color="#2E86AB", edgecolor="black")
        ax.axvline(df["cancer"].mean(), color="#E63946", linestyle="--",
                   label=f"Baseline {df['cancer'].mean()*100:.2f} %")
        ax.set_title(col); ax.set_xlabel("Prevalencia cancer")
        ax.legend(fontsize=8)
        # Persistir tabla por categoria
        tasa.to_frame("prev_cancer").to_csv(TABLES_DIR / f"03_cat_{col}.csv")
    plt.suptitle("Prevalencia de cancer por categoria", fontsize=14, y=1.01)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "04_prevalencia_por_categoria.png")
    plt.close()

    # ----- Correlaciones con cancer + mutual info -----
    bin_cols = ["diabetes","hipertension","obesidad","enfermedad_cardiaca","asma","epoc",
                "fumador","alcohol","vive",
                "mut_BRCA1","mut_TP53","mut_EGFR","mut_KRAS","mut_PIK3CA","mut_ALK","mut_BRAF"]
    num_cont = ["edad","glucosa","colesterol","trigliceridos","hemoglobina","leucocitos",
                "plaquetas","creatinina","num_hijos","distancia_hospital_km",
                "coste_total","coste_farmaco","num_ingresos","dias_hospital"]

    corrs = {}
    for col in bin_cols + num_cont:
        if col in df.columns:
            try:
                r = df[col].astype(float).corr(df["cancer"].astype(float))
                corrs[col] = round(r, 4)
            except Exception:
                pass
    pd.Series(corrs).sort_values(ascending=False).to_csv(
        TABLES_DIR / "02_correlaciones_con_cancer.csv", header=["pearson_r"])

    # Medias por clase
    medias = df.groupby("cancer")[num_cont].mean().T
    medias["delta_pct"] = (medias[1] - medias[0]) / medias[0].abs() * 100
    medias.round(3).to_csv(TABLES_DIR / "01_medias_por_clase.csv")

    # ----- Figura 05: mutual information -----
    X_mi = df.drop(columns=["paciente_id", "cancer"])
    # Codificar categoricas para MI
    for c in cat_cols:
        if c in X_mi.columns:
            X_mi[c] = pd.factorize(X_mi[c])[0]
    mi = mutual_info_classif(X_mi, df["cancer"], random_state=SEED)
    mi_s = pd.Series(mi, index=X_mi.columns).sort_values(ascending=True)
    mi_s.to_csv(TABLES_DIR / "04_mutual_information.csv", header=["mutual_info"])

    fig, ax = plt.subplots(figsize=(10, 9))
    colors = ["#E63946" if v > 0.05 else "#2E86AB" for v in mi_s.values]
    ax.barh(mi_s.index, mi_s.values, color=colors, edgecolor="black")
    ax.axvline(0.05, color="black", linestyle="--", alpha=0.5, label="Umbral 0.05")
    ax.set_xlabel("Mutual Information con `cancer`")
    ax.set_title("Mutual information de cada predictor con el target")
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "05_mutual_information.png")
    plt.close()

    return df


# =============================================================================
# FASE 2 — SELECCION DE FEATURES + FEATURE ENGINEERING
# =============================================================================
def fase_2_seleccion_y_engineering(df):
    section("FASE 2 — Seleccion de features + feature engineering")

    # === Justificacion de cada exclusion ===
    decisiones = [
        ("paciente_id",   "EXCLUIR", "identificador",          "Identificador unico, no es predictor"),
        ("alcohol",       "EXCLUIR", "constante",              "vale 1 en los 50.001 pacientes (std=0)"),
        ("coste_total",   "EXCLUIR", "data_leakage",           "Coste post-diagnostico (r=+0,89 con cancer)"),
        ("dias_hospital", "EXCLUIR", "data_leakage",           "Hospitalizacion post-diagnostico (r=+0,88)"),
        ("coste_farmaco", "EXCLUIR", "data_leakage",           "Medicacion oncologica post-dx (r=+0,85)"),
        ("num_ingresos",  "EXCLUIR", "data_leakage",           "Reingresos derivados del seguimiento (r=+0,64)"),
        ("vive",          "EXCLUIR", "data_leakage",           "Mortalidad es desenlace, no antecedente"),
    ]
    df_dec = pd.DataFrame(decisiones, columns=["variable","decision","motivo","justificacion"])
    df_dec.to_csv(TABLES_DIR / "05_decisiones_features.csv", index=False)
    print("\nExclusiones aplicadas:")
    print(df_dec.to_string(index=False))

    excluir = df_dec.loc[df_dec["decision"] == "EXCLUIR", "variable"].tolist()
    df_features = df.drop(columns=excluir).copy()
    print(f"\n  Tras exclusion: {df_features.shape[1] - 1} predictoras (sin contar cancer)")

    # === Figura 06: feature selection bar chart ===
    bin_cols = ["diabetes","hipertension","obesidad","enfermedad_cardiaca","asma","epoc","fumador",
                "mut_BRCA1","mut_TP53","mut_EGFR","mut_KRAS","mut_PIK3CA","mut_ALK","mut_BRAF"]
    cat_cols = ["actividad_fisica","nivel_educativo","nivel_ingresos","zona","estado_civil","tipo_seguro"]
    num_cols = ["edad","glucosa","colesterol","trigliceridos","hemoglobina","leucocitos",
                "plaquetas","creatinina","num_hijos","distancia_hospital_km"]

    # Mapeo nombre → tipo y decision
    def clasifica(v):
        if v == "cancer":  return ("TARGET", "binaria", "Variable objetivo")
        if v in excluir:
            motivo = df_dec.loc[df_dec.variable==v, "motivo"].iloc[0]
            tipo = "binaria" if v in {"alcohol","vive"} else "data_leakage"
            return ("EXCLUIR", tipo, motivo)
        if v in bin_cols:  return ("INCLUIR", "binaria",            "Comorbilidad / mutacion / habito conocido")
        if v in num_cols:  return ("INCLUIR", "numerica_continua",  "Predictora medible en el cribado")
        if v in cat_cols:
            if v == "actividad_fisica":  orden = "Orden: Baja < Moderada < Alta"
            elif v == "nivel_educativo": orden = "Orden: Sin estudios < Primaria < Secundaria < Universitario"
            elif v == "nivel_ingresos":  orden = "Orden: Muy bajo < Bajo < Medio < Alto"
            else:                        orden = "Categorica sin orden, OneHot"
            tipo = "ordinal" if v in {"actividad_fisica","nivel_educativo","nivel_ingresos"} else "nominal"
            return ("INCLUIR", tipo, orden)
        return ("INCLUIR", "?", "")

    all_vars = list(df.columns)
    info = pd.DataFrame([(v, *clasifica(v)) for v in all_vars],
                        columns=["variable","decision","tipo","detalle"])
    info = info.set_index("variable").loc[
        sorted(all_vars, key=lambda v: (info.set_index("variable").loc[v,"decision"] != "INCLUIR", v))
    ].reset_index()

    # === Figura 06: justificacion visual de la seleccion de features ===
    # Panel izquierdo: las 7 exclusiones con la correlacion que las justifica
    # Panel derecho: las 30 features incluidas agrupadas por tipo
    mut_cols    = ["mut_BRCA1","mut_TP53","mut_EGFR","mut_KRAS","mut_PIK3CA","mut_ALK","mut_BRAF"]
    com_cols    = ["diabetes","hipertension","obesidad","enfermedad_cardiaca","asma","epoc"]
    habito_cols = ["fumador"]  # solo este; alcohol esta excluido
    socio_cols  = ["zona","estado_civil","tipo_seguro","nivel_educativo","nivel_ingresos",
                   "num_hijos","distancia_hospital_km","edad"]
    bioq_cols   = ["glucosa","colesterol","trigliceridos","hemoglobina","leucocitos","plaquetas","creatinina"]
    activ_cols  = ["actividad_fisica"]

    # Correlaciones de las EXCLUIDAS (con cancer) -> para el panel izquierdo
    excl_data = []
    for v in ["coste_total","dias_hospital","coste_farmaco","num_ingresos","vive","alcohol","paciente_id"]:
        if v in df.columns:
            if v == "paciente_id":
                excl_data.append((v, 0.0, "Identificador", "Sin valor predictivo"))
            elif v == "alcohol":
                excl_data.append((v, 0.0, "Varianza cero", "Vale 1 en los 50.001 pacientes"))
            else:
                try:
                    r = df[v].astype(float).corr(df["cancer"].astype(float))
                    sign = "+" if r >= 0 else "−"
                    excl_data.append((v, abs(r), "Data leakage", f"r = {sign}{abs(r):.2f} con cancer"))
                except Exception:
                    excl_data.append((v, 0.0, "Data leakage", "Variable post-diagnostico"))

    # Ordenar por correlacion descendente
    excl_data.sort(key=lambda x: -x[1])

    # === FIGURA con 2 paneles ===
    from matplotlib.gridspec import GridSpec
    fig = plt.figure(figsize=(16, 9))
    gs = GridSpec(1, 2, width_ratios=[0.9, 1.30], wspace=0.25)

    # ----- PANEL IZQUIERDO: las 7 exclusiones con correlaciones -----
    ax1 = fig.add_subplot(gs[0])
    vars_e   = [e[0] for e in excl_data]
    vals_e   = [e[1] for e in excl_data]
    motivos  = [e[2] for e in excl_data]
    detalles = [e[3] for e in excl_data]
    color_map = {"Data leakage": "#E63946", "Identificador": "#94A3B8", "Varianza cero": "#F4A261"}
    colors_e = [color_map[m] for m in motivos]

    y_pos = np.arange(len(vars_e))
    bars = ax1.barh(y_pos, vals_e, color=colors_e, edgecolor="black", linewidth=0.6, height=0.7)
    # Etiquetas a la derecha de cada barra
    for i, (b, det) in enumerate(zip(bars, detalles)):
        ax1.text(b.get_width() + 0.02, b.get_y() + b.get_height()/2, det,
                 va="center", fontsize=10, color="#1A1A2E", fontweight="bold")

    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(vars_e, fontsize=11)
    ax1.invert_yaxis()
    ax1.set_xlim(0, 1.15)
    ax1.set_xlabel("|correlacion con cancer|", fontsize=10)
    ax1.set_title("7 variables EXCLUIDAS\nJustificacion cuantitativa",
                  fontsize=13, fontweight="bold", color="#1D3557", pad=15, loc="left")

    # Leyenda del panel izquierdo
    from matplotlib.patches import Patch
    leg_items = [
        Patch(color="#E63946", label="Data leakage  (5)"),
        Patch(color="#F4A261", label="Varianza cero  (1)"),
        Patch(color="#94A3B8", label="Identificador  (1)"),
    ]
    ax1.legend(handles=leg_items, loc="lower right", fontsize=9, framealpha=0.95)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.grid(axis="x", alpha=0.3, linestyle="--")

    # ----- PANEL DERECHO: resumen visual simple, sin tarjetas individuales -----
    ax2 = fig.add_subplot(gs[1])
    ax2.set_xlim(0, 10); ax2.set_ylim(0, 10); ax2.axis("off")

    grupos = [
        ("Bioquimicas",       bioq_cols,                 "#2E86AB"),
        ("Comorbilidades",    com_cols,                  "#457B9D"),
        ("Mutaciones",        mut_cols,                  "#1D3557"),
        ("Sociodemograficas", socio_cols,                "#76C1C7"),
        ("Estilo de vida",    habito_cols + activ_cols,  "#A8DADC"),
    ]

    # Titulo del panel derecho
    ax2.text(0.5, 9.6, "30 variables INCLUIDAS",
             fontsize=16, fontweight="bold", color="#10B981")
    ax2.text(0.5, 9.15, "agrupadas en 5 bloques tematicos",
             fontsize=11, color="#475569", style="italic")

    # Stacked bar horizontal con las categorias (1 sola barra)
    bar_y     = 8.2
    bar_h     = 0.55
    bar_xstart = 0.5
    bar_total  = 9.0
    total_vars = sum(len(g[1]) for g in grupos)

    x_cursor = bar_xstart
    for nombre, items, color in grupos:
        w = bar_total * (len(items) / total_vars)
        ax2.add_patch(plt.Rectangle((x_cursor, bar_y), w, bar_h,
                                     facecolor=color, edgecolor="white", linewidth=1.5))
        # Numero centrado en cada bloque
        ax2.text(x_cursor + w/2, bar_y + bar_h/2, str(len(items)),
                 ha="center", va="center", fontsize=13, fontweight="bold",
                 color="white" if color != "#A8DADC" else "#1D3557")
        x_cursor += w

    # Leyenda con icono de color + nombre + contador para cada bloque (compacta, 5 filas)
    y_start = 7.0
    row_h   = 1.05
    for i, (nombre, items, color) in enumerate(grupos):
        yi = y_start - i * row_h
        # Cuadro de color a la izquierda
        ax2.add_patch(plt.Rectangle((0.5, yi - 0.15), 0.45, 0.45,
                                     facecolor=color, edgecolor=color))
        ax2.text(0.725, yi + 0.075, str(len(items)),
                 ha="center", va="center", fontsize=11, fontweight="bold",
                 color="white" if color != "#A8DADC" else "#1D3557")
        # Nombre de la categoria
        ax2.text(1.15, yi + 0.18, nombre,
                 fontsize=12, fontweight="bold", color="#1A1A2E", va="center")
        # Lista de variables (en una sola linea, compacta)
        items_str = " · ".join(items)
        # Truncar si es muy largo
        if len(items_str) > 65:
            items_str = items_str[:62] + "..."
        ax2.text(1.15, yi - 0.10, items_str,
                 fontsize=8.5, color="#475569", va="center",
                 family="DejaVu Sans")

    # Banner final: feature engineering como destacado
    fe_y = y_start - 5 * row_h - 0.25
    ax2.add_patch(plt.Rectangle((0.5, fe_y), 9.0, 0.75,
                                 facecolor="#FFF3E0", edgecolor="#F59E0B", linewidth=1.5))
    ax2.add_patch(plt.Rectangle((0.5, fe_y), 0.10, 0.75,
                                 facecolor="#F59E0B", edgecolor="#F59E0B"))
    ax2.text(0.85, fe_y + 0.50, "+ FEATURE ENGINEERING",
             fontsize=11, fontweight="bold", color="#D97706", va="center")
    ax2.text(0.85, fe_y + 0.22,
             "n_mutaciones (ρ=0,29)  ·  n_comorbilidades (ρ=0,18)",
             fontsize=9.5, color="#475569", va="center")
    # Badge "+2" a la derecha
    from matplotlib.patches import FancyBboxPatch
    badge_fe = FancyBboxPatch((8.85, fe_y + 0.22), 0.55, 0.35,
                               boxstyle="round,pad=0.02,rounding_size=0.10",
                               facecolor="#F59E0B", edgecolor="#F59E0B", linewidth=0)
    ax2.add_patch(badge_fe)
    ax2.text(9.125, fe_y + 0.395, "+2",
             fontsize=11, fontweight="bold", color="white", va="center", ha="center")

    plt.suptitle("Seleccion de features: exclusiones justificadas + 30 predictoras agrupadas",
                 fontsize=15, fontweight="bold", color="#1A1A2E", y=1.01)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "06_feature_selection.png")
    plt.close()

    # === FEATURE ENGINEERING: n_mutaciones y n_comorbilidades ===
    mut_cols = ["mut_BRCA1","mut_TP53","mut_EGFR","mut_KRAS","mut_PIK3CA","mut_ALK","mut_BRAF"]
    com_cols = ["diabetes","hipertension","obesidad","enfermedad_cardiaca","asma","epoc"]
    df_features["n_mutaciones"]     = df_features[mut_cols].sum(axis=1)
    df_features["n_comorbilidades"] = df_features[com_cols].sum(axis=1)

    rho_mut, _ = spearmanr(df_features["n_mutaciones"],     df_features["cancer"])
    rho_com, _ = spearmanr(df_features["n_comorbilidades"], df_features["cancer"])
    print(f"\nFeatures engineered:")
    print(f"  · n_mutaciones      ∈ [0, {df_features.n_mutaciones.max()}]  "
          f"Spearman ρ con cancer = {rho_mut:.4f}")
    print(f"  · n_comorbilidades  ∈ [0, {df_features.n_comorbilidades.max()}]  "
          f"Spearman ρ con cancer = {rho_com:.4f}")

    # === Figura 06b: monotonia de las nuevas features ===
    tbl_mut = df_features.groupby("n_mutaciones").agg(
        n=("cancer","size"), prev=("cancer","mean")).round(4)
    tbl_com = df_features.groupby("n_comorbilidades").agg(
        n=("cancer","size"), prev=("cancer","mean")).round(4)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, tbl, name, rho in [(axes[0], tbl_mut, "n_mutaciones", rho_mut),
                               (axes[1], tbl_com, "n_comorbilidades", rho_com)]:
        x = tbl.index
        y = tbl["prev"] * 100
        pal = ["#A8DADC","#76C1C7","#457B9D","#1D3557","#E63946","#990022","#666"] * 2
        ax.bar(x, y, color=pal[:len(x)], edgecolor="black")
        ax.axhline(df_features["cancer"].mean() * 100,
                   color="black", linestyle="--", alpha=0.6,
                   label=f"Prevalencia global ({df_features['cancer'].mean()*100:.2f} %)")
        for xi, yi, ni in zip(x, y, tbl["n"]):
            ax.text(xi, yi+1.0, f"{yi:.1f}%\n(n={ni:,})", ha="center", fontsize=8)
        ax.set_xlabel(name); ax.set_ylabel("Prevalencia cancer (%)")
        ax.set_title(f"{name} vs cancer  (Spearman ρ = {rho:.3f})")
        ax.legend(loc="upper left")
        ax.set_ylim(0, max(y) * 1.18)
    plt.suptitle("Features engineered: monotonia con el target", fontsize=13, y=1.02)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "06b_feature_engineering.png")
    plt.close()

    # === Figura 07: correlacion entre predictoras ===
    pred_cols = [c for c in df_features.columns if c != "cancer"]
    df_corr = df_features[pred_cols].copy()
    for c in cat_cols:
        if c in df_corr.columns:
            df_corr[c] = pd.factorize(df_corr[c])[0]
    corr_pred = df_corr.corr().abs()
    fig, ax = plt.subplots(figsize=(13, 11))
    sns.heatmap(corr_pred, cmap="YlOrRd", vmin=0, vmax=1, square=True,
                cbar_kws={"shrink": 0.8})
    ax.set_title("Matriz de correlacion absoluta entre predictoras\n"
                 "(Pearson para numericas, factorize+Pearson para categoricas)")
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "07_correlacion_predictoras.png")
    plt.close()

    # === Metadata final ===
    metadata = {
        "n_features": int(len(pred_cols)),
        "numericas_continuas": num_cols + ["n_mutaciones", "n_comorbilidades"],
        "binarias": bin_cols,
        "ordinales": {
            "actividad_fisica":  ["Baja", "Moderada", "Alta"],
            "nivel_educativo":   ["Sin estudios", "Primaria", "Secundaria", "Universitario"],
            "nivel_ingresos":    ["Muy bajo", "Bajo", "Medio", "Alto"],
        },
        "nominales": {
            "zona":         "OneHot drop=first",
            "estado_civil": "OneHot drop=first",
            "tipo_seguro":  "OneHot drop=first",
        },
        "target": "cancer",
        "exclusiones": excluir,
        "feature_engineering": {
            "n_mutaciones":     {"derivada_de": mut_cols, "spearman_rho": round(rho_mut, 4)},
            "n_comorbilidades": {"derivada_de": com_cols, "spearman_rho": round(rho_com, 4)},
        },
    }
    with open(TABLES_DIR / "06_feature_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    df_features.to_csv(DATA_DIR / "df_features.csv", index=False)
    print(f"\n  df_features guardado: {df_features.shape}")
    return df_features, metadata


# =============================================================================
# FASE 3 — PREPROCESAMIENTO
# =============================================================================
def fase_3_preprocesamiento(df_features, metadata):
    section("FASE 3 — Encoding, escalado, split estratificado")

    X = df_features.drop(columns=[metadata["target"]])
    y = df_features[metadata["target"]]

    # Split 64/16/20 estratificado (test fuera primero)
    X_trainval, X_test, y_trainval, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=SEED)
    X_train, X_val, y_train, y_val = train_test_split(
        X_trainval, y_trainval, test_size=0.20, stratify=y_trainval, random_state=SEED)

    splits = pd.DataFrame([
        {"split": "train", "n": len(X_train), "%": len(X_train)/len(X)*100, "prev": y_train.mean()*100},
        {"split": "val",   "n": len(X_val),   "%": len(X_val)/len(X)*100,   "prev": y_val.mean()*100},
        {"split": "test",  "n": len(X_test),  "%": len(X_test)/len(X)*100,  "prev": y_test.mean()*100},
    ]).round(3)
    splits.to_csv(TABLES_DIR / "08_splits_resumen.csv", index=False)
    print(splits.to_string(index=False))

    # Figura 08: distribucion del target en los splits
    fig, ax = plt.subplots(figsize=(8, 5))
    x_pos = np.arange(len(splits))
    width = 0.35
    n_neg = [len(X_train)*(1-y_train.mean()), len(X_val)*(1-y_val.mean()), len(X_test)*(1-y_test.mean())]
    n_pos = [len(X_train)*y_train.mean(),     len(X_val)*y_val.mean(),     len(X_test)*y_test.mean()]
    ax.bar(x_pos - width/2, n_neg, width, label="Sin cancer", color="#2E86AB", edgecolor="black")
    ax.bar(x_pos + width/2, n_pos, width, label="Cancer",     color="#E63946", edgecolor="black")
    ax.set_xticks(x_pos); ax.set_xticklabels(splits["split"])
    ax.set_ylabel("Numero de pacientes")
    ax.set_title("Distribucion del target en los 3 splits (estratificacion verificada)")
    for i, (n, p) in enumerate(zip(n_neg, n_pos)):
        ax.text(i - width/2, n + 200, f"{int(n):,}", ha="center", fontsize=9)
        ax.text(i + width/2, p + 200, f"{int(p):,}", ha="center", fontsize=9)
    ax.legend()
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "08_distribucion_splits.png")
    plt.close()

    # ColumnTransformer
    NUM   = metadata["numericas_continuas"]
    BIN   = metadata["binarias"]
    ORD_COLS = list(metadata["ordinales"].keys())
    ORDERS   = [metadata["ordinales"][c] for c in ORD_COLS]
    NOM   = list(metadata["nominales"].keys())

    preprocessor = ColumnTransformer([
        ("num", StandardScaler(),                          NUM),
        ("bin", "passthrough",                              BIN),
        ("ord", OrdinalEncoder(categories=ORDERS),         ORD_COLS),
        ("cat", OneHotEncoder(drop="first", sparse_output=False,
                              handle_unknown="ignore"),    NOM),
    ], remainder="drop", verbose_feature_names_out=False)

    X_train_p = preprocessor.fit_transform(X_train)     # fit SOLO en train
    X_val_p   = preprocessor.transform(X_val)
    X_test_p  = preprocessor.transform(X_test)
    feature_names = preprocessor.get_feature_names_out().tolist()

    print(f"\n  Tras encoding: {X_train_p.shape[1]} columnas (era {len(NUM)+len(BIN)+len(ORD_COLS)+len(NOM)} pre-encoding)")
    n_cont = len(NUM)
    assert abs(X_train_p[:, :n_cont].mean()) < 1e-3
    print(f"  Escalado correcto: mean={X_train_p[:,:n_cont].mean():.6f}  std={X_train_p[:,:n_cont].std():.6f}")

    # Figura 09: efecto del scaler en algunas variables
    fig, axes = plt.subplots(2, 4, figsize=(16, 8))
    vars_show = NUM[:8]
    for ax, var in zip(axes.flatten(), vars_show):
        ax.hist(X_train[var], bins=50, alpha=0.5, label="Antes", color="#E63946")
        idx = NUM.index(var)
        ax.hist(X_train_p[:, idx], bins=50, alpha=0.5, label="Despues", color="#2E86AB")
        ax.set_title(var); ax.legend(fontsize=8)
    plt.suptitle("Efecto del StandardScaler (en train)", fontsize=13, y=1.01)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "09_efecto_scaler.png")
    plt.close()

    # class_weight balanceado (solo en y_train)
    weights = compute_class_weight("balanced", classes=np.array([0,1]), y=y_train)
    class_weight = {int(c): float(w) for c, w in zip([0,1], weights)}
    with open(TABLES_DIR / "07_class_weight.json", "w") as f:
        json.dump(class_weight, f, indent=2)
    print(f"\n  class_weight balanceado: {class_weight}  (ratio {weights[1]/weights[0]:.3f}:1)")

    # Persistencia
    joblib.dump(preprocessor, MODELS_DIR / "preprocessor.joblib")
    np.savez_compressed(
        DATA_DIR / "preprocessed.npz",
        X_train=X_train_p, y_train=y_train.values.astype(np.int64),
        X_val=X_val_p,     y_val=y_val.values.astype(np.int64),
        X_test=X_test_p,   y_test=y_test.values.astype(np.int64),
        feature_names=np.array(feature_names),
    )
    print(f"\n  ✓ models/preprocessor.joblib")
    print(f"  ✓ data/preprocessed.npz")
    return preprocessor, class_weight


# =============================================================================
# FASE 4 — MODELOS DE MACHINE LEARNING CLASICOS
# =============================================================================
def fase_4_modelos_ml(class_weight, fast=False):
    section("FASE 4 — Entrenamiento de los 4 modelos ML clasicos"
            + ("  [modo FAST]" if fast else ""))

    data = np.load(DATA_DIR / "preprocessed.npz", allow_pickle=True)
    X_train, y_train = data["X_train"], data["y_train"]
    X_val,   y_val   = data["X_val"],   data["y_val"]
    X_test,  y_test  = data["X_test"],  data["y_test"]
    feature_names = data["feature_names"].tolist()
    scale_pos = (y_train == 0).sum() / (y_train == 1).sum()

    # Hiperparametros segun modo
    if fast:
        n_rf, max_d_rf  = 150, 12     # menos arboles y profundidad
        max_iter_hgb    = 150
        n_xgb           = 200
    else:
        n_rf, max_d_rf  = 400, 15
        max_iter_hgb    = 300
        n_xgb           = 400

    modelos = {
        "LogisticRegression": LogisticRegression(
            max_iter=1000, solver="lbfgs",
            class_weight="balanced", random_state=SEED),
        "RandomForest": RandomForestClassifier(
            n_estimators=n_rf, max_depth=max_d_rf, min_samples_leaf=10,
            n_jobs=-1, class_weight="balanced", random_state=SEED),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=max_iter_hgb, learning_rate=0.05, max_depth=8,
            l2_regularization=1.0, early_stopping=True,
            validation_fraction=0.15, n_iter_no_change=20,
            class_weight="balanced", random_state=SEED),
        "XGBoost": XGBClassifier(
            n_estimators=n_xgb, max_depth=6, learning_rate=0.1,
            subsample=0.9, colsample_bytree=0.9,
            scale_pos_weight=scale_pos, eval_metric="logloss",
            n_jobs=-1, random_state=SEED, tree_method="hist"),
    }

    resultados = []
    proba_val_d, proba_test_d = {}, {}

    for nombre, modelo in modelos.items():
        t0 = time.time()
        modelo.fit(X_train, y_train)
        t_train = time.time() - t0
        proba_val  = modelo.predict_proba(X_val)[:, 1]
        proba_test = modelo.predict_proba(X_test)[:, 1]
        pred_test  = (proba_test >= 0.5).astype(int)
        cm = confusion_matrix(y_test, pred_test)
        m = {
            "modelo":    nombre,
            "accuracy":  round(accuracy_score(y_test, pred_test), 4),
            "precision": round(precision_score(y_test, pred_test, zero_division=0), 4),
            "recall":    round(recall_score(y_test, pred_test), 4),
            "f1":        round(f1_score(y_test, pred_test), 4),
            "auc_roc":   round(roc_auc_score(y_test, proba_test), 4),
            "avg_prec":  round(average_precision_score(y_test, proba_test), 4),
            "tiempo_s":  round(t_train, 2),
            "TN": int(cm[0,0]), "FP": int(cm[0,1]),
            "FN": int(cm[1,0]), "TP": int(cm[1,1]),
        }
        resultados.append(m)
        proba_val_d[nombre]  = proba_val
        proba_test_d[nombre] = proba_test
        joblib.dump(modelo, MODELS_DIR / f"{nombre.lower()}.joblib")
        print(f"  {nombre:25s} t={t_train:6.2f}s  F1={m['f1']:.4f}  AUC={m['auc_roc']:.4f}  "
              f"Rec={m['recall']:.4f}  Pre={m['precision']:.4f}")

    df_metrics = pd.DataFrame(resultados).sort_values("f1", ascending=False).reset_index(drop=True)
    df_metrics.to_csv(TABLES_DIR / "09_metricas_ml.csv", index=False)
    ganador = df_metrics.iloc[0]
    print(f"\n  Ganador ML: {ganador['modelo']}  F1={ganador['f1']:.4f}")

    # Figura 10: matriz de confusion del ganador
    nombre_g = ganador["modelo"]
    proba_g  = proba_test_d[nombre_g]
    pred_g   = (proba_g >= 0.5).astype(int)
    cm_g     = confusion_matrix(y_test, pred_g)
    fig, ax = plt.subplots(figsize=(7, 6))
    labels = np.array([
        [f"TN\n{cm_g[0,0]:,}\n({cm_g[0,0]/cm_g.sum()*100:.1f} %)",
         f"FP\n{cm_g[0,1]:,}\n({cm_g[0,1]/cm_g.sum()*100:.1f} %)"],
        [f"FN\n{cm_g[1,0]:,}\n({cm_g[1,0]/cm_g.sum()*100:.1f} %)",
         f"TP\n{cm_g[1,1]:,}\n({cm_g[1,1]/cm_g.sum()*100:.1f} %)"]])
    sns.heatmap(cm_g, annot=labels, fmt="", cmap="Blues",
                xticklabels=["Predicho 0", "Predicho 1"],
                yticklabels=["Real 0", "Real 1"], cbar=False, ax=ax,
                annot_kws={"fontsize": 12, "fontweight": "bold"})
    ax.set_title(f"Matriz de confusion — {nombre_g} (ganador ML)\n"
                 f"F1={ganador['f1']:.4f}  AUC={ganador['auc_roc']:.4f}")
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "10_confusion_best_ml.png")
    plt.close()

    # Figura 11: feature importance combinada RF + XGBoost
    rf  = joblib.load(MODELS_DIR / "randomforest.joblib")
    xgb = joblib.load(MODELS_DIR / "xgboost.joblib")
    df_imp = pd.DataFrame({
        "RandomForest": rf.feature_importances_,
        "XGBoost":      xgb.feature_importances_,
    }, index=feature_names)
    df_imp["mean"] = df_imp.mean(axis=1)
    df_imp = df_imp.sort_values("mean", ascending=False)
    df_imp.to_csv(TABLES_DIR / "10_feature_importance.csv")

    top15 = df_imp.head(15)
    fig, ax = plt.subplots(figsize=(10, 8))
    y_pos = np.arange(len(top15)); w = 0.4
    ax.barh(y_pos - w/2, top15["RandomForest"], w, label="RandomForest",
            color="#2E86AB", edgecolor="black")
    ax.barh(y_pos + w/2, top15["XGBoost"], w, label="XGBoost",
            color="#E63946", edgecolor="black")
    # Resaltar features engineered en amarillo
    for i, n in enumerate(top15.index):
        if "n_mut" in n or "n_com" in n:
            ax.axhspan(i - 0.5, i + 0.5, color="#FFD700", alpha=0.15, zorder=0)
    ax.set_yticks(y_pos); ax.set_yticklabels(top15.index)
    ax.invert_yaxis()
    ax.set_xlabel("Importancia (gain / Gini)")
    ax.set_title("Top 15 features — features engineered destacadas en amarillo")
    ax.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "11_feature_importance.png")
    plt.close()

    # SHAP beeswarm sobre RandomForest (limita a 1000 ejemplos para velocidad)
    try:
        import shap
        explainer   = shap.TreeExplainer(rf)
        sample      = X_test[:1000]
        shap_values = explainer.shap_values(sample)
        # En clasificacion binaria, devuelve lista o array [n_classes,...]
        sv = shap_values[1] if isinstance(shap_values, list) else shap_values
        if sv.ndim == 3:                 # (n_samples, n_features, n_classes)
            sv = sv[:, :, 1]
        plt.figure(figsize=(10, 8))
        shap.summary_plot(sv, sample, feature_names=feature_names,
                          show=False, max_display=15)
        plt.tight_layout()
        plt.savefig(FIGS_DIR / "12_shap_beeswarm.png")
        plt.close()
        print("  ✓ SHAP beeswarm generado")
    except Exception as e:
        print(f"  ⚠ SHAP omitido: {e}")

    # Figura 13: ROC + PR de los 4 ML
    colores = {"LogisticRegression": "#1D3557", "RandomForest": "#2E86AB",
               "HistGradientBoosting": "#F4A261", "XGBoost": "#E63946"}
    fig, (ax_roc, ax_pr) = plt.subplots(1, 2, figsize=(14, 6))
    for n, proba in proba_test_d.items():
        fpr, tpr, _ = roc_curve(y_test, proba)
        ax_roc.plot(fpr, tpr, color=colores[n], lw=2,
                    label=f"{n} (AUC={roc_auc_score(y_test, proba):.4f})")
        pr, rc, _ = precision_recall_curve(y_test, proba)
        ax_pr.plot(rc, pr, color=colores[n], lw=2,
                   label=f"{n} (AP={average_precision_score(y_test, proba):.4f})")
    ax_roc.plot([0,1], [0,1], "k--", lw=1, alpha=0.5)
    ax_roc.set_xlabel("False Positive Rate"); ax_roc.set_ylabel("Recall (TPR)")
    ax_roc.set_title("Curvas ROC — 4 modelos ML (test)")
    ax_roc.legend(loc="lower right", fontsize=9)
    ax_pr.axhline(y_test.mean(), color="black", linestyle="--", lw=1, alpha=0.5,
                  label=f"Baseline ({y_test.mean():.3f})")
    ax_pr.set_xlabel("Recall"); ax_pr.set_ylabel("Precision")
    ax_pr.set_title("Curvas Precision-Recall — 4 modelos ML")
    ax_pr.legend(loc="upper right", fontsize=9)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "13_roc_pr_ml.png")
    plt.close()

    # Figura 14: validacion contra modelo generativo declarado en el metadata
    pesos_reales = {
        "mut_BRCA1": 2.0, "mut_TP53": 1.8, "fumador": 1.5, "mut_KRAS": 1.4,
        "glucosa": 1.2, "obesidad": 1.1, "mut_EGFR": 1.0, "hemoglobina": 0.9,
        "mut_PIK3CA": 0.8, "leucocitos": 0.7, "mut_BRAF": 0.6,
        "hipertension": 0.5, "edad": 0.4, "actividad_fisica": 1.2,
    }
    df_val = df_imp[["mean"]].copy()
    df_val.columns = ["importancia_aprendida"]
    df_val["peso_generativo_abs"] = df_val.index.map(lambda v: abs(pesos_reales.get(v, 0)))
    mask = df_val["peso_generativo_abs"] > 0
    rho_gen, _ = spearmanr(df_val.loc[mask, "importancia_aprendida"],
                            df_val.loc[mask, "peso_generativo_abs"])
    print(f"\n  Validacion generativa: Spearman ρ = {rho_gen:.4f}")
    df_val.head(15).round(4).to_csv(TABLES_DIR / "11_validacion_generativa.csv")

    fig, ax = plt.subplots(figsize=(10, 7))
    sub = df_val.loc[mask]
    ax.scatter(sub["peso_generativo_abs"], sub["importancia_aprendida"],
               s=120, color="#2E86AB", edgecolor="black", alpha=0.85)
    for var, row in sub.iterrows():
        ax.annotate(var, (row["peso_generativo_abs"], row["importancia_aprendida"]),
                    xytext=(7, 4), textcoords="offset points", fontsize=9)
    # Marcar features engineered como estrellas
    for var in ["n_mutaciones", "n_comorbilidades"]:
        if var in df_val.index:
            ag = 1.3 if var == "n_mutaciones" else 0.8
            ax.scatter(ag, df_val.loc[var, "importancia_aprendida"],
                       s=250, color="#E63946", edgecolor="black", marker="*", zorder=10)
            ax.annotate(f"{var}\n(engineered)",
                        (ag, df_val.loc[var, "importancia_aprendida"]),
                        xytext=(8, -12), textcoords="offset points",
                        fontsize=9, color="#E63946", fontweight="bold")
    ax.set_xlabel("|peso generativo real| (declarado en metadata)")
    ax.set_ylabel("Importancia aprendida (media RF + XGBoost)")
    ax.set_title(f"Validacion: ranking aprendido vs pesos generativos reales\n"
                 f"Spearman ρ = {rho_gen:.3f}   |   ★ = features engineered")
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "14_aprendido_vs_generativo.png")
    plt.close()

    np.savez_compressed(
        DATA_DIR / "predictions_ml.npz",
        proba_val=np.column_stack([proba_val_d[n]  for n in modelos]),
        proba_test=np.column_stack([proba_test_d[n] for n in modelos]),
        model_names=np.array(list(modelos.keys())),
        y_val=y_val, y_test=y_test,
    )
    return df_metrics


# =============================================================================
# FASE 5 — RED NEURONAL MULTICAPA (MLP)
# =============================================================================
# =============================================================================
# FASE 5 — RED NEURONAL MULTICAPA (MLP) en PyTorch
# =============================================================================
def fase_5_mlp(class_weight, fast=False):
    """Entrena la Red Neuronal Multicapa con PyTorch.

    Esta funcion importa torch internamente (lazy), de forma que las otras
    fases pueden ejecutarse sin tener PyTorch instalado.
    """
    section("FASE 5 — Red Neuronal Multicapa (MLP) con PyTorch"
            + ("  [modo FAST]" if fast else ""))

    # ---------- Imports diferidos de PyTorch ----------
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    torch.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark     = False

    # ---------- Definicion del modelo (clase interna) ----------
    class MLPClassifier(nn.Module):
        """Red MLP con 3 capas ocultas + BatchNorm + Dropout.

        Arquitectura:
            Input(N) -> Dense(240) -> BN -> ReLU -> Drop(0.25)
                     -> Dense(120) -> BN -> ReLU -> Drop(0.25)
                     -> Dense(60)  -> BN -> ReLU -> Drop(0.20)
                     -> Dense(1)   -> (Sigmoid aplicado fuera)
        """
        def __init__(self, n_features, hidden=(240, 120, 60),
                     dropout=(0.25, 0.25, 0.20)):
            super().__init__()
            layers_seq = []
            prev = n_features
            for h, d in zip(hidden, dropout):
                layers_seq.append(nn.Linear(prev, h))
                layers_seq.append(nn.BatchNorm1d(h))
                layers_seq.append(nn.ReLU(inplace=True))
                layers_seq.append(nn.Dropout(d))
                prev = h
            layers_seq.append(nn.Linear(prev, 1))
            self.net = nn.Sequential(*layers_seq)
            # Inicializacion He (equivalente a HeNormal de Keras)
            for m in self.modules():
                if isinstance(m, nn.Linear):
                    nn.init.kaiming_normal_(m.weight, nonlinearity="relu")
                    if m.bias is not None:
                        nn.init.zeros_(m.bias)

        def forward(self, x):
            return self.net(x).squeeze(-1)   # logits (sin sigmoid)

    class _EarlyStop:
        """Equivalente a Keras EarlyStopping(restore_best_weights=True)."""
        def __init__(self, patience=12):
            self.patience    = patience
            self.best_loss   = float("inf")
            self.bad_epochs  = 0
            self.best_state  = None
            self.should_stop = False

        def step(self, val_loss, model):
            if val_loss < self.best_loss:
                self.best_loss  = val_loss
                self.bad_epochs = 0
                self.best_state = {k: v.detach().clone()
                                    for k, v in model.state_dict().items()}
            else:
                self.bad_epochs += 1
                if self.bad_epochs >= self.patience:
                    self.should_stop = True

        def restore(self, model):
            if self.best_state is not None:
                model.load_state_dict(self.best_state)

    # ---------- Cargar datos preprocesados ----------

    data = np.load(DATA_DIR / "preprocessed.npz", allow_pickle=True)
    X_train = data["X_train"].astype("float32"); y_train = data["y_train"].astype("float32")
    X_val   = data["X_val"].astype("float32");   y_val   = data["y_val"].astype("float32")
    X_test  = data["X_test"].astype("float32");  y_test  = data["y_test"].astype("float32")
    N_FEATURES = X_train.shape[1]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"\n  Dispositivo: {device}")

    # Tensores en device
    X_train_t = torch.from_numpy(X_train).to(device)
    y_train_t = torch.from_numpy(y_train).to(device)
    X_val_t   = torch.from_numpy(X_val).to(device)
    y_val_t   = torch.from_numpy(y_val).to(device)
    X_test_t  = torch.from_numpy(X_test).to(device)

    # DataLoader con generador reproducible
    g = torch.Generator(); g.manual_seed(SEED)
    train_loader = DataLoader(TensorDataset(X_train_t, y_train_t),
                              batch_size=128, shuffle=True, generator=g)

    # Modelo
    DENSE = (240, 120, 60); DROP = (0.25, 0.25, 0.20)
    model = MLPClassifier(N_FEATURES, hidden=DENSE, dropout=DROP).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"  Arquitectura: {N_FEATURES} -> {DENSE[0]} -> {DENSE[1]} -> {DENSE[2]} -> 1")
    print(f"  Parametros:   {n_params:,}  (objetivo del PDF: 46.913)")

    # Loss con class_weight (pos_weight reescala la clase positiva)
    pos_weight = torch.tensor([float(class_weight[1] / class_weight[0])], device=device)
    criterion  = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    # Optimizador + scheduler
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=6, min_lr=1e-6)

    EPOCHS    = 60 if fast else 200      # modo rapido limita epocas
    PATIENCE  = 8 if fast else 12
    stopper   = _EarlyStop(patience=PATIENCE)

    print(f"  Entrenando: max {EPOCHS} epocas, early-stop patience={PATIENCE}...")
    history = {"loss": [], "val_loss": [], "accuracy": [], "val_accuracy": [],
               "auc":  [], "val_auc":  []}
    t0 = time.time()

    for epoch in range(1, EPOCHS + 1):
        # ----- Train -----
        model.train()
        loss_sum, correct, total = 0.0, 0, 0
        for xb, yb in train_loader:
            optimizer.zero_grad()
            logits = model(xb)
            loss   = criterion(logits, yb)
            loss.backward()
            optimizer.step()
            loss_sum += loss.item() * xb.size(0)
            with torch.no_grad():
                preds = (torch.sigmoid(logits) >= 0.5).float()
                correct += (preds == yb).sum().item()
                total   += xb.size(0)
        train_loss = loss_sum / total
        train_acc  = correct / total

        # ----- Eval -----
        model.eval()
        with torch.no_grad():
            train_proba = torch.sigmoid(model(X_train_t)).cpu().numpy()
            train_auc   = roc_auc_score(y_train, train_proba)
            val_logits  = model(X_val_t)
            val_loss    = criterion(val_logits, y_val_t).item()
            val_proba   = torch.sigmoid(val_logits).cpu().numpy()
            val_acc     = accuracy_score(y_val, (val_proba >= 0.5).astype(int))
            val_auc     = roc_auc_score(y_val, val_proba)

        history["loss"].append(train_loss);    history["val_loss"].append(val_loss)
        history["accuracy"].append(train_acc); history["val_accuracy"].append(val_acc)
        history["auc"].append(train_auc);      history["val_auc"].append(val_auc)

        # Scheduler basado en val_loss
        scheduler.step(val_loss)

        # Early stopping
        stopper.step(val_loss, model)
        if stopper.should_stop:
            print(f"  Epoch {epoch}: early stopping (mejor val_loss={stopper.best_loss:.4f})")
            stopper.restore(model)
            break
    else:
        stopper.restore(model)

    t_train  = time.time() - t0
    n_epocas = len(history["loss"])
    print(f"  Entrenamiento: {n_epocas} epocas, {t_train:.1f}s")

    # ===== Predicciones finales =====
    model.eval()
    with torch.no_grad():
        proba_val  = torch.sigmoid(model(X_val_t)).cpu().numpy()
        proba_test = torch.sigmoid(model(X_test_t)).cpu().numpy()

    # Guardar modelo
    torch.save({
        "model_state_dict": model.state_dict(),
        "architecture":     {"n_features": N_FEATURES, "hidden": DENSE, "dropout": DROP},
        "n_params":         n_params,
    }, MODELS_DIR / "mlp_best.pt")

    # ===== Threshold tuning SOBRE VALIDACION =====
    print("  Threshold tuning sobre VALIDACION (rango [0.10, 0.90] paso 0.01)...")
    rows = []
    for t in np.arange(0.10, 0.91, 0.01):
        pred = (proba_val >= t).astype(int)
        rows.append({
            "threshold": round(float(t), 2),
            "precision": precision_score(y_val, pred, zero_division=0),
            "recall":    recall_score(y_val, pred, zero_division=0),
            "f1":        f1_score(y_val, pred, zero_division=0),
        })
    df_thr = pd.DataFrame(rows).round(4)
    df_thr.to_csv(TABLES_DIR / "13_threshold_search.csv", index=False)
    best_idx = df_thr["f1"].idxmax()
    best_threshold = float(df_thr.loc[best_idx, "threshold"])
    print(f"  Umbral optimo (val): {best_threshold:.2f}  F1_val={df_thr.loc[best_idx,'f1']:.4f}")

    # ===== Evaluacion final SOBRE TEST =====
    def eval_t(t, etiqueta):
        pred = (proba_test >= t).astype(int)
        cm = confusion_matrix(y_test, pred)
        return {"modelo": f"MLP ({etiqueta})", "threshold": round(t, 2),
                "accuracy":  round(accuracy_score(y_test, pred), 4),
                "precision": round(precision_score(y_test, pred, zero_division=0), 4),
                "recall":    round(recall_score(y_test, pred), 4),
                "f1":        round(f1_score(y_test, pred), 4),
                "auc_roc":   round(roc_auc_score(y_test, proba_test), 4),
                "avg_prec":  round(average_precision_score(y_test, proba_test), 4),
                "TN": int(cm[0,0]), "FP": int(cm[0,1]),
                "FN": int(cm[1,0]), "TP": int(cm[1,1])}

    met_50  = eval_t(0.50,           "umbral=0.50")
    met_opt = eval_t(best_threshold, f"umbral={best_threshold:.2f}")
    df_mlp = pd.DataFrame([met_50, met_opt])
    df_mlp.to_csv(TABLES_DIR / "12_metricas_mlp.csv", index=False)
    print("METRICAS MLP:")
    print(df_mlp.to_string(index=False))

    # ===== Figuras MLP =====
    # Figura 15: arquitectura visual
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 6); ax.axis("off")
    blocks = [("Input", N_FEATURES, "#1D3557"),
              ("Dense 1", DENSE[0], "#2E86AB"), ("BN+Drop", DENSE[0], "#A8DADC"),
              ("Dense 2", DENSE[1], "#2E86AB"), ("BN+Drop", DENSE[1], "#A8DADC"),
              ("Dense 3", DENSE[2], "#2E86AB"), ("BN+Drop", DENSE[2], "#A8DADC"),
              ("Output",  1,        "#E63946")]
    xpos = np.linspace(0.5, 9.5, len(blocks))
    for i, (n, u, col) in enumerate(blocks):
        h = 0.4 + 2.5 * (u / max(DENSE))
        ax.add_patch(plt.Rectangle((xpos[i]-0.45, 3-h/2), 0.9, h,
                                    facecolor=col, edgecolor="black", linewidth=1.2))
        ax.text(xpos[i], 5.0, n, ha="center", fontsize=10, fontweight="bold")
        ax.text(xpos[i], 0.7, f"{u}", ha="center", fontsize=10)
        if i < len(blocks)-1:
            ax.annotate("", xy=(xpos[i+1]-0.5, 3), xytext=(xpos[i]+0.5, 3),
                        arrowprops=dict(arrowstyle="->", color="gray", lw=1.2))
    ax.text(5, 5.7, f"Arquitectura MLP (PyTorch) — {n_params:,} parametros  (objetivo ≈ 46.913)",
            ha="center", fontsize=13, fontweight="bold")
    ax.text(5, 0.15, "Dropout: 0.25 -> 0.25 -> 0.20   |   Activaciones: ReLU -> ReLU -> ReLU -> Sigmoid",
            ha="center", fontsize=9, style="italic")
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "15_arquitectura_mlp.png")
    plt.close()

    # Figura 16: curvas de entrenamiento
    hist = pd.DataFrame(history)
    hist.to_csv(TABLES_DIR / "12b_history_mlp.csv", index_label="epoch")
    fig, axes = plt.subplots(1, 3, figsize=(17, 5))
    for ax, (k_t, k_v, lab) in zip(axes, [
        ("loss",     "val_loss",     "Loss (BCEWithLogits)"),
        ("accuracy", "val_accuracy", "Accuracy"),
        ("auc",      "val_auc",      "AUC-ROC")]):
        ax.plot(hist[k_t], label="Train",      color="#2E86AB", lw=2)
        ax.plot(hist[k_v], label="Validation", color="#E63946", lw=2)
        ax.set_xlabel("Epoca"); ax.set_ylabel(lab); ax.legend(); ax.grid(alpha=0.3)
        ax.set_title(lab.split(" ")[0] + " por epoca")
    plt.suptitle(f"Curvas de entrenamiento — {n_epocas} epocas (PyTorch)", fontsize=13, y=1.00)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "16_curvas_entrenamiento.png")
    plt.close()

    # Figura 17: threshold tuning
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.plot(df_thr["threshold"], df_thr["precision"], label="Precision", color="#1D3557", lw=2)
    ax.plot(df_thr["threshold"], df_thr["recall"],    label="Recall",    color="#E63946", lw=2)
    ax.plot(df_thr["threshold"], df_thr["f1"],        label="F1",        color="#2E86AB", lw=2.5)
    ax.axvline(best_threshold, color="black", linestyle="--", lw=1.5,
               label=f"Optimo: {best_threshold:.2f}  (F1={df_thr.loc[best_idx,'f1']:.4f})")
    ax.axvline(0.50, color="gray", linestyle=":", lw=1, alpha=0.7, label="Defecto: 0.50")
    ax.set_xlabel("Umbral de clasificacion"); ax.set_ylabel("Metrica")
    ax.set_title("Threshold tuning sobre VALIDACION (sin data leakage)")
    ax.legend(loc="lower center", ncol=4); ax.grid(alpha=0.3)
    ax.set_xlim(0.1, 0.9)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "17_threshold_tuning.png")
    plt.close()

    # Figura 18: matrices de confusion
    pred_50  = (proba_test >= 0.50).astype(int)
    pred_opt = (proba_test >= best_threshold).astype(int)
    cm_50    = confusion_matrix(y_test, pred_50)
    cm_opt   = confusion_matrix(y_test, pred_opt)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    for ax, cm, lab, f1v in [
        (axes[0], cm_50,  "Umbral 0.50 (defecto)",    met_50["f1"]),
        (axes[1], cm_opt, f"Umbral {best_threshold:.2f} (optimo)", met_opt["f1"])
    ]:
        labels = np.array([
            [f"TN\n{cm[0,0]:,}\n({cm[0,0]/cm.sum()*100:.1f} %)",
             f"FP\n{cm[0,1]:,}\n({cm[0,1]/cm.sum()*100:.1f} %)"],
            [f"FN\n{cm[1,0]:,}\n({cm[1,0]/cm.sum()*100:.1f} %)",
             f"TP\n{cm[1,1]:,}\n({cm[1,1]/cm.sum()*100:.1f} %)"]])
        sns.heatmap(cm, annot=labels, fmt="", cmap="Blues",
                    xticklabels=["Pred 0", "Pred 1"], yticklabels=["Real 0", "Real 1"],
                    cbar=False, ax=ax, annot_kws={"fontsize":11, "fontweight":"bold"})
        ax.set_title(f"MLP — {lab}\nF1 = {f1v:.4f}", fontsize=11)
    plt.suptitle("Matrices de confusion del MLP sobre test", fontsize=13, y=1.02)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "18_confusion_mlp.png")
    plt.close()

    # Persistencia
    np.savez_compressed(
        DATA_DIR / "predictions_mlp.npz",
        proba_val=proba_val, proba_test=proba_test,
        y_val=y_val.astype(np.int64), y_test=y_test.astype(np.int64),
        best_threshold=np.array(best_threshold),
        history_loss=np.array(history["loss"]),
        history_val_loss=np.array(history["val_loss"]),
        history_accuracy=np.array(history["accuracy"]),
        history_val_accuracy=np.array(history["val_accuracy"]),
        history_auc=np.array(history["auc"]),
        history_val_auc=np.array(history["val_auc"]),
    )
    return df_mlp, best_threshold


# =============================================================================
# FASE 6 — COMPARATIVA GLOBAL ML vs MLP
# =============================================================================
def fase_6_comparativa(best_threshold):
    section("FASE 6 — Comparativa global ML vs MLP")

    ml  = np.load(DATA_DIR / "predictions_ml.npz",  allow_pickle=True)
    mlp = np.load(DATA_DIR / "predictions_mlp.npz", allow_pickle=True)
    y_test = ml["y_test"]
    assert np.array_equal(y_test, mlp["y_test"]), "y_test inconsistente"

    ml_names = ml["model_names"].tolist()

    def calc_metricas(nombre, proba, t=0.5):
        pred = (proba >= t).astype(int)
        cm = confusion_matrix(y_test, pred)
        return {"modelo": nombre, "threshold": round(t, 2),
                "precision": round(precision_score(y_test, pred, zero_division=0), 4),
                "recall":    round(recall_score(y_test, pred), 4),
                "f1":        round(f1_score(y_test, pred), 4),
                "auc_roc":   round(roc_auc_score(y_test, proba), 4),
                "avg_prec":  round(average_precision_score(y_test, proba), 4),
                "accuracy":  round(accuracy_score(y_test, pred), 4),
                "TN": int(cm[0,0]), "FP": int(cm[0,1]),
                "FN": int(cm[1,0]), "TP": int(cm[1,1])}

    filas = []
    for i, n in enumerate(ml_names):
        filas.append(calc_metricas(n, ml["proba_test"][:, i], 0.5))
    filas.append(calc_metricas("MLP (umbral 0.50)", mlp["proba_test"], 0.50))
    filas.append(calc_metricas(f"MLP (umbral {best_threshold:.2f})",
                                mlp["proba_test"], best_threshold))

    df = pd.DataFrame(filas).sort_values("f1", ascending=False).reset_index(drop=True)
    df.insert(0, "rank", df.index + 1)
    df.to_csv(TABLES_DIR / "14_ranking_final.csv", index=False)

    # Resumen ejecutivo: sin MLP@0.5 (solo el optimo)
    df_resumen = df[~df["modelo"].str.contains("MLP \\(umbral 0\\.50\\)", regex=True)] \
                   .reset_index(drop=True)
    df_resumen["rank"] = df_resumen.index + 1
    df_resumen.to_csv(TABLES_DIR / "15_resumen_ejecutivo.csv", index=False)
    print("\nRANKING FINAL (por F1):")
    print(df_resumen[["rank","modelo","f1","auc_roc","precision","recall"]].to_string(index=False))

    # Diccionario de probabilidades por modelo (para curvas)
    proba_dict = {n: ml["proba_test"][:, i] for i, n in enumerate(ml_names)}
    proba_dict["MLP"] = mlp["proba_test"]
    colores = {"LogisticRegression":"#1D3557", "RandomForest":"#2E86AB",
               "HistGradientBoosting":"#F4A261", "XGBoost":"#E63946", "MLP":"#6A0DAD"}

    # Figura 19: barchart
    modelos_plot = df_resumen["modelo"].tolist()
    metricas      = ["precision","recall","f1","auc_roc"]
    metricas_lab  = ["Precision","Recall","F1","AUC-ROC"]
    fig, ax = plt.subplots(figsize=(13, 6.5))
    x = np.arange(len(modelos_plot)); width = 0.20
    for i, (m, lab) in enumerate(zip(metricas, metricas_lab)):
        vals = df_resumen[m].values
        cg = ["#1D3557","#E63946","#2E86AB","#F4A261"][i]
        bars = ax.bar(x + (i-1.5)*width, vals, width, label=lab,
                       color=cg, edgecolor="black", linewidth=0.6)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.012,
                    f"{v:.3f}", ha="center", fontsize=8, fontweight="bold")
    labels_clean = [m.replace(" (umbral 0.50)","")
                     .replace(f" (umbral {best_threshold:.2f})","*") for m in modelos_plot]
    ax.set_xticks(x); ax.set_xticklabels(labels_clean, rotation=15, ha="right")
    ax.set_ylabel("Valor de la metrica")
    ax.set_title("Comparativa de los 5 modelos (test, 10.001 pacientes)\n"
                 f"* MLP con umbral optimo encontrado en validacion ({best_threshold:.2f})")
    ax.set_ylim(0, 1.0); ax.legend(loc="upper right", ncol=4); ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "19_barchart_metricas.png")
    plt.close()

    # Figura 20: ROC superpuestas
    fig, ax = plt.subplots(figsize=(9, 7))
    for n, p in proba_dict.items():
        fpr, tpr, _ = roc_curve(y_test, p)
        lw = 3 if n=="MLP" else 2
        ax.plot(fpr, tpr, color=colores[n], lw=lw,
                label=f"{n} (AUC={roc_auc_score(y_test, p):.4f})")
    ax.plot([0,1], [0,1], "k--", lw=1, alpha=0.5, label="Clasificador aleatorio")
    ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate (Recall)")
    ax.set_title("Curvas ROC — comparativa global de los 5 modelos (test)")
    ax.legend(loc="lower right"); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "20_roc_global.png")
    plt.close()

    # Figura 21: PR superpuestas
    fig, ax = plt.subplots(figsize=(9, 7))
    prev = y_test.mean()
    for n, p in proba_dict.items():
        pr, rc, _ = precision_recall_curve(y_test, p)
        lw = 3 if n=="MLP" else 2
        ax.plot(rc, pr, color=colores[n], lw=lw,
                label=f"{n} (AP={average_precision_score(y_test, p):.4f})")
    ax.axhline(prev, color="black", linestyle="--", lw=1, alpha=0.6,
               label=f"Baseline aleatorio (prev={prev:.3f})")
    pred_opt = (mlp["proba_test"] >= best_threshold).astype(int)
    p_op = precision_score(y_test, pred_opt, zero_division=0)
    r_op = recall_score(y_test, pred_opt)
    ax.scatter(r_op, p_op, s=200, color=colores["MLP"], edgecolor="black",
               zorder=10, marker="*",
               label=f"MLP @ {best_threshold:.2f}\n(P={p_op:.3f}, R={r_op:.3f})")
    ax.set_xlabel("Recall"); ax.set_ylabel("Precision")
    ax.set_title("Curvas Precision-Recall — comparativa global (test)")
    ax.legend(loc="upper right", fontsize=9); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "21_pr_global.png")
    plt.close()

    # Figura 22: PR zoom con iso-F1
    fig, ax = plt.subplots(figsize=(9, 7))
    for n, p in proba_dict.items():
        pr, rc, _ = precision_recall_curve(y_test, p)
        lw = 2.5 if n=="MLP" else 1.8
        ax.plot(rc, pr, color=colores[n], lw=lw, alpha=0.7, label=n)
        pred05 = (p >= 0.5).astype(int)
        ax.scatter(recall_score(y_test, pred05),
                   precision_score(y_test, pred05, zero_division=0),
                   s=80, color=colores[n], edgecolor="black", zorder=5)
    ax.scatter(r_op, p_op, s=300, color=colores["MLP"], edgecolor="black",
               zorder=10, marker="*", label=f"MLP @ {best_threshold:.2f} (optimo)")
    for fs in [0.4, 0.5, 0.55, 0.6, 0.65]:
        x_l = np.linspace(0.01, 1, 100)
        with np.errstate(divide="ignore", invalid="ignore"):
            y_l = fs * x_l / (2*x_l - fs)
        valid = (y_l > 0) & (y_l <= 1)
        ax.plot(x_l[valid], y_l[valid], color="gray", alpha=0.25, linestyle=":", lw=1)
    ax.set_xlabel("Recall"); ax.set_ylabel("Precision")
    ax.set_title("Zoom: punto operativo de cada modelo\n"
                 "● = umbral 0.5  |  ★ = MLP umbral optimo  |  Lineas grises: iso-F1")
    ax.set_xlim(0.45, 0.85); ax.set_ylim(0.40, 0.65)
    ax.legend(loc="upper right", fontsize=9); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "22_pr_zoom_operating_point.png")
    plt.close()

    # Figura 23: calibracion
    fig, ax = plt.subplots(figsize=(9, 7))
    for n, p in proba_dict.items():
        fp, mp = calibration_curve(y_test, p, n_bins=10, strategy="quantile")
        lw = 2.5 if n=="MLP" else 1.8
        ax.plot(mp, fp, marker="o", color=colores[n], lw=lw, label=n, markersize=7)
    ax.plot([0,1], [0,1], "k--", lw=1, label="Calibracion perfecta")
    ax.set_xlabel("Probabilidad media predicha (por decil)")
    ax.set_ylabel("Fraccion real de positivos en el decil")
    ax.set_title("Curva de calibracion — ¿son fiables las probabilidades?")
    ax.legend(loc="upper left"); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "23_calibracion.png")
    plt.close()

    print("\n  Brier scores (menor = mejor calibrado):")
    for n, p in proba_dict.items():
        print(f"    {n:25s}: {brier_score_loss(y_test, p):.4f}")

    # Figura 24: ranking visual
    fig, ax = plt.subplots(figsize=(11, 6))
    ax.axis("off")
    df_rk = df_resumen[["rank","modelo","f1","auc_roc","precision","recall"]].copy()
    df_rk.columns = ["#", "Modelo", "F1 ★", "AUC-ROC", "Precision", "Recall"]
    tbl = ax.table(cellText=df_rk.values.tolist(),
                    colLabels=df_rk.columns.tolist(),
                    cellLoc="center", loc="center",
                    colColours=["#1D3557"]*len(df_rk.columns))
    tbl.auto_set_font_size(False); tbl.set_fontsize(11); tbl.scale(1.0, 2.2)
    for ci in range(len(df_rk.columns)):
        tbl[(0, ci)].get_text().set_color("white")
        tbl[(0, ci)].get_text().set_fontweight("bold")
    for ci in range(len(df_rk.columns)):
        tbl[(1, ci)].set_facecolor("#A8DADC")
        tbl[(1, ci)].get_text().set_fontweight("bold")
    ax.set_title("Ranking final de los 5 modelos (ordenado por F1, metrica principal)",
                 fontsize=14, fontweight="bold", pad=20)
    plt.tight_layout()
    plt.savefig(FIGS_DIR / "24_ranking_visual.png")
    plt.close()
    return df


# =============================================================================
# MAIN — Orquestador del pipeline completo
# =============================================================================
def main():
    # ===== Argumentos de linea de comandos =====
    import argparse
    parser = argparse.ArgumentParser(
        description="Pipeline completo de prediccion de cancer (UAX 2025/26).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modos de uso:
  python cancer_pipeline.py              -> Ejecucion normal (cache por fase activado)
  python cancer_pipeline.py --force      -> Forzar re-ejecucion de TODAS las fases
  python cancer_pipeline.py --fast       -> Modo rapido (menos arboles, menos epocas)

Por defecto, si los modelos ya estan en `models/` se reutilizan y solo se
regeneran tablas y figuras finales. La ejecucion completa desde cero tarda
~4-5 min en CPU; con cache es practicamente instantanea (<10 s).
        """)
    parser.add_argument("--force", action="store_true",
                        help="Forzar re-ejecucion completa (ignora cache)")
    parser.add_argument("--fast",  action="store_true",
                        help="Modo rapido: menos arboles y menos epocas (~2 min)")
    args = parser.parse_args()

    print("\n" + "=" * 78)
    print(" CASO PRACTICO — Prediccion de diagnostico de cancer")
    print(" UAX · Ingenieria Matematica · IA · 2025/26")
    print("=" * 78)
    print(f"\n  Directorio raiz: {ROOT}")
    print(f"  Seed:            {SEED}")
    print(f"  Backend MLP:     PyTorch (cudnn.deterministic = True)")
    modo = ("FORCE (re-entrenar todo)" if args.force
            else "FAST (rapido)"        if args.fast
            else "normal (con cache por fase)")
    print(f"  Modo:            {modo}")
    t_start = time.time()

    def cached(path):
        """Devuelve True si el artefacto existe y no se ha pedido --force."""
        return Path(path).exists() and not args.force

    # ===== FASE 1: carga + EDA =====
    if cached(DATA_DIR / "df_merged.csv"):
        print("\n  [cache] FASE 1 saltada: cargando df_merged.csv")
        df = pd.read_csv(DATA_DIR / "df_merged.csv")
    else:
        df = fase_1_carga_y_eda()

    # ===== FASE 2: seleccion + feature engineering =====
    if cached(DATA_DIR / "df_features.csv") and cached(TABLES_DIR / "06_feature_metadata.json"):
        print("  [cache] FASE 2 saltada: cargando df_features.csv")
        df_features = pd.read_csv(DATA_DIR / "df_features.csv")
        with open(TABLES_DIR / "06_feature_metadata.json", encoding="utf-8") as f:
            meta = json.load(f)
    else:
        df_features, meta = fase_2_seleccion_y_engineering(df)

    # ===== FASE 3: preprocesado =====
    if (cached(DATA_DIR / "preprocessed.npz") and
        cached(MODELS_DIR / "preprocessor.joblib") and
        cached(TABLES_DIR / "07_class_weight.json")):
        print("  [cache] FASE 3 saltada: cargando preprocessed.npz")
        with open(TABLES_DIR / "07_class_weight.json") as f:
            class_weight = {int(k): float(v) for k, v in json.load(f).items()}
    else:
        _, class_weight = fase_3_preprocesamiento(df_features, meta)

    # ===== FASE 4: 4 modelos ML clasicos =====
    ml_cached = all([
        cached(MODELS_DIR / "randomforest.joblib"),
        cached(MODELS_DIR / "xgboost.joblib"),
        cached(MODELS_DIR / "logisticregression.joblib"),
        cached(MODELS_DIR / "histgradientboosting.joblib"),
        cached(DATA_DIR / "predictions_ml.npz"),
    ])
    if ml_cached:
        print("  [cache] FASE 4 saltada: 4 modelos ML ya entrenados")
    else:
        fase_4_modelos_ml(class_weight, fast=args.fast)

    # ===== FASE 5: MLP en PyTorch =====
    if cached(MODELS_DIR / "mlp_best.pt") and cached(DATA_DIR / "predictions_mlp.npz"):
        print("  [cache] FASE 5 saltada: MLP PyTorch ya entrenado")
        mlp_data = np.load(DATA_DIR / "predictions_mlp.npz", allow_pickle=True)
        best_t = float(mlp_data["best_threshold"])
    else:
        _, best_t = fase_5_mlp(class_weight, fast=args.fast)

    # ===== FASE 6: comparativa (siempre se regenera, tarda <5s) =====
    df_final = fase_6_comparativa(best_t)

    # ===== Resumen final =====
    elapsed = time.time() - t_start
    section("PIPELINE COMPLETO — Resumen")

    print(f"\n  Tiempo total de ejecucion: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"\n  RANKING FINAL:")
    print(df_final[["rank","modelo","f1","auc_roc","precision","recall"]].to_string(index=False))

    ganador = df_final.iloc[0]
    print(f"\n  MODELO RECOMENDADO: {ganador['modelo']}")
    print(f"     F1        = {ganador['f1']:.4f}")
    print(f"     AUC-ROC   = {ganador['auc_roc']:.4f}")
    print(f"     Precision = {ganador['precision']:.4f}")
    print(f"     Recall    = {ganador['recall']:.4f}")

    print(f"\n  Artefactos generados:")
    print(f"     · {len(list(FIGS_DIR.glob('*.png')))} figuras en figs/")
    print(f"     · {len(list(TABLES_DIR.glob('*')))} tablas en tables/")
    print(f"     · {len(list(MODELS_DIR.glob('*')))} modelos en models/")
    print("\n  Para generar el PPTX final ejecuta:  node generar_slides.js")
    print("=" * 78)


if __name__ == "__main__":
    main()
