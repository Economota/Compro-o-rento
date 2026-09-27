"""
¿Rento o Compro? — Calculadora de patrimonio neto: rentar e invertir vs. comprar
==================================================================================

Simula, mes a mes durante 30 años, el patrimonio neto de dos caminos que parten
del MISMO capital inicial (el enganche + los gastos de compra):

  1. COMPRAR: se adquiere la vivienda con crédito hipotecario. El patrimonio es
     el valor de la casa (con plusvalía) menos el costo de venderla, menos el
     saldo pendiente de la hipoteca, más cualquier ahorro que sobre si comprar
     resulta más barato que rentar en algún mes (se invierte).

  2. RENTAR E INVERTIR: el enganche + gastos de compra se invierten desde el
     día uno, y cada mes se invierte también la diferencia entre lo que le
     hubiera costado ser dueño (hipoteca + mantenimiento + predial/seguros) y
     lo que efectivamente paga de renta.

Ver la pestaña "Metodología" dentro de la app para las fórmulas explícitas y
las fuentes de cada supuesto.

Este proyecto es software educativo de código abierto. No constituye
asesoría financiera, fiscal ni inmobiliaria.
"""

import streamlit as st
import plotly.graph_objects as go

# ──────────────────────────────────────────────────────────────────────────
# Supuestos fijos del modelo (no editables desde la interfaz)
# ──────────────────────────────────────────────────────────────────────────
PLAZO_HIPOTECA_ANIOS = 20       # plazo típico de un crédito hipotecario en México
HORIZONTE_ANIOS = 30            # años que se simulan hacia adelante
MANTENIMIENTO_ANUAL = 0.010     # 1.0% del valor de la vivienda por año
PREDIAL_SEGUROS_ANUAL = 0.0035  # 0.35% del valor de la vivienda por año
GASTOS_COMPRA = 0.06            # escrituración, ISAI, notario, avalúo (≈6%)
COSTO_VENTA = 0.05              # comisión inmobiliaria al vender (≈5%)


# ──────────────────────────────────────────────────────────────────────────
# Utilidades
# ──────────────────────────────────────────────────────────────────────────
def fmt_mxn(monto: float) -> str:
    """Formatea un número como pesos mexicanos, sin decimales."""
    return f"${monto:,.0f} MXN"


