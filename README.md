# Caso Práctico — Predicción de Diagnóstico de Cáncer

**UAX · Ingeniería Matemática · Inteligencia Artificial · Curso 2025/26**

Pipeline completo de Machine Learning + Red Neuronal Multicapa para anticipar el diagnóstico de cáncer a partir de datos clínicos, bioquímicos, genéticos, sociodemográficos, de estilo de vida y económicos de **50.001 pacientes** repartidos en 6 colecciones CSV.

---

## 🚀 Cómo ejecutar (un único comando)

```bash
python cancer_pipeline.py
```

Eso es todo. El script `cancer_pipeline.py` ejecuta las 6 fases del trabajo de principio a fin: carga los 6 CSV, hace el EDA, selecciona features, entrena 4 modelos ML clásicos, entrena la red neuronal MLP en PyTorch, hace la comparativa global y guarda todos los artefactos.

### ⚡ Modos de ejecución (caché inteligente)

| Comando | Qué hace | Tiempo |
|---|---|---:|
| `python cancer_pipeline.py` | **Normal**: caché por fase. Si ya hay modelos, los reutiliza. | ~5 s (caché) / ~4 min (1ª vez) |
| `python cancer_pipeline.py --fast` | **Rápido**: menos árboles, menos épocas. Métricas casi idénticas. | ~1-2 min |
| `python cancer_pipeline.py --force` | **Re-entrenar todo** ignorando caché. | ~4-5 min |
| `python cancer_pipeline.py --help` | Ver todos los argumentos. | instantáneo |

Cada fase comprueba si su output ya existe; si sí, lo carga y salta. **La primera ejecución tarda unos minutos, pero cualquier re-ejecución posterior es prácticamente instantánea.**

### Dependencias

```bash
pip install pandas scikit-learn matplotlib seaborn xgboost torch joblib scipy shap
```

> **Nota**: la Red Neuronal Multicapa está implementada en **PyTorch** (requisito del profesor).

Para regenerar las diapositivas del entregable:

```bash
node generar_slides.js
```

Requiere Node.js + pptxgenjs (`npm install pptxgenjs`).

---

## 📊 Resumen ejecutivo

| Dimensión | Valor |
|---|---:|
| Pacientes | 50.001 |
| Variables tras merge | 38 |
| Variables predictoras finales | 32 (30 originales + 2 engineered) |
| Valores nulos | 0 |
| Prevalencia cáncer | 19,29 % |
| Ratio desbalance neg : pos | 4,18 : 1 |
| Test set (intacto hasta el final) | 10.001 muestras |
| Métrica principal | F1 (clase 1) + AUC-ROC |
| **Modelo recomendado** | **RandomForest con feature engineering** |
| **F1 final** | **0,5719** |
| **AUC-ROC final** | **0,8367** |
| Validación contra modelo generativo (Spearman ρ) | 0,862 |

---

## 🗂️ Estructura del proyecto

```
caso_cancer/
├── README.md                          ← este documento
├── CLAUDE.md                          ← memoria del proyecto
├── metadata_dataset_cancer.md         ← metadata oficial del profesor
│
├── cancer_pipeline.py                 ⭐ SCRIPT PRINCIPAL — ejecutar este
├── generar_slides.js                  Genera Entregable_5_diapositivas.pptx
│
├── Entregable_5_diapositivas.pptx     ⭐ ENTREGABLE PRINCIPAL
├── Entregable_5_diapositivas.pdf
│
├── data/                              CSV originales + datasets derivados
│   ├── CASOCANCER_*.csv (6 archivos)
│   ├── df_merged.csv                  (todos unidos por paciente_id)
│   ├── df_features.csv                (con feature engineering)
│   ├── preprocessed.npz               (matrices listas para entrenar)
│   ├── predictions_ml.npz             (probabilidades de los 4 ML)
│   └── predictions_mlp.npz            (probabilidades del MLP)
│
├── figs/                              24 figuras en PNG
│   ├── 01-09  EDA y preprocesamiento
│   ├── 10-14  Modelos ML clásicos
│   ├── 15-18  Red neuronal MLP
│   └── 19-24  Comparativa global
│
├── tables/                            22 tablas CSV/JSON con todas las métricas
│   ├── 00-08  Resúmenes EDA y splits
│   ├── 09-11  Métricas y feature importance de ML
│   ├── 12-13  Métricas y threshold tuning del MLP
│   └── 14-15  Ranking final y resumen ejecutivo
│
└── models/                            Modelos serializados
    ├── preprocessor.joblib            (ColumnTransformer ajustado en train)
    ├── logisticregression.joblib
    ├── randomforest.joblib            ⭐ ganador
    ├── histgradientboosting.joblib
    ├── xgboost.joblib
    └── mlp_best.keras                 (red neuronal en formato Keras)
```

---

## 🧠 Decisiones técnicas clave

### Reproducibilidad estricta
- `SEED = 42` global (Python, NumPy, TensorFlow, PYTHONHASHSEED)
- `TF_DETERMINISTIC_OPS = 1`

### Exclusiones cuantificadas (Fase 2)

