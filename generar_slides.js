// =============================================================================
// CASO PRÁCTICO — Predicción de Diagnóstico de Cáncer
// UAX · Ingeniería Matemática · IA · 2025/26
// FASE 7 — Entregable: 5 diapositivas (PowerPoint)
//
// Paleta: Midnight Executive (navy + ice blue + accent rojo+morado)
// Tipografía: títulos Georgia + body Calibri
// Diseño: estructura "sandwich" (T+conclusión oscura, contenido claro)
// =============================================================================

const pptxgen = require("pptxgenjs");
const path    = require("path");

// ---------- Configuración base ----------------------------------------------
const FIGS = "./figs";
const pres = new pptxgen();
pres.layout      = "LAYOUT_WIDE";        // 13.3" × 7.5"
pres.author      = "Equipo UAX Ingenieria Matematica";
pres.title       = "Prediccion de Diagnostico de Cancer";
pres.subject     = "Estudio de viabilidad ML vs Red Neuronal MLP";
pres.company     = "UAX 2025/26";

// Paleta personalizada — Midnight Executive ajustada
const C = {
  navy:       "1E2761",   // fondo títulos / dark
  navyDeep:   "0F1A47",   // fondo conclusión
  iceBlue:    "CADCFC",   // texto secundario / fondos suaves
  white:      "FFFFFF",
  cream:      "F9FAFC",   // fondo contenido (alternativa al blanco)
  accentRed:  "E63946",   // resaltar puntos clave / warnings
  accentMlp:  "6A0DAD",   // color del MLP (morado)
  textDark:   "1A1A2E",
  textMid:    "475569",
  textLight:  "94A3B8",
  successGr:  "10B981",   // ✅ verde
  warningOr:  "F59E0B",   // ⚠ naranja
  grid:       "E2E8F0",
};

// ---------- Helpers ----------------------------------------------------------
function addPageHeader(slide, num, title, subtitle) {
  // Banda superior oscura (28% de la altura para títulos sustanciosos)
  slide.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 13.3, h: 1.1,
    fill: { color: C.navy }, line: { color: C.navy }
  });
  // Número de página dentro de círculo accent
  slide.addShape(pres.shapes.OVAL, {
    x: 0.45, y: 0.25, w: 0.6, h: 0.6,
    fill: { color: C.accentRed }, line: { color: C.accentRed }
  });
  slide.addText(String(num), {
    x: 0.45, y: 0.25, w: 0.6, h: 0.6,
    fontSize: 20, fontFace: "Georgia", color: C.white,
    bold: true, align: "center", valign: "middle", margin: 0,
  });
  // Título
  slide.addText(title, {
    x: 1.2, y: 0.15, w: 11.5, h: 0.5,
    fontSize: 24, fontFace: "Georgia", color: C.white, bold: true,
    align: "left", valign: "middle", margin: 0,
  });
  // Subtítulo
  if (subtitle) {
    slide.addText(subtitle, {
      x: 1.2, y: 0.62, w: 11.5, h: 0.35,
      fontSize: 12, fontFace: "Calibri", color: C.iceBlue,
      italic: true, align: "left", valign: "middle", margin: 0,
    });
  }
  // Pie de página
  slide.addText("UAX · Ingenieria Matematica · IA 2025/26   |   Caso de uso: Prediccion de cancer",
    { x: 0.5, y: 7.2, w: 12.3, h: 0.25,
      fontSize: 8, fontFace: "Calibri", color: C.textLight, align: "left", margin: 0 });
  slide.addText(`Slide ${num} / 5`,
    { x: 0.5, y: 7.2, w: 12.3, h: 0.25,
      fontSize: 8, fontFace: "Calibri", color: C.textLight, align: "right", margin: 0 });
}

function statCallout(slide, x, y, w, h, value, label, valueColor = C.accentRed) {
  // Tarjeta con métrica grande
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h, fill: { color: C.white },
    line: { color: C.grid, width: 1 },
    shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 90, opacity: 0.08 },
  });
  // Barra lateral coloreada
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w: 0.10, h, fill: { color: valueColor }, line: { color: valueColor },
  });
  slide.addText(value, {
    x: x + 0.15, y: y + 0.05, w: w - 0.20, h: h * 0.55,
    fontSize: 28, fontFace: "Georgia", color: valueColor, bold: true,
    align: "center", valign: "middle", margin: 0,
    shrinkText: true,
  });
  slide.addText(label, {
    x: x + 0.15, y: y + h * 0.55, w: w - 0.20, h: h * 0.40,
    fontSize: 10, fontFace: "Calibri", color: C.textMid,
    align: "center", valign: "middle", margin: 0,
  });
}


// ============================================================================
//  SLIDE 0 — PORTADA (mismo lenguaje visual que el resto)
// ============================================================================
let s = pres.addSlide();
s.background = { color: C.cream };

// Banda superior navy (igual altura que el header de las otras slides)
s.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 13.3, h: 1.1,
  fill: { color: C.navy }, line: { color: C.navy }
});
// Etiqueta de curso/asignatura en la banda navy
s.addText("CASO PRACTICO · INTELIGENCIA ARTIFICIAL · CURSO 2025-2026",
  { x: 0.5, y: 0.35, w: 12.3, h: 0.4,
    fontSize: 13, fontFace: "Calibri", color: C.iceBlue,
    bold: true, charSpacing: 4, align: "left", valign: "middle", margin: 0 });

