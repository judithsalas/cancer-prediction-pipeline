# Caso Práctico: Predicción de Diagnóstico de Cáncer

**Estudio de viabilidad mediante Machine Learning y Redes Neuronales**

UAX · Ingeniería Matemática · Inteligencia Artificial · Curso 2025/26

---

## Descripción

Pipeline completo de Machine Learning + Red Neuronal Multicapa (MLP) para anticipar el diagnóstico de cáncer a partir de datos clínicos, bioquímicos, genéticos, sociodemográficos y de estilo de vida de **50.001 pacientes** repartidos en 6 colecciones CSV.

El estudio compara cuatro modelos clásicos (Logistic Regression, Random Forest, HistGradientBoosting, XGBoost) con una red neuronal multicapa de tres capas ocultas implementada en PyTorch, y recomienda el modelo más adecuado para un sistema de cribado clínico.

---

## Ejecución

### Requisitos

- Python 3.10 o superior
- Dependencias:

```bash
pip install pandas scikit-learn matplotlib seaborn xgboost torch joblib scipy shap
```

### Cómo ejecutar el pipeline

```bash
python cancer_pipeline.py
```

El script ejecuta las seis fases del trabajo: carga y unión de los seis CSV, análisis exploratorio, selección de features y feature engineering, preprocesamiento, entrenamiento de los cuatro modelos ML clásicos, entrenamiento de la red neuronal MLP en PyTorch y comparativa global con generación de tablas y figuras.

### Sistema de caché para evaluación rápida

El proyecto incluye los modelos ya entrenados en la carpeta `models/`. El script detecta automáticamente los artefactos existentes y salta las fases ya completadas.

| Escenario | Tiempo aproximado |
|---|---:|
| Primera ejecución sobre el ZIP descomprimido | ~25 segundos (solo entrena el MLP) |
| Re-ejecución posterior (caché completa) | ~3 segundos |
| `python cancer_pipeline.py --force` (auditoría desde cero) | ~4-5 minutos |
| `python cancer_pipeline.py --fast` (re-entrenamiento ligero) | ~1-2 minutos |

Para auditar el entrenamiento completo desde cero, ejecutar `python cancer_pipeline.py --force`. Esto borra el caché y vuelve a entrenar los cinco modelos.

---

## Resumen ejecutivo

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
| Modelo recomendado | **MLP umbral 0,63 (PyTorch)** |
| F1 final | **0,5748** |
| AUC-ROC final | **0,8418** |
| Validación contra modelo generativo (Spearman ρ) | 0,862 |

---

## Estructura del proyecto

```
caso_cancer/
├── README.md                          documentación del proyecto
├── metadata_dataset_cancer.md         metadata oficial del dataset
│
├── cancer_pipeline.py                 SCRIPT PRINCIPAL (ejecutar con python)
│
├── Entregable_5_diapositivas.pptx     entregable principal (PowerPoint)
├── Entregable_5_diapositivas.pdf      entregable principal (PDF)
│
├── data/                              CSV originales y datasets derivados
│   ├── CASOCANCER_*.csv (6 archivos)
│   ├── df_merged.csv                  los 6 CSV unidos por paciente_id
│   ├── df_features.csv                con feature engineering aplicado
│   ├── preprocessed.npz               matrices listas para entrenar
│   ├── predictions_ml.npz             probabilidades de los 4 ML
│   └── predictions_mlp.npz            probabilidades del MLP
│
├── figs/                              25 figuras en PNG
│   ├── 01-09  EDA y preprocesamiento
│   ├── 10-14  Modelos ML clásicos
│   ├── 15-18  Red neuronal MLP
│   └── 19-24  Comparativa global
│
├── tables/                            22 tablas con todas las métricas
│
└── models/                            Modelos serializados
    ├── preprocessor.joblib            ColumnTransformer ajustado en train
    ├── logisticregression.joblib
    ├── randomforest.joblib
    ├── histgradientboosting.joblib
    ├── xgboost.joblib
    └── mlp_best.pt                    red neuronal en formato PyTorch
```

---

## Decisiones técnicas

### Reproducibilidad estricta

- `SEED = 42` global (Python, NumPy, PyTorch, `PYTHONHASHSEED`)
- `torch.backends.cudnn.deterministic = True`
- `torch.backends.cudnn.benchmark = False`

### Exclusiones de variables (Fase 2)

Siete variables se excluyen del conjunto de predictoras con justificación cuantitativa:

| Variable | Razón | Evidencia |
|---|---|---:|
| `paciente_id` | Identificador | — |
| `alcohol` | Varianza cero (vale 1 siempre) | std = 0 |
| `coste_total` | Data leakage (post-diagnóstico) | r = +0,89 |
| `dias_hospital` | Data leakage | r = +0,88 |
| `coste_farmaco` | Data leakage | r = +0,85 |
| `num_ingresos` | Data leakage | r = +0,64 |
| `vive` | Data leakage (mortalidad es desenlace) | confirmado en metadata |

### Feature engineering

Se construyen dos variables compuestas con monotonía verificada respecto al target:

| Feature | Construcción | Monotonía | Spearman ρ |
|---|---|---|---:|
| `n_mutaciones` | suma de las 7 binarias `mut_*` | 0→9,6 % · 1→23,7 % · 2→42,8 % · 3→60,9 % · **4→81,4 %** | 0,294 |
| `n_comorbilidades` | suma de 6 binarias clínicas | 0→9,5 % · 1→15,4 % · 2→22,7 % · 3→30,7 % · 4→39,2 % · **5→43,2 %** | 0,185 |