| Variable | Razón | Evidencia |
|---|---|---:|
| `paciente_id` | Identificador | — |
| `alcohol` | **Varianza cero** (vale 1 siempre) | std = 0 |
| `coste_total` | Data leakage (post-diagnóstico) | r = +0,89 |
| `dias_hospital` | Data leakage | r = +0,88 |
| `coste_farmaco` | Data leakage | r = +0,85 |
| `num_ingresos` | Data leakage | r = +0,64 |
| `vive` | Data leakage (mortalidad = desenlace) | confirmado en metadata |

### Feature engineering

Dos features compuestas con monotonía verificada con el target:

| Feature | Construcción | Monotonía | Spearman ρ |
|---|---|---|---:|
| `n_mutaciones` | suma de las 7 binarias `mut_*` | 0→9,6 % · 1→23,7 % · 2→42,8 % · 3→60,9 % · **4→81,4 %** | 0,294 |
| `n_comorbilidades` | suma de 6 binarias clínicas | 0→9,5 % · 1→15,4 % · 2→22,7 % · 3→30,7 % · 4→39,2 % · **5→43,2 %** | 0,185 |

`n_mutaciones` se convierte en la feature **#1 más importante** según RandomForest y XGBoost.

### Pipeline de preprocesamiento (Fase 3)

- Split estratificado **64 / 16 / 20** — prevalencia 19,287 % en los 3 splits (spread 0,001 pp).
- **StandardScaler** ajustado SOLO en train.
- **OrdinalEncoder** con orden clínico explícito.
- **OneHotEncoder(drop="first")** para nominales.
- **class_weight balanced** sobre y_train: `{0: 0,62, 1: 2,59}`.
- 36 columnas tras encoding.

### Threshold tuning sin leakage (Fase 5)

1. Probabilidades sobre VALIDACIÓN.
2. Barrido [0,10; 0,90] paso 0,01.
3. Umbral óptimo = arg max F1 sobre validación.
4. Aplicado UNA SOLA VEZ sobre test.

---

## 📈 Resultados consolidados

### Ranking final (test, ordenado por F1)

| # | Modelo | F1 | AUC-ROC | Precision | Recall |
|---|---|---:|---:|---:|---:|
| 🥇 1 | **RandomForest** | **0,5719** | 0,8367 | 0,4990 | 0,6698 |
| 🥈 2 | MLP (umbral 0,64) | 0,5615 | 0,8356 | 0,5138 | 0,6190 |
| 🥉 3 | HistGradientBoosting | 0,5527 | 0,8409 | 0,4365 | 0,7532 |
| 4 | LogisticRegression | 0,5526 | 0,8417 | 0,4343 | 0,7595 |
| 5 | XGBoost | 0,5423 | 0,8221 | 0,4890 | 0,6086 |

### Modelo recomendado: **RandomForest**

- **F1 = 0,5719** (el mejor de los 5)
- **AUC-ROC = 0,8367**
- Matriz de confusión: TN = 6.775, FP = 1.297, FN = 637, TP = 1.292
- Interpretación clínica: **identifica al 67 % de los pacientes con cáncer con un 50 % de precisión**

### Alternativa interpretable: LogisticRegression

Si se prioriza interpretabilidad: AUC = 0,8417 (el más alto) + coeficientes log-odds legibles.

---

## ⭐ Validación contra el modelo generativo

El metadata oficial declara que `cancer` se genera con `P(cancer=1) = σ(β₀ + Σ wₖ·xₖ + ε)`, β₀ = −4,0, ε ~ N(0; 0,8) y 15 factores explícitos (mut_BRCA1 = +2,0, mut_TP53 = +1,8, fumador = +1,5, etc.).

**Spearman ρ = 0,862** entre el ranking de importancia aprendido por los modelos y los pesos generativos verdaderos. El modelo aprende los predictores correctos, sin atajos espurios.

---

## ⚠️ Limitaciones del sistema actual

- **Dataset sintético** (logística + ruido N(0; 0,8)): sociodemográficas sin señal real.
- **Sin datos longitudinales** ni imágenes (mamografía, TC).
- **Calibración sobre-confiada** (efecto del `class_weight`): aplicar Platt scaling en despliegue real.
- **Coste asimétrico FP vs FN no parametrizado**: en oncología un FN suele costar más que un FP.
- **Rol como herramienta de apoyo**: cribado, NO diagnóstico. El médico tiene la decisión final.

## 🔬 Datos adicionales que mejorarían el modelo

- **Marcadores tumorales**: CA-125, CEA, PSA, AFP, HE4, CA 15-3, CA 19-9.
- **Imagenología**: mamografía digital, TC tórax/abdomen, RM hepática.
- **Datos longitudinales**: evolución de bioquímicos en los últimos 12-24 meses.
- **Historial familiar** oncológico de primer grado.
- **Exposición ambiental**: amianto, radón, radiación ionizante.

---

## 📜 Stack técnico

- Python 3.12
- pandas 2.x · scikit-learn 1.8 · NumPy 2.x
- XGBoost 3.2
- TensorFlow 2.x (Keras)
- matplotlib + seaborn (visualización)
- SHAP (interpretabilidad)
- Node.js + pptxgenjs (generación del PPTX)

Dataset sintético del profesor (caso práctico UAX 2025/26). Modelo generativo declarado en `metadata_dataset_cancer.md`.