// Bloque central: título grande
s.addText("Prediccion de diagnostico\nde cancer",
  { x: 0.5, y: 1.6, w: 12.3, h: 1.85, fontSize: 52, fontFace: "Georgia",
    color: C.navy, bold: true, align: "left", valign: "top", margin: 0 });

// Línea decorativa roja bajo el título (motivo del statCallout)
s.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 3.55, w: 1.5, h: 0.08,
  fill: { color: C.accentRed }, line: { color: C.accentRed },
});

// Subtítulo
s.addText("Estudio de viabilidad mediante Machine Learning y Redes Neuronales",
  { x: 0.5, y: 3.75, w: 12.3, h: 0.45,
    fontSize: 18, fontFace: "Georgia", color: C.textMid,
    italic: true, align: "left", margin: 0 });

// 3 statCallouts: misma estética que slides 1, 3
statCallout(s, 0.5,  4.85, 4.0, 1.4, "50.001", "Pacientes analizados",          C.navy);
statCallout(s, 4.65, 4.85, 4.0, 1.4, "5",      "Modelos comparados (4 ML + MLP)", C.accentRed);
statCallout(s, 8.80, 4.85, 4.0, 1.4, "0,5719", "F1 del modelo ganador",         C.warningOr);

// Pie idéntico al de las otras slides
s.addText("UAX · Ingenieria Matematica · IA 2025/26   |   Caso de uso: Prediccion de cancer",
  { x: 0.5, y: 7.2, w: 12.3, h: 0.25,
    fontSize: 8, fontFace: "Calibri", color: C.textLight, align: "left", margin: 0 });
s.addText("Portada",
  { x: 0.5, y: 7.2, w: 12.3, h: 0.25,
    fontSize: 8, fontFace: "Calibri", color: C.textLight, align: "right", margin: 0 });


// ============================================================================
//  SLIDE 1 — Objetivo y datos del proyecto
// ============================================================================
s = pres.addSlide();
s.background = { color: C.cream };
addPageHeader(s, 1, "Objetivo del proyecto y datos disponibles",
              "Estudio de viabilidad: ¿pueden los datos del hospital anticipar un diagnóstico de cáncer?");

// Texto descriptivo (panel izquierdo)
s.addText("El hospital recoge datos multimodales de 50.001 pacientes y necesita evaluar si son suficientes para anticipar un diagnostico de cancer mediante modelos de IA. Variable objetivo: cancer (0/1).",
  { x: 0.5, y: 1.35, w: 6.5, h: 0.85, fontSize: 13, fontFace: "Calibri",
    color: C.textDark, valign: "top", margin: 0, paraSpaceAfter: 4 });

// 3 callouts de métricas clave (debajo del texto)
statCallout(s, 0.5,  2.35, 2.05, 1.0, "50.001", "Pacientes",          C.navy);
statCallout(s, 2.65, 2.35, 2.05, 1.0, "19,29%", "Prevalencia cancer", C.accentRed);
statCallout(s, 4.80, 2.35, 2.20, 1.0, "4,18:1", "Ratio desbalance",   C.warningOr);

// Tabla de las 6 colecciones (panel izquierdo, debajo)
s.addText("Las 6 colecciones disponibles (unidas por paciente_id):",
  { x: 0.5, y: 3.5, w: 6.5, h: 0.3, fontSize: 12, fontFace: "Calibri",
    color: C.textDark, bold: true, margin: 0 });

const datosColecciones = [
  [{ text: "Coleccion",   options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 11 } },
   { text: "Contenido",   options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 11 } },
   { text: "# vars",       options: { bold: true, color: C.white, fill: { color: C.navy }, fontSize: 11 } }],
  ["01 BIOQUIMICOS",    "Marcadores en sangre (glucosa, hemoglobina, leucocitos...)",  "7"],
  ["02 CLINICOS",       "Comorbilidades + variable objetivo cancer",                    "7"],
  ["03 GENETICOS",      "Mutaciones oncologicas (BRCA1, TP53, KRAS, EGFR...)",          "7"],
  ["03 ECONOMICOS",     "Coste y uso del sistema (⚠ data leakage)",                     "5"],
  ["05 GENERALES",      "Habitos de vida (fumador, alcohol, actividad fisica)",         "4"],
  ["06 SOCIODEMOGRAFICOS","Edad, nivel educativo, zona, estado civil",                  "7"],
];

s.addTable(datosColecciones, {
  x: 0.5, y: 3.85, w: 6.5, h: 2.85,
  colW: [1.85, 4.05, 0.6],
  fontSize: 10, fontFace: "Calibri", color: C.textDark,
  border: { type: "solid", pt: 0.5, color: C.grid },
  rowH: 0.4,
  valign: "middle",
});

// Panel derecho: figura de selección de features (data leakage)
s.addText("Seleccion de features con justificacion empirica",
  { x: 7.3, y: 1.3, w: 5.6, h: 0.35, fontSize: 13, fontFace: "Calibri",
    color: C.navy, bold: true, margin: 0 });

s.addText("30 INCLUIDAS · 7 EXCLUIDAS · 1 TARGET",
  { x: 7.3, y: 1.65, w: 5.6, h: 0.30, fontSize: 11, fontFace: "Calibri",
    color: C.textMid, italic: true, margin: 0 });

s.addImage({
  path: `${FIGS}/06_feature_selection.png`,
  x: 7.3, y: 1.95, w: 5.5, h: 4.7,
  sizing: { type: "contain", w: 5.5, h: 4.7 },
});