# ──────────────────────────────────────────────────────────────────────────
# Motor de cálculo
# ──────────────────────────────────────────────────────────────────────────
def calcular(renta0, precio, enganche, anios_plan,
             tasa_hipoteca_pct, plusvalia_pct, rendimiento_pct, inflacion_renta_pct):
    """
    Simula mes a mes el patrimonio neto de RENTAR vs. COMPRAR.
    Devuelve un diccionario con la serie anual y los indicadores clave.
    """
    enganche = min(enganche, precio)
    credito = max(precio - enganche, 0)

    # Tasas mensuales equivalentes (capitalización mensual)
    i_hip = tasa_hipoteca_pct / 100 / 12
    n_hip = PLAZO_HIPOTECA_ANIOS * 12
    if credito <= 0:
        pago_hipoteca = 0.0
    elif i_hip == 0:
        pago_hipoteca = credito / n_hip
    else:
        # Fórmula de amortización francesa (pago fijo mensual)
        pago_hipoteca = credito * i_hip / (1 - (1 + i_hip) ** (-n_hip))

    i_inv = (1 + rendimiento_pct / 100) ** (1 / 12) - 1      # tasa mensual efectiva de inversión
    g_plus = (1 + plusvalia_pct / 100) ** (1 / 12) - 1        # crecimiento mensual del valor de la casa
    g_renta = (1 + inflacion_renta_pct / 100) ** (1 / 12) - 1 # crecimiento mensual de la renta

    # Ambos escenarios arrancan con el mismo capital: el costo de oportunidad del enganche
    cash_inicial = enganche + precio * GASTOS_COMPRA

    saldo_hip = credito
    valor_casa = precio
    renta = renta0
    portafolio_rentero = cash_inicial
    portafolio_comprador = 0.0

    serie = [{
        "anio": 0,
        "Compro": round(valor_casa * (1 - COSTO_VENTA) - saldo_hip),
        "Rento": round(portafolio_rentero),
    }]

    for mes in range(1, HORIZONTE_ANIOS * 12 + 1):
        # Rendimiento del mes sobre lo ya invertido en cada portafolio
        portafolio_rentero *= (1 + i_inv)
        portafolio_comprador *= (1 + i_inv)

        # Pago de la hipoteca este mes (solo mientras dure el crédito)
        pago_mes = 0.0
        if saldo_hip > 0:
            interes = saldo_hip * i_hip
            abono = min(pago_hipoteca - interes, saldo_hip)
            saldo_hip -= abono
            pago_mes = interes + abono

        # Costos de ser dueño este mes (mantenimiento + predial/seguros)
        costos_dueno = valor_casa * (MANTENIMIENTO_ANUAL + PREDIAL_SEGUROS_ANUAL) / 12
        flujo_comprador = pago_mes + costos_dueno

        # La diferencia de flujos se invierte del lado que gasta menos ese mes
        diferencia_flujo = flujo_comprador - renta
        if diferencia_flujo > 0:
            portafolio_rentero += diferencia_flujo
        else:
            portafolio_comprador += -diferencia_flujo

        # Crecimientos del mes
        valor_casa *= (1 + g_plus)
        renta *= (1 + g_renta)

        if mes % 12 == 0:
            serie.append({
                "anio": mes // 12,
                "Compro": round(valor_casa * (1 - COSTO_VENTA) - saldo_hip + portafolio_comprador),
                "Rento": round(portafolio_rentero),
            })

    # Punto de equilibrio: primer año donde COMPRAR alcanza o supera a RENTAR
    breakeven = None
    for punto in serie:
        if punto["anio"] > 0 and punto["Compro"] >= punto["Rento"]:
            breakeven = punto["anio"]
            break

    en_anio = serie[anios_plan]
    diferencia = en_anio["Compro"] - en_anio["Rento"]
    gana = "COMPRAR" if diferencia >= 0 else "RENTAR"

    return {
        "serie": serie,
        "breakeven": breakeven,
        "en_anio": en_anio,
        "diferencia": diferencia,
        "gana": gana,
        "pago_hipoteca": pago_hipoteca,
        "credito": credito,
    }


# ──────────────────────────────────────────────────────────────────────────
# Gráfico
# ──────────────────────────────────────────────────────────────────────────
def construir_grafico(serie, anios_plan, breakeven):
    anios_x = [p["anio"] for p in serie]
    compro_y = [p["Compro"] for p in serie]
    rento_y = [p["Rento"] for p in serie]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=anios_x, y=compro_y, mode="lines", name="Compro",
        line=dict(color="#1C1B1F", width=3),
        hovertemplate="Año %{x}<br>Compro: $%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=anios_x, y=rento_y, mode="lines", name="Rento e invierto",
        line=dict(color="#E4007C", width=3),
        hovertemplate="Año %{x}<br>Rento e invierto: $%{y:,.0f}<extra></extra>",
    ))

    fig.add_vline(
        x=anios_plan, line_dash="dash", line_color="#8A8580", line_width=1.5,
        annotation_text="Tu plan", annotation_position="top",
        annotation_font_color="#8A8580", annotation_font_size=11,
    )

    if breakeven is not None:
        y_be = next(p["Compro"] for p in serie if p["anio"] == breakeven)
        fig.add_trace(go.Scatter(
            x=[breakeven], y=[y_be], mode="markers",
            marker=dict(color="#E4007C", size=11, line=dict(color="white", width=2)),
            name=f"Cruce: año {breakeven}",
            hovertemplate=f"Punto de equilibrio<br>Año {breakeven}<extra></extra>",
        ))

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Archivo, sans-serif", color="#1C1B1F", size=13),
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
        xaxis=dict(title="Años", gridcolor="#EFE9E3", zeroline=False),
        yaxis=dict(title="Patrimonio neto (MXN)", tickformat=",.0f", gridcolor="#EFE9E3", zeroline=False),
        height=400,
        hovermode="x unified",
    )
    return fig


