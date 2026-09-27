# 🏠 ¿Rento o Compro?

Calculadora interactiva que compara, mes a mes durante 30 años, el patrimonio
neto de **rentar e invertir la diferencia** contra **comprar con crédito
hipotecario** — usando el mismo capital inicial en ambos escenarios (el
enganche que en un caso se invierte y en el otro se inmoviliza).

Construida para responder una sola pregunta sin refranes ni sesgos de venta:
**¿a partir de cuántos años te conviene más comprar que rentar?**

> Proyecto educativo de finanzas personales. No constituye asesoría
> financiera, fiscal ni inmobiliaria.

---

## ✨ Qué incluye

- **Motor financiero real:** amortización francesa para la hipoteca, valor
  futuro con capitalización mensual para las inversiones, costo de
  oportunidad del enganche, costos ocultos de ser dueño (mantenimiento,
  predial, seguros), gastos de escrituración y comisión de venta.
- **Punto de equilibrio (*breakeven horizon*):** el gráfico marca el año
  exacto en el que comprar empieza a ganarle a rentar.
- **Panel de supuestos transparente:** tasa hipotecaria, plusvalía,
  rendimiento de inversión e inflación de la renta son 100% ajustables —
  nada queda oculto en el código.
- **Pestaña de metodología:** todas las fórmulas explicadas paso a paso,
  con las fuentes de cada supuesto por defecto.

## 🚀 Ejecutar en local

```bash
git clone https://github.com/<tu-usuario>/<tu-repo>.git
cd <tu-repo>
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

La app se abre automáticamente en `http://localhost:8501`.

## ☁️ Publicar gratis en Streamlit Community Cloud

1. Sube este proyecto a un repositorio público de GitHub (ver sección
   siguiente si no lo has hecho).
2. Entra a [share.streamlit.io](https://share.streamlit.io) e inicia sesión
   con tu cuenta de GitHub.
3. Clic en **"New app"** → selecciona el repositorio, la rama (`main`) y el
   archivo de entrada (`app.py`).
4. Clic en **"Deploy"**. En un par de minutos tendrás una URL pública tipo
   `https://tu-app.streamlit.app` para compartir en tu portafolio.

## 📦 Subir el proyecto a GitHub por primera vez

```bash
cd rento-o-compro-streamlit
git init
git add .
git commit -m "Primera versión: calculadora Rento o Compro"
git branch -M main
git remote add origin https://github.com/<tu-usuario>/<tu-repo>.git
git push -u origin main
```

## 🗂️ Estructura del proyecto

```
rento-o-compro-streamlit/
├── app.py                    # App de Streamlit (calculadora + metodología)
├── requirements.txt          # Dependencias
├── .streamlit/config.toml    # Tema visual (paleta de marca)
├── .gitignore
└── README.md
```

## 🛠️ Stack

- [Streamlit](https://streamlit.io) — interfaz e interactividad
- [Plotly](https://plotly.com/python/) — gráfico de cruce de patrimonio neto
- Python puro para el motor de cálculo (sin dependencias de ciencia de
  datos pesadas)

## 📄 Licencia

MIT — siéntete libre de usar, modificar y distribuir este proyecto citando
la fuente.

## Autor

**Isaac Ortega Mota** — Economista, especialidad en Economía de la Empresa y
Finanzas.