// Caja de leakage (parte inferior derecha)
s.addShape(pres.shapes.RECTANGLE, {
  x: 7.3, y: 6.7, w: 5.5, h: 0.45,
  fill: { color: C.accentRed }, line: { color: C.accentRed },
});
s.addText("⚠ EXCLUIDAS: 5 por data leakage (coste_total, dias_hospital, coste_farmaco, num_ingresos, vive) · alcohol (varianza 0) · paciente_id",
  { x: 7.3, y: 6.7, w: 5.5, h: 0.45, fontSize: 9, fontFace: "Calibri",
    color: C.white, bold: true, align: "center", valign: "middle", margin: 0.05 });


// ============================================================================
//  SLIDE 2 — Resultados de los modelos de ML clásicos
// ============================================================================
s = pres.addSlide();
s.background = { color: C.cream };
addPageHeader(s, 2, "Resultados de los modelos ML clasicos",
              "Cuatro modelos entrenados sobre 32.000 muestras y evaluados sobre 10.001 de test");

// Tabla de métricas (izquierda)
s.addText("Comparativa de los 4 modelos (umbral 0,50) — con feature engineering",
  { x: 0.5, y: 1.35, w: 6.4, h: 0.3, fontSize: 13, fontFace: "Calibri",
    color: C.navy, bold: true, margin: 0 });

const tablaML = [
  [{ text: "#",         options: { bold: true, color: C.white, fill: { color: C.navy }, align: "center" } },
   { text: "Modelo",    options: { bold: true, color: C.white, fill: { color: C.navy } } },
   { text: "F1 ★",      options: { bold: true, color: C.white, fill: { color: C.navy }, align: "center" } },
   { text: "AUC-ROC",   options: { bold: true, color: C.white, fill: { color: C.navy }, align: "center" } },
   { text: "Precision", options: { bold: true, color: C.white, fill: { color: C.navy }, align: "center" } },
   { text: "Recall",    options: { bold: true, color: C.white, fill: { color: C.navy }, align: "center" } }],

  // RandomForest (ganador)
  [{ text: "1", options: { fill: { color: C.iceBlue }, bold: true, align: "center" } },
   { text: "RandomForest", options: { fill: { color: C.iceBlue }, bold: true } },
   { text: "0,5719", options: { fill: { color: C.iceBlue }, bold: true, align: "center", color: C.accentRed } },
   { text: "0,8367", options: { fill: { color: C.iceBlue }, align: "center" } },
   { text: "0,4990", options: { fill: { color: C.iceBlue }, align: "center" } },
   { text: "0,6698", options: { fill: { color: C.iceBlue }, align: "center" } }],

  [{ text: "2", options: { align: "center" } }, "HistGradientBoosting",
   { text: "0,5527", options: { align: "center" } },
   { text: "0,8409", options: { align: "center" } },
   { text: "0,4365", options: { align: "center" } },
   { text: "0,7532", options: { align: "center" } }],

  [{ text: "3", options: { align: "center" } }, "LogisticRegression",
   { text: "0,5526", options: { align: "center" } },
   { text: "0,8417", options: { align: "center" } },
   { text: "0,4343", options: { align: "center" } },
   { text: "0,7595", options: { align: "center" } }],

  [{ text: "4", options: { align: "center" } }, "XGBoost",
   { text: "0,5423", options: { align: "center" } },
   { text: "0,8221", options: { align: "center" } },
   { text: "0,4890", options: { align: "center" } },
   { text: "0,6086", options: { align: "center" } }],
];
s.addTable(tablaML, {
  x: 0.5, y: 1.7, w: 6.4, h: 2.1,
  colW: [0.4, 2.0, 1.0, 1.0, 1.0, 1.0],
  fontSize: 10, fontFace: "Calibri", color: C.textDark,
  border: { type: "solid", pt: 0.5, color: C.grid },
  rowH: 0.4, valign: "middle",
});

// Matriz de confusión del ganador
s.addText("Matriz de confusion · RandomForest (test)",
  { x: 0.5, y: 4.0, w: 6.4, h: 0.3, fontSize: 12, fontFace: "Calibri",
    color: C.navy, bold: true, margin: 0 });

s.addImage({
  path: `${FIGS}/10_confusion_best_ml.png`,
  x: 0.5, y: 4.3, w: 3.0, h: 2.7,
  sizing: { type: "contain", w: 3.0, h: 2.7 },
});

// Validación generativa al lado de la matriz
s.addText("Validacion contra modelo generativo del metadata",
  { x: 3.7, y: 4.3, w: 3.4, h: 0.3, fontSize: 11, fontFace: "Calibri",
    color: C.navy, bold: true, margin: 0 });

s.addText([
  { text: "Spearman ρ = ", options: { fontSize: 11, color: C.textMid } },
  { text: "0,862", options: { fontSize: 16, color: C.accentRed, bold: true } },
], { x: 3.7, y: 4.65, w: 3.4, h: 0.4, fontFace: "Georgia", margin: 0 });

s.addText("entre el ranking aprendido (sin feature engineering) y los pesos generativos REALES declarados en el metadata oficial.",
  { x: 3.7, y: 5.1, w: 3.4, h: 0.7, fontSize: 9, fontFace: "Calibri",
    color: C.textMid, italic: true, margin: 0, paraSpaceAfter: 2 });

s.addText("⇒ El modelo aprende los predictores CORRECTOS. Tras anadir n_mutaciones y n_comorbilidades, esta se convierte en la feature #1 mas importante (sustituye al atajo aprendido).",
  { x: 3.7, y: 5.8, w: 3.4, h: 1.15, fontSize: 9, fontFace: "Calibri",
    color: C.textDark, bold: true, margin: 0 });