`n_mutaciones` se convierte en la feature más importante según Random Forest y XGBoost.

### Pipeline de preprocesamiento (Fase 3)

- Split estratificado **64 / 16 / 20** — prevalencia 19,287 % en los tres splits (spread 0,001 pp).
- StandardScaler ajustado únicamente en train.
- OrdinalEncoder con orden clínico explícito para variables ordinales.
- OneHotEncoder con `drop="first"` para variables nominales.
- `class_weight="balanced"` calculado sobre y_train: `{0: 0,62, 1: 2,59}`.
- 36 columnas tras encoding.

### Red Neuronal Multicapa (Fase 5)

- Implementación en PyTorch (`torch.nn`).
- Arquitectura: 36 → 240 → 120 → 60 → 1.
- BatchNorm + Dropout (0,25 / 0,25 / 0,20) entre capas ocultas.
- Activaciones ReLU + sigmoide final.
- Inicialización He (`kaiming_normal_`).
- Pérdida `BCEWithLogitsLoss` con `pos_weight` para manejar el desbalance.
- Optimizador Adam con `lr=1e-3`.
- `ReduceLROnPlateau` (factor 0,5, paciencia 6).
- Early Stopping con paciencia 12 y restauración de los mejores pesos.
- Aproximadamente 45.961 parámetros.

### Threshold tuning sin data leakage

1. Cálculo de probabilidades sobre el conjunto de **validación**.
2. Barrido de umbrales en [0,10; 0,90] con paso 0,01.
3. Selección del umbral que maximiza F1 sobre validación.
4. Aplicación una sola vez sobre el conjunto de test.

---

## Resultados consolidados

### Ranking final (test, ordenado por F1)

| # | Modelo | F1 | AUC-ROC | Precision | Recall |
|---|---|---:|---:|---:|---:|
| 1 | **MLP umbral 0,63 (PyTorch)** | **0,5748** | 0,8418 | 0,5305 | 0,6273 |
| 2 | RandomForest (+ feat eng) | 0,5719 | 0,8367 | 0,4990 | 0,6698 |
| 3 | HistGradientBoosting | 0,5527 | 0,8409 | 0,4365 | 0,7532 |
| 4 | LogisticRegression | 0,5526 | 0,8417 | 0,4343 | 0,7595 |
| 5 | XGBoost | 0,5423 | 0,8221 | 0,4890 | 0,6086 |

### Modelo recomendado: MLP umbral 0,63 (PyTorch)

- F1 = 0,5748 (el más alto de los cinco modelos).
- AUC-ROC = 0,8418.
- Matriz de confusión: TN = 7.001, FP = 1.071, FN = 719, TP = 1.210.
- Interpretación clínica: identifica al 63 % de los pacientes con cáncer con un 53 % de precisión.
- Hallazgo: la red neuronal supera ligeramente al mejor modelo clásico (Random Forest, F1 = 0,5719) tras threshold tuning estricto sobre validación.

### Alternativa interpretable: LogisticRegression

Si se prioriza la interpretabilidad del modelo, Logistic Regression ofrece el AUC más alto (0,8417) y coeficientes log-odds legibles.

---

## Validación contra el modelo generativo

El metadata oficial declara que `cancer` se genera con `P(cancer=1) = σ(β₀ + Σ wₖ·xₖ + ε)`, β₀ = −4,0, ε ~ N(0; 0,8) y 15 factores explícitos (mut_BRCA1 = +2,0, mut_TP53 = +1,8, fumador = +1,5, etc.).

La correlación de Spearman entre el ranking de importancia aprendido por los modelos y los pesos generativos verdaderos es ρ = 0,862. Los modelos aprenden los predictores correctos, sin atajos espurios derivados del data leakage.

---

## Limitaciones del sistema actual

- **Dataset sintético** generado mediante logística más ruido N(0; 0,8); las variables sociodemográficas no portan señal real.
- **Sin datos longitudinales** ni imágenes médicas (mamografía, TC, RM).
- **Calibración sobre-confiada** como efecto de `class_weight`. En despliegue real procedería aplicar Platt scaling.
- **Coste asimétrico FP vs FN no parametrizado**. En oncología un falso negativo suele costar más que un falso positivo.
- El sistema se concibe como **herramienta de cribado**, no de diagnóstico. La decisión clínica final corresponde al facultativo.

## Datos adicionales que mejorarían el modelo

- **Marcadores tumorales**: CA-125, CEA, PSA, AFP, HE4, CA 15-3, CA 19-9.
- **Imagenología**: mamografía digital, TC tórax/abdomen, RM hepática.
- **Datos longitudinales**: evolución de los bioquímicos en los últimos 12-24 meses.
- **Historial familiar** oncológico de primer grado.
- **Exposición ambiental**: amianto, radón, radiación ionizante.

---

## Stack técnico

- Python 3.10+
- pandas, NumPy, scikit-learn
- XGBoost
- PyTorch (red neuronal multicapa)
- matplotlib, seaborn (visualización)
- SHAP (interpretabilidad opcional)

Dataset sintético generado a partir del modelo declarado en `metadata_dataset_cancer.md`.