# ──────────────────────────────────────────────────────────────────────────
# Interfaz
# ──────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="¿Rento o Compro?", page_icon="🏠", layout="centered")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Archivo:wght@400;600;800&display=swap');

html, body, [class*="css"]  { font-family: 'Archivo', sans-serif; }

.eyebrow {
    color: #E4007C; font-size: 12px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.2em; margin-bottom: 2px;
}
.brand-title {
    font-family: 'Anton', sans-serif; font-size: 42px; line-height: 1;
    margin: 0 0 6px 0; color: #1C1B1F;
}
.card-dark {
    background:#1C1B1F; color:#FFFBF7; border-radius:16px;
    padding:28px 24px; text-align:center; margin: 18px 0 22px 0;
}
.card-dark .p1 { font-size:14px; color:#B5B0AA; margin:0 0 8px; }
.veredicto {
    font-family:'Anton',sans-serif; font-size:clamp(48px,10vw,72px);
    color:#E4007C; line-height:1; margin:0;
}
.card-dark .p2 { font-size:15px; color:#D6D2CC; margin:12px 0 0; }
.card-dark .p2 strong { color:#E4007C; }
.card-dark .p3 {
    font-size:13px; color:#B5B0AA; margin:12px 0 0;
    padding-top:12px; border-top:1px solid #3A383D;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown('<p class="eyebrow">La decisión más grande de tu vida, sin refranes</p>', unsafe_allow_html=True)
st.markdown('<h1 class="brand-title">¿RENTO O COMPRO?</h1>', unsafe_allow_html=True)
st.caption(
    "Sin que te mienta el banco ni tu tía. Aquí sí contamos el costo de "
    "oportunidad del enganche, la escrituración y lo que cuesta vender."
)

tab_calc, tab_meta = st.tabs(["🧮  Calculadora", "📚  Metodología"])

# ── TAB: CALCULADORA ────────────────────────────────────────────────────
with tab_calc:
    renta0 = st.number_input(
        "¿Cuánto pagas (o pagarías) de renta al mes?",
        min_value=0, value=12000, step=500, format="%d",
    )
    precio = st.number_input(
        "Precio de la casa o depa equivalente",
        min_value=0, value=2_500_000, step=50_000, format="%d",
    )
    enganche = st.number_input(
        "Enganche que tienes ahorrado",
        min_value=0, value=500_000, step=10_000, format="%d",
    )

    precio_actual = max(precio, 1)
    eng_pct = min(enganche, precio) / precio_actual * 100 if precio > 0 else 0
    st.caption(f"{fmt_mxn(min(enganche, precio))} = {eng_pct:.0f}% del precio")
    if precio > 0 and eng_pct < 10:
        st.warning("Ojo: la mayoría de los bancos pide mínimo 10% de enganche.", icon="⚠️")

    anios_plan = st.slider("¿Cuántos años planeas quedarte ahí?", 1, 30, 7)

    with st.expander("🔧  Los supuestos (muévelos, no escondemos nada)"):
        tasa_hipoteca = st.slider(
            "Tasa hipotecaria anual", 6.0, 15.0, 10.5, 0.1,
            help="Tasa fija anual del crédito hipotecario a 20 años.",
        )
        plusvalia = st.slider(
            "Plusvalía de la casa (% anual)", 0.0, 12.0, 5.0, 0.1,
            help="Crecimiento anual esperado del valor de la propiedad.",
        )
        rendimiento = st.slider(
            "Rendimiento si inviertes (% anual)", 4.0, 14.0, 7.0, 0.1,
            help="Rendimiento anual esperado del dinero que NO se destina a la casa.",
        )
        inflacion_renta = st.slider(
            "Inflación de la renta (% anual)", 0.0, 8.0, 3.3, 0.1,
            help="Qué tan rápido sube la renta cada año.",
        )
        st.caption(
            "Fijos en el modelo: mantenimiento 1.0% del valor/año, predial y "
            "seguros 0.35%/año, gastos de compra 6% (escrituras, ISAI, notario), "
            "comisión de venta 5%, hipoteca a 20 años. Ver pestaña Metodología."
        )

    r = calcular(renta0, precio, enganche, anios_plan,
                 tasa_hipoteca, plusvalia, rendimiento, inflacion_renta)

    extra = (
        f"Punto de equilibrio: comprar empieza a ganar a partir del año {r['breakeven']}."
        if r["breakeven"] else
        "Con estos supuestos, comprar no alcanza a rentar e invertir en 30 años."
    )
    if r["credito"] > 0:
        extra += f" Tu hipoteca saldría en {fmt_mxn(r['pago_hipoteca'])} al mes ({PLAZO_HIPOTECA_ANIOS} años)."

    st.markdown(f"""
    <div class="card-dark">
      <p class="p1">Si te quedas {anios_plan} {'año' if anios_plan == 1 else 'años'}, te conviene:</p>
      <p class="veredicto">{r['gana']}</p>
      <p class="p2">Te deja <strong>{fmt_mxn(abs(r['diferencia']))}</strong> más de patrimonio que la otra opción.</p>
      <p class="p3">{extra}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Tu patrimonio neto en cada camino**")
    st.plotly_chart(construir_grafico(r["serie"], anios_plan, r["breakeven"]), use_container_width=True)

    st.info(
        "Ni rentar es \"tirar el dinero\" ni comprar es siempre ganar. La respuesta "
        "depende del tiempo que te quedes — y ahora ya sabes exactamente dónde "
        "está tu punto de cruce."
    )

    st.caption(
        "Herramienta educativa, no asesoría financiera ni inmobiliaria. "
        "Los resultados dependen enteramente de los supuestos que elijas arriba."
    )

# ── TAB: METODOLOGÍA ────────────────────────────────────────────────────
with tab_meta:
    st.markdown("## Cómo funciona el modelo")
    st.markdown(
        "La calculadora simula, **mes a mes durante 30 años**, el patrimonio neto "
        "de dos caminos que parten del **mismo capital inicial**: el enganche más "
        "los gastos de compra. Eso es justamente lo que las calculadoras de bancos "
        "suelen omitir — y por lo que rentar parece, a simple vista, \"tirar el dinero\"."
    )

    st.markdown("### 1. Pago mensual de la hipoteca (amortización francesa)")
    st.latex(r"""
    M = \frac{P \cdot i}{1 - (1+i)^{-n}}
    """)
    st.markdown(
        "- **M**: pago mensual fijo\n"
        "- **P**: monto del crédito (precio − enganche)\n"
        "- **i**: tasa de interés mensual = tasa anual ÷ 12\n"
        "- **n**: número de pagos = 20 años × 12 = 240\n\n"
        "Cada mes, parte del pago cubre intereses sobre el saldo pendiente y el resto "
        "abona a capital, reduciendo el saldo — así funciona cualquier crédito hipotecario a tasa fija en México."
    )

    st.markdown("### 2. Crecimiento del valor de la casa y de la renta")
    st.latex(r"""
    V_t = V_0 \cdot (1 + g)^{t}
    """)
    st.markdown(
        "La misma fórmula de interés compuesto se usa para proyectar el valor de la "
        "propiedad (con la tasa de plusvalía) y el monto de la renta (con su propia "
        "inflación) mes a mes, usando la tasa mensual equivalente "
        r"$(1+g_{anual})^{1/12}-1$."
    )

    st.markdown("### 3. El costo de oportunidad del enganche")
    st.markdown(
        "Quien renta no inmoviliza su dinero en un enganche: lo invierte desde el "
        "día uno. Ese es el **costo de oportunidad** — lo que se deja de ganar por "
        "elegir comprar en vez de invertir. El modelo lo calcula con la fórmula de "
        "valor futuro de una suma con capitalización mensual:"
    )
    st.latex(r"""
    VF = VP \cdot (1 + i)^{n}
    """)
    st.markdown(
        "Además, cada mes se compara cuánto le habría costado ser dueño (pago de "
        "hipoteca + mantenimiento + predial y seguros) contra la renta efectivamente "
        "pagada. La diferencia también se invierte, del lado que gastó menos ese mes — "
        "así ningún escenario recibe ventaja artificial."
    )

    st.markdown("### 4. Patrimonio neto de cada camino")
    st.latex(r"""
    PN_{compro} = V_{casa}\,(1 - c_{venta}) - Saldo_{hipoteca} + Portafolio_{comprador}
    """)
    st.latex(r"""
    PN_{rento} = Portafolio_{rentero}
    """)
    st.markdown(
        "- **c_venta**: comisión inmobiliaria al vender (5%)\n"
        "- **Portafolio_comprador**: ahorros invertidos en los meses donde comprar salió más barato que rentar\n"
        "- **Portafolio_rentero**: enganche + gastos de compra iniciales, más cada diferencia mensual invertida"
    )

    st.markdown("### 5. Punto de equilibrio (*breakeven horizon*)")
    st.markdown(
        "Es el primer año, dentro de la simulación de 30 años, en el que "
        r"$PN_{compro} \geq PN_{rento}$. "
        "Antes de ese año, irte más pronto favorece rentar; después de ese año, "
        "quedarte más tiempo favorece comprar."
    )

    st.markdown("### Supuestos fijos del modelo")
    st.markdown(
        "| Supuesto | Valor |\n"
        "|---|---|\n"
        "| Plazo de la hipoteca | 20 años |\n"
        "| Mantenimiento anual | 1.0% del valor de la vivienda |\n"
        "| Predial y seguros anual | 0.35% del valor de la vivienda |\n"
        "| Gastos de compra (escrituración, ISAI, notario, avalúo) | 6% del precio |\n"
        "| Comisión de venta al vender | 5% del valor de venta |\n"
    )

    st.markdown("### Supuestos ajustables — referencia septiembre 2026, CDMX")
    st.markdown(
        "Los valores por defecto de los sliders se calibraron con datos públicos "
        "vigentes a septiembre de 2026. Muévelos libremente: la app es un "
        "laboratorio, no una receta.\n\n"
        "- **Tasa hipotecaria (10.5% por defecto):** Banxico fijó su tasa de "
        "referencia en 6.50% el 25 de junio de 2026. Sobre esa base, la banca "
        "ofrece tasas de 8.5% a 10.5% a los perfiles crediticios más competitivos, "
        "mientras que el promedio general del mercado ronda 11-11.5% (algunos "
        "bancos publican tasas ordinarias de hasta 11.2%, con CAT cercano a 13%). "
        "*Fuente: Banco de México, comparativas de mercado 2026.*\n\n"
        "- **Plusvalía (5% por defecto):** el índice nacional de la Sociedad "
        "Hipotecaria Federal (SHF) mostró una apreciación de 7.3% interanual en "
        "el segundo trimestre de 2026. Dentro de CDMX hay mucha dispersión: la "
        "vivienda usada de la capital creció alrededor de 4.3% anual en 2024, "
        "mientras que zonas premium (Roma, Condesa, Polanco) promedian 7-9% "
        "anual. El 5% es un estimado moderado, citywide. "
        "*Fuente: SHF, análisis de mercado inmobiliario CDMX 2026.*\n\n"
        "- **Rendimiento si inviertes (7% por defecto):** los CETES a 28 días "
        "—el piso de referencia libre de riesgo en México— pagaban 6.15% anual "
        "en la subasta del 22 de septiembre de 2026. El 7% asume un premio "
        "moderado sobre ese piso, razonable para un portafolio diversificado a "
        "20-30 años. No es una garantía ni una recomendación de inversión. "
        "*Fuente: Banco de México (subastas de CETES).*\n\n"
        "- **Inflación de la renta (3.3% por defecto):** el INEGI reportó una "
        "inflación general anual de 3.26% en agosto de 2026. "
        "*Fuente: INEGI, Índice Nacional de Precios al Consumidor.*"
    )

    st.warning(
        "Estos supuestos cambian con el tiempo. Antes de tomar una decisión real, "
        "verifica las tasas vigentes con tu banco y las cifras de plusvalía con un "
        "valuador o asesor inmobiliario de la zona específica que te interesa.",
        icon="ℹ️",
    )

    st.caption("Herramienta educativa de código abierto. No constituye asesoría financiera, fiscal ni inmobiliaria.")