// Curva ROC + PR (derecha)
s.addText("Curvas ROC y Precision-Recall (test)",
  { x: 7.3, y: 1.35, w: 5.6, h: 0.3, fontSize: 13, fontFace: "Calibri",
    color: C.navy, bold: true, margin: 0 });

s.addImage({
  path: `${FIGS}/13_roc_pr_ml.png`,
  x: 7.3, y: 1.7, w: 5.6, h: 2.6,
  sizing: { type: "contain", w: 5.6, h: 2.6 },
});

s.addText("Top 5 features aprendidas (RF + XGBoost)",
  { x: 7.3, y: 4.45, w: 5.6, h: 0.3, fontSize: 12, fontFace: "Calibri",
    color: C.navy, bold: true, margin: 0 });

s.addImage({
  path: `${FIGS}/14_aprendido_vs_generativo.png`,
  x: 7.3, y: 4.75, w: 5.6, h: 2.4,
  sizing: { type: "contain", w: 5.6, h: 2.4 },
});


// ============================================================================
//  SLIDE 3 — Resultados de la Red Neuronal MLP
// ============================================================================
s = pres.addSlide();
s.background = { color: C.cream };
addPageHeader(s, 3, "Red Neuronal Multicapa (MLP) — nucleo tecnico",
              "Arquitectura ≈ 46.913 parametros · regularizacion estricta · threshold tuning sin data leakage");

// Arquitectura (panel superior izquierdo)
s.addText("Arquitectura: Dense(240) → Dense(120) → Dense(60) → Dense(1)",
  { x: 0.5, y: 1.3, w: 6.4, h: 0.3, fontSize: 12, fontFace: "Calibri",
    color: C.navy, bold: true, margin: 0 });

s.addImage({
  path: `${FIGS}/15_arquitectura_mlp.png`,
  x: 0.5, y: 1.6, w: 6.4, h: 2.0,
  sizing: { type: "contain", w: 6.4, h: 2.0 },
});

// 3 callouts de configuración
statCallout(s, 0.5,  3.75, 2.0, 0.95, "46.801", "Parametros",        C.navy);
statCallout(s, 2.60, 3.75, 2.0, 0.95, "31",     "Epocas (EarlyStop)", C.successGr);
statCallout(s, 4.70, 3.75, 2.2, 0.95, "42 s",  "Tiempo (CPU)",       C.warningOr);

// Curvas entrenamiento
s.addText("Curvas de entrenamiento por epoca",
  { x: 0.5, y: 4.85, w: 6.4, h: 0.3, fontSize: 12, fontFace: "Calibri",
    color: C.navy, bold: true, margin: 0 });

s.addImage({
  path: `${FIGS}/16_curvas_entrenamiento.png`,
  x: 0.5, y: 5.15, w: 6.4, h: 1.95,
  sizing: { type: "contain", w: 6.4, h: 1.95 },
});

// Threshold tuning (panel derecho superior)
s.addText("Threshold tuning sobre VALIDACION (sin data leakage)",
  { x: 7.3, y: 1.3, w: 5.6, h: 0.3, fontSize: 12, fontFace: "Calibri",
    color: C.navy, bold: true, margin: 0 });

s.addImage({
  path: `${FIGS}/17_threshold_tuning.png`,
  x: 7.3, y: 1.6, w: 5.6, h: 2.4,
  sizing: { type: "contain", w: 5.6, h: 2.4 },
});

// Resultado final MLP vs RF (panel derecho inferior)
s.addText("Resultado final (test) · MLP vs mejor ML",
  { x: 7.3, y: 4.15, w: 5.6, h: 0.3, fontSize: 12, fontFace: "Calibri",
    color: C.navy, bold: true, margin: 0 });

const tablaMLP = [
  [{ text: "Modelo / config",         options: { bold: true, color: C.white, fill: { color: C.navy } } },
   { text: "F1 ★",        options: { bold: true, color: C.white, fill: { color: C.navy }, align: "center" } },
   { text: "AUC-ROC",     options: { bold: true, color: C.white, fill: { color: C.navy }, align: "center" } },
   { text: "Precision",   options: { bold: true, color: C.white, fill: { color: C.navy }, align: "center" } },
   { text: "Recall",      options: { bold: true, color: C.white, fill: { color: C.navy }, align: "center" } }],
  ["MLP umbral 0,50",
   { text: "0,5413", options: { align: "center" } },
   { text: "0,8337", options: { align: "center" } },
   { text: "0,4182", options: { align: "center" } },
   { text: "0,7672", options: { align: "center" } }],
  [{ text: "MLP umbral 0,64 (optimo)", options: { fill: { color: C.iceBlue }, bold: true } },
   { text: "0,5615", options: { fill: { color: C.iceBlue }, bold: true, align: "center", color: C.accentMlp } },
   { text: "0,8337", options: { fill: { color: C.iceBlue }, bold: true, align: "center" } },
   { text: "0,5138", options: { fill: { color: C.iceBlue }, bold: true, align: "center" } },
   { text: "0,6190", options: { fill: { color: C.iceBlue }, bold: true, align: "center" } }],
  [{ text: "RandomForest (GANADOR)", options: { fill: { color: "#FFE0B2" }, bold: true } },
   { text: "0,5719", options: { fill: { color: "#FFE0B2" }, bold: true, align: "center", color: C.accentRed } },
   { text: "0,8367", options: { fill: { color: "#FFE0B2" }, align: "center" } },
   { text: "0,4990", options: { fill: { color: "#FFE0B2" }, align: "center" } },
   { text: "0,6698", options: { fill: { color: "#FFE0B2" }, align: "center" } }],
];

