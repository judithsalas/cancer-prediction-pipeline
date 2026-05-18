# CLAUDE.md — Memoria del proyecto

Proyecto: **Caso práctico — Predicción de diagnóstico de cáncer**  
UAX · Ingeniería Matemática · Inteligencia Artificial · Curso 2025/26

---

## 🎯 Resumen rápido

Pipeline ML+MLP sobre 50.001 pacientes sintéticos (6 CSV unidos por `paciente_id`) para predecir `cancer` (prevalencia 19,29 %, ratio 4,18:1). Métrica principal F1 sobre clase 1. Modelo ganador: **RandomForest con feature engineering, F1 = 0,5719, AUC = 0,8367**.

## 🚀 Cómo se ejecuta

```bash
python cancer_pipeline.py   # ejecuta las 6 fases del pipeline de tirón (~7 min CPU)
node generar_slides.js      # regenera el PPTX del entregable
```

## 🗂️ Estructura

- `cancer_pipeline.py` — script Python único con todo el pipeline (6 fases)
- `generar_slides.js` — script Node.js que produce las 7 diapositivas del PPTX
- `data/` — 6 CSV originales + datasets derivados
- `figs/` — 24 figuras PNG (EDA, ML, MLP, comparativa)
- `tables/` — 22 tablas CSV/JSON con todas las métricas
- `models/` — 6 modelos serializados (preprocessor + 4 ML + MLP)
- `Entregable_5_diapositivas.pptx` y `.pdf` — entregable final

## 🧠 Decisiones técnicas

**Exclusiones**: paciente_id, alcohol (varianza 0), coste_total / coste_farmaco / dias_hospital / num_ingresos / vive (data leakage).

**Feature engineering**: `n_mutaciones` (suma de 7 mut_*) y `n_comorbilidades` (suma de 6 binarias clínicas). Ambas con monotonía verificada contra el target.

**Pipeline**:
- Split estratificado 64/16/20 (test intacto hasta evaluación final).
- StandardScaler + OrdinalEncoder + OneHotEncoder(drop=first) — todo dentro de un `ColumnTransformer` ajustado solo en train.
- 36 columnas tras encoding.
- `class_weight="balanced"` calculado solo sobre y_train.

**Modelos ML (umbral 0.5)**:
- LogisticRegression, RandomForest (n=400, depth=15), HistGradientBoosting, XGBoost.

**MLP**: arquitectura 240→120→60 con BatchNorm + Dropout (0.25/0.25/0.20), ReLU+Sigmoid, ~46.801 parámetros. 3 callbacks: EarlyStopping(patience=12), ReduceLROnPlateau(factor=0.5, patience=6), ModelCheckpoint. Threshold tuning estricto sobre validación.

**SEED = 42** global, `TF_DETERMINISTIC_OPS = 1`.

## 📈 Resultados

| Modelo | F1 | AUC-ROC |
|---|---:|---:|
| **RandomForest** | **0,5719** | 0,8367 |
| MLP @ 0,64 | 0,5615 | 0,8356 |
| HistGradientBoosting | 0,5527 | 0,8409 |
| LogisticRegression | 0,5526 | 0,8417 |
| XGBoost | 0,5423 | 0,8221 |

**Validación generativa**: Spearman ρ = 0,862 entre ranking aprendido y pesos del metadata oficial.

## 📦 Entregable final

7 diapositivas con diseño coherente (fondo cream + banda navy + statCallouts):
1. Portada
2. Objetivo y datos
3. Resultados ML
4. MLP
5. Comparativa global
6. Viabilidad y modelo recomendado
7. Conclusiones finales

Generadas con pptxgenjs (Node.js).