s.addTable(tablaMLP, {
  x: 7.3, y: 4.5, w: 5.6, h: 1.5,
  colW: [2.4, 0.8, 0.8, 0.8, 0.8],
  fontSize: 10, fontFace: "Calibri", color: C.textDark,
  border: { type: "solid", pt: 0.5, color: C.grid },
  rowH: 0.36, valign: "middle",
});

// Caja con hallazgo honesto: feature eng ayudó a árboles, no al MLP
s.addShape(pres.shapes.RECTANGLE, {
  x: 7.3, y: 6.15, w: 5.6, h: 1.0,
  fill: { color: C.accentMlp }, line: { color: C.accentMlp }
});
s.addText([
  { text: "Hallazgo metodologico\n", options: { fontSize: 12, bold: true, color: C.white } },
  { text: "El feature engineering (n_mutaciones, n_comorbilidades) ", options: { fontSize: 9, color: C.iceBlue } },
  { text: "ayuda a los arboles pero no al MLP. RandomForest gana.", options: { fontSize: 9, color: C.iceBlue, italic: true } },
], { x: 7.3, y: 6.15, w: 5.6, h: 1.0, fontFace: "Calibri", align: "center", valign: "middle", margin: 0.1 });


// ============================================================================
//  SLIDE 4 — Comparativa global ML vs Red Neuronal
// ============================================================================
s = pres.addSlide();
s.background = { color: C.cream };
addPageHeader(s, 4, "Comparativa global: 4 ML vs Red Neuronal MLP",
              "Bar chart, curvas ROC y Precision-Recall superpuestas, ranking final");

// Bar chart (parte superior, ocupa todo el ancho)
s.addText("Comparativa de los 5 modelos · 4 metricas",
  { x: 0.5, y: 1.35, w: 12.3, h: 0.3, fontSize: 13, fontFace: "Calibri",
    color: C.navy, bold: true, margin: 0 });

s.addImage({
  path: `${FIGS}/19_barchart_metricas.png`,
  x: 0.5, y: 1.65, w: 7.5, h: 2.5,
  sizing: { type: "contain", w: 7.5, h: 2.5 },
});

// Curvas ROC y PR (derecha del bar chart)
s.addImage({
  path: `${FIGS}/20_roc_global.png`,
  x: 8.1, y: 1.65, w: 2.5, h: 2.5,
  sizing: { type: "contain", w: 2.5, h: 2.5 },
});
s.addImage({
  path: `${FIGS}/21_pr_global.png`,
  x: 10.7, y: 1.65, w: 2.5, h: 2.5,
  sizing: { type: "contain", w: 2.5, h: 2.5 },
});

// Ranking final (tabla, mitad inferior izquierda)
s.addText("Ranking final · ordenado por F1 (metrica principal)",
  { x: 0.5, y: 4.3, w: 7.5, h: 0.3, fontSize: 13, fontFace: "Calibri",
    color: C.navy, bold: true, margin: 0 });

const ranking = [
  [{ text: "#",          options: { bold: true, color: C.white, fill: { color: C.navy }, align: "center" } },
   { text: "Modelo",     options: { bold: true, color: C.white, fill: { color: C.navy } } },
   { text: "F1 ★",       options: { bold: true, color: C.white, fill: { color: C.navy }, align: "center" } },
   { text: "AUC-ROC",    options: { bold: true, color: C.white, fill: { color: C.navy }, align: "center" } },
   { text: "Precision",  options: { bold: true, color: C.white, fill: { color: C.navy }, align: "center" } },
   { text: "Recall",     options: { bold: true, color: C.white, fill: { color: C.navy }, align: "center" } }],
  // GANADOR: RandomForest con feature engineering
  [{ text: "1", options: { fill: { color: C.accentRed }, bold: true, color: C.white, align: "center" } },
   { text: "RandomForest (+ feat eng)", options: { fill: { color: C.accentRed }, bold: true, color: C.white } },
   { text: "0,5719", options: { fill: { color: C.accentRed }, bold: true, color: C.white, align: "center" } },
   { text: "0,8367", options: { fill: { color: C.accentRed }, color: C.white, align: "center" } },
   { text: "0,4990", options: { fill: { color: C.accentRed }, color: C.white, align: "center" } },
   { text: "0,6698", options: { fill: { color: C.accentRed }, color: C.white, align: "center" } }],
  [{ text: "2", options: { fill: { color: C.iceBlue }, align: "center" } },
   { text: "MLP (umbral 0,69)", options: { fill: { color: C.iceBlue }, bold: true, color: C.accentMlp } },
   { text: "0,5615", options: { fill: { color: C.iceBlue }, align: "center" } },
   { text: "0,8337", options: { fill: { color: C.iceBlue }, align: "center" } },
   { text: "0,5138", options: { fill: { color: C.iceBlue }, align: "center" } },
   { text: "0,6190", options: { fill: { color: C.iceBlue }, align: "center" } }],
  [{ text: "3", options: { align: "center" } }, "HistGradientBoosting",
   { text: "0,5527", options: { align: "center" } },
   { text: "0,8409", options: { align: "center" } },
   { text: "0,4365", options: { align: "center" } },
   { text: "0,7532", options: { align: "center" } }],
  [{ text: "4", options: { align: "center" } }, "LogisticRegression",
   { text: "0,5526", options: { align: "center" } },
   { text: "0,8417", options: { align: "center" } },
   { text: "0,4343", options: { align: "center" } },
   { text: "0,7595", options: { align: "center" } }],
  [{ text: "5", options: { align: "center" } }, "XGBoost",
   { text: "0,5423", options: { align: "center" } },
   { text: "0,8221", options: { align: "center" } },
   { text: "0,4890", options: { align: "center" } },
   { text: "0,6086", options: { align: "center" } }],
];
s.addTable(ranking, {
  x: 0.5, y: 4.65, w: 7.5, h: 2.5,
  colW: [0.5, 2.5, 1.1, 1.1, 1.1, 1.2],
  fontSize: 11, fontFace: "Calibri", color: C.textDark,
  border: { type: "solid", pt: 0.5, color: C.grid },
  rowH: 0.4, valign: "middle",
});

// Trade-off P-R (panel derecho)
s.addText("Trade-off Precision–Recall",
  { x: 8.2, y: 4.3, w: 5.0, h: 0.3, fontSize: 13, fontFace: "Calibri",
    color: C.navy, bold: true, margin: 0 });

s.addImage({
  path: `${FIGS}/22_pr_zoom_operating_point.png`,
  x: 8.2, y: 4.65, w: 5.0, h: 2.5,
  sizing: { type: "contain", w: 5.0, h: 2.5 },
});


// ============================================================================
//  SLIDE 5 — Viabilidad y decisión final (mismo lenguaje visual que slides 1-4)
// ============================================================================
s = pres.addSlide();
s.background = { color: C.cream };
addPageHeader(s, 5, "Viabilidad y modelo recomendado para el hospital",
              "Conclusiones del estudio: KPIs clave, limitaciones y datos adicionales");

// =====================================================================
// FILA 1: 3 statCallouts grandes con los KPIs del proyecto
// =====================================================================
statCallout(s, 0.5,  1.35, 4.0, 1.5, "0,5719", "F1 SCORE — RandomForest + feat eng", C.accentRed);
statCallout(s, 4.65, 1.35, 4.0, 1.5, "67 %",   "RECALL — 1.292 de 1.929 casos",      C.successGr);
statCallout(s, 8.80, 1.35, 4.0, 1.5, "0,84",   "AUC-ROC — discriminacion global",    C.navy);

// =====================================================================
// FILA 2: Banner de respuesta destacada (mismo estilo de banner accent)
// =====================================================================
s.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 3.05, w: 12.3, h: 0.75,
  fill: { color: C.successGr }, line: { color: C.successGr }
});
s.addText([
  { text: "VIABLE COMO SISTEMA DE CRIBADO  ", options: { fontSize: 15, bold: true, color: C.white, charSpacing: 1.5 } },
  { text: "·  ", options: { fontSize: 15, color: C.white } },
  { text: "Filtro inicial de priorizacion, no diagnostico definitivo", options: { fontSize: 12, color: C.white, italic: true } },
], { x: 0.5, y: 3.05, w: 12.3, h: 0.75, fontFace: "Calibri",
     align: "center", valign: "middle", margin: 0.1 });

// =====================================================================
// FILA 3: 2 tarjetas grandes (limitaciones | datos adicionales)
//         con MISMO estilo statCallout: fondo blanco + barra lateral + sombra
// =====================================================================
const cardY = 4.05;
const cardH = 3.0;
const cardW = 6.05;
const xLeft = 0.5;
const xRight = 7.25;

// === TARJETA IZQUIERDA: LIMITACIONES ===
s.addShape(pres.shapes.RECTANGLE, {
  x: xLeft, y: cardY, w: cardW, h: cardH,
  fill: { color: C.white }, line: { color: C.grid, width: 1 },
  shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 90, opacity: 0.08 }
});
// Barra lateral roja
s.addShape(pres.shapes.RECTANGLE, {
  x: xLeft, y: cardY, w: 0.10, h: cardH,
  fill: { color: C.accentRed }, line: { color: C.accentRed }
});
// Header rojo de la tarjeta con icono
s.addShape(pres.shapes.OVAL, {
  x: xLeft + 0.30, y: cardY + 0.20, w: 0.45, h: 0.45,
  fill: { color: C.accentRed }, line: { color: C.accentRed }
});
s.addText("!", {
  x: xLeft + 0.30, y: cardY + 0.20, w: 0.45, h: 0.45,
  fontSize: 22, fontFace: "Georgia", color: C.white, bold: true,
  align: "center", valign: "middle", margin: 0
});
s.addText("LIMITACIONES DEL SISTEMA ACTUAL",
  { x: xLeft + 0.90, y: cardY + 0.20, w: cardW - 1.10, h: 0.45,
    fontSize: 12, fontFace: "Calibri", color: C.navy, bold: true,
    charSpacing: 1.5, valign: "middle", margin: 0 });

// Línea separadora bajo header
s.addShape(pres.shapes.RECTANGLE, {
  x: xLeft + 0.30, y: cardY + 0.78, w: cardW - 0.60, h: 0.015,
  fill: { color: C.grid }, line: { color: C.grid }
});

// Contenido de limitaciones
s.addText([
  { text: "Dataset sintetico", options: { bold: true, color: C.navy, fontSize: 11, breakLine: true } },
  { text: "Logistica + ruido N(0; 0,8). Sociodemograficas sin senal real.", options: { color: C.textMid, fontSize: 10, breakLine: true } },
  { text: " ", options: { fontSize: 4, breakLine: true } },
  { text: "Sin datos longitudinales ni imagenes", options: { bold: true, color: C.navy, fontSize: 11, breakLine: true } },
  { text: "Falta evolucion temporal, mamografias, TC y patologia.", options: { color: C.textMid, fontSize: 10, breakLine: true } },
  { text: " ", options: { fontSize: 4, breakLine: true } },
  { text: "Calibracion sobre-confiada", options: { bold: true, color: C.navy, fontSize: 11, breakLine: true } },
  { text: "class_weight sesga las probabilidades. Aplicar Platt scaling.", options: { color: C.textMid, fontSize: 10, breakLine: true } },
  { text: " ", options: { fontSize: 4, breakLine: true } },
  { text: "Coste FP vs FN no parametrizado", options: { bold: true, color: C.navy, fontSize: 11, breakLine: true } },
  { text: "En oncologia, un FN suele costar mucho mas que un FP.", options: { color: C.textMid, fontSize: 10 } },
], { x: xLeft + 0.30, y: cardY + 0.90, w: cardW - 0.55, h: cardH - 1.00,
     fontFace: "Calibri", paraSpaceAfter: 0, margin: 0 });

// === TARJETA DERECHA: DATOS ADICIONALES ===
s.addShape(pres.shapes.RECTANGLE, {
  x: xRight, y: cardY, w: cardW, h: cardH,
  fill: { color: C.white }, line: { color: C.grid, width: 1 },
  shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 90, opacity: 0.08 }
});
// Barra lateral naranja
s.addShape(pres.shapes.RECTANGLE, {
  x: xRight, y: cardY, w: 0.10, h: cardH,
  fill: { color: C.warningOr }, line: { color: C.warningOr }
});
// Header naranja con icono +
s.addShape(pres.shapes.OVAL, {
  x: xRight + 0.30, y: cardY + 0.20, w: 0.45, h: 0.45,
  fill: { color: C.warningOr }, line: { color: C.warningOr }
});
s.addText("+", {
  x: xRight + 0.30, y: cardY + 0.20, w: 0.45, h: 0.45,
  fontSize: 26, fontFace: "Georgia", color: C.white, bold: true,
  align: "center", valign: "middle", margin: 0
});
s.addText("DATOS ADICIONALES QUE MEJORARIAN EL MODELO",
  { x: xRight + 0.90, y: cardY + 0.20, w: cardW - 1.10, h: 0.45,
    fontSize: 11, fontFace: "Calibri", color: C.navy, bold: true,
    charSpacing: 1.2, valign: "middle", margin: 0 });

// Línea separadora bajo header
s.addShape(pres.shapes.RECTANGLE, {
  x: xRight + 0.30, y: cardY + 0.78, w: cardW - 0.60, h: 0.015,
  fill: { color: C.grid }, line: { color: C.grid }
});

// Contenido de datos adicionales
s.addText([
  { text: "Marcadores tumorales", options: { bold: true, color: C.navy, fontSize: 11, breakLine: true } },
  { text: "CA-125 (ovario), CEA (colorrectal), PSA (prostata), AFP, HE4.", options: { color: C.textMid, fontSize: 10, breakLine: true } },
  { text: " ", options: { fontSize: 4, breakLine: true } },
  { text: "Imagenologia", options: { bold: true, color: C.navy, fontSize: 11, breakLine: true } },
  { text: "Mamografia digital, TC torax/abdomen, RM hepatica.", options: { color: C.textMid, fontSize: 10, breakLine: true } },
  { text: " ", options: { fontSize: 4, breakLine: true } },
  { text: "Datos longitudinales", options: { bold: true, color: C.navy, fontSize: 11, breakLine: true } },
  { text: "Evolucion temporal de bioquimicos (12-24 meses).", options: { color: C.textMid, fontSize: 10, breakLine: true } },
  { text: " ", options: { fontSize: 4, breakLine: true } },
  { text: "Historial familiar y exposicion ambiental", options: { bold: true, color: C.navy, fontSize: 11, breakLine: true } },
  { text: "1er grado, ocupacion (amianto, radon, radiacion).", options: { color: C.textMid, fontSize: 10 } },
], { x: xRight + 0.30, y: cardY + 0.90, w: cardW - 0.55, h: cardH - 1.00,
     fontFace: "Calibri", paraSpaceAfter: 0, margin: 0 });


// ============================================================================
//  SLIDE 6 — Cierre / conclusiones finales (grid 2x2 profesional)
// ============================================================================
s = pres.addSlide();
s.background = { color: C.cream };

// Header con mismo addPageHeader pero usamos ★ en lugar de número
s.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 13.3, h: 1.1,
  fill: { color: C.navy }, line: { color: C.navy }
});
s.addShape(pres.shapes.OVAL, {
  x: 0.45, y: 0.25, w: 0.6, h: 0.6,
  fill: { color: C.accentRed }, line: { color: C.accentRed }
});
s.addText("★", {
  x: 0.45, y: 0.25, w: 0.6, h: 0.6,
  fontSize: 22, fontFace: "Georgia", color: C.white,
  bold: true, align: "center", valign: "middle", margin: 0,
});
s.addText("Conclusiones finales del estudio",
  { x: 1.2, y: 0.15, w: 11.5, h: 0.5,
    fontSize: 24, fontFace: "Georgia", color: C.white, bold: true,
    align: "left", valign: "middle", margin: 0 });
s.addText("Cuatro hallazgos clave que avalan el rigor metodologico del trabajo",
  { x: 1.2, y: 0.62, w: 11.5, h: 0.35,
    fontSize: 12, fontFace: "Calibri", color: C.iceBlue,
    italic: true, align: "left", valign: "middle", margin: 0 });

// =====================================================================
// Grid 2x2 — 4 tarjetas grandes con métrica destacada
// =====================================================================
const findings = [
  {
    icon: "✓",
    metric: "0,84",
    metricLabel: "AUC-ROC",
    title: "Sistema de cribado viable",
    body: "Detecta el 67 % de los pacientes con cancer entre los 10.001 de test. Suficiente como filtro inicial de priorizacion clinica.",
    color: C.successGr,
  },
  {
    icon: "⚙",
    metric: "+0,008",
    metricLabel: "F1 EN RF · −0,015 EN MLP",
    title: "Feature engineering no es universal",
    body: "n_mutaciones y n_comorbilidades ayudan a los arboles pero perjudican al MLP. Hallazgo metodologico defendible.",
    color: C.accentRed,
  },
  {
    icon: "ρ",
    metric: "0,862",
    metricLabel: "SPEARMAN ρ",
    title: "Pipeline validado contra el modelo generativo",
    body: "Correlacion entre el ranking aprendido y los pesos verdaderos del metadata oficial. El modelo aprende los predictores correctos.",
    color: C.navy,
  },
  {
    icon: "λ",
    metric: "SEED=42",
    metricLabel: "REPRODUCIBILIDAD ESTRICTA",
    title: "Sin data leakage en ninguna fase",
    body: "Threshold tuning sobre validacion. Test intacto hasta el final. Scaler ajustado solo en train. Seeds fijos en todas las fases.",
    color: C.warningOr,
  },
];

const gridX0 = 0.5;
const gridY0 = 1.35;
const gW = 6.05;   // ancho de cada tarjeta
const gH = 2.83;   // alto de cada tarjeta
const gGap = 0.20;

for (let i = 0; i < findings.length; i++) {
  const row = Math.floor(i / 2);
  const col = i % 2;
  const xi = gridX0 + col * (gW + gGap);
  const yi = gridY0 + row * (gH + gGap);
  const f = findings[i];

  // Tarjeta blanca con sombra
  s.addShape(pres.shapes.RECTANGLE, {
    x: xi, y: yi, w: gW, h: gH,
    fill: { color: C.white }, line: { color: C.grid, width: 1 },
    shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 90, opacity: 0.08 }
  });
  // Barra lateral coloreada
  s.addShape(pres.shapes.RECTANGLE, {
    x: xi, y: yi, w: 0.10, h: gH,
    fill: { color: f.color }, line: { color: f.color }
  });

  // ZONA SUPERIOR: círculo con icono + métrica grande + label
  // Círculo del icono
  s.addShape(pres.shapes.OVAL, {
    x: xi + 0.35, y: yi + 0.30, w: 0.65, h: 0.65,
    fill: { color: f.color }, line: { color: f.color }
  });
  s.addText(f.icon, {
    x: xi + 0.35, y: yi + 0.30, w: 0.65, h: 0.65,
    fontSize: 26, fontFace: "Georgia", color: C.white, bold: true,
    align: "center", valign: "middle", margin: 0
  });

  // Métrica grande (a la derecha del icono)
  s.addText(f.metric, {
    x: xi + 1.15, y: yi + 0.20, w: gW - 1.30, h: 0.65,
    fontSize: 34, fontFace: "Georgia", color: f.color, bold: true,
    valign: "middle", margin: 0
  });
  // Label de la métrica
  s.addText(f.metricLabel, {
    x: xi + 1.15, y: yi + 0.82, w: gW - 1.30, h: 0.25,
    fontSize: 9, fontFace: "Calibri", color: C.textMid, bold: true,
    charSpacing: 1.5, valign: "middle", margin: 0
  });

  // Línea separadora
  s.addShape(pres.shapes.RECTANGLE, {
    x: xi + 0.35, y: yi + 1.20, w: gW - 0.65, h: 0.015,
    fill: { color: C.grid }, line: { color: C.grid }
  });

  // Título de la tarjeta (debajo)
  s.addText(f.title, {
    x: xi + 0.35, y: yi + 1.30, w: gW - 0.55, h: 0.50,
    fontSize: 16, fontFace: "Calibri", color: C.navy, bold: true,
    valign: "top", margin: 0
  });
  // Body
  s.addText(f.body, {
    x: xi + 0.35, y: yi + 1.85, w: gW - 0.55, h: gH - 2.0,
    fontSize: 11, fontFace: "Calibri", color: C.textMid,
    valign: "top", margin: 0
  });
}

// Pie idéntico al de las otras slides
s.addText("UAX · Ingenieria Matematica · IA 2025/26   |   Caso de uso: Prediccion de cancer",
  { x: 0.5, y: 7.2, w: 12.3, h: 0.25,
    fontSize: 8, fontFace: "Calibri", color: C.textLight, align: "left", margin: 0 });
s.addText("Conclusiones finales",
  { x: 0.5, y: 7.2, w: 12.3, h: 0.25,
    fontSize: 8, fontFace: "Calibri", color: C.textLight, align: "right", margin: 0 });


// ============================================================================
// Persistir
// ============================================================================
const outPath = "./Entregable_5_diapositivas.pptx";
pres.writeFile({ fileName: outPath })
   .then(f => console.log(`\n✓ Generado: ${f}\n`))
   .catch(err => { console.error("ERROR:", err); process.exit(1); });
