"""Reglas de aplicación, no prescripciones oficiales. Véase docs/fundamento_rutinas.md."""
from itertools import product

VERSION = "MG-EVIDENCIA-2026-09-v1"
ZONAS = {
    "cuerpo_completo": frozenset(("superior", "inferior")),
    "tren_superior": frozenset(("superior",)),
    "tren_inferior": frozenset(("inferior",)),
}


def distribuir_enfoques(dias, preferencia=None):
    """Maximiza cobertura sin repetir zona en fechas contiguas, incluido dom/lun.

    Heurística propia: no equivale a demostrar recuperación fisiológica ni a
    garantizar frecuencia suficiente para cada músculo.
    """
    dias = sorted(dias)
    mejor, puntuacion = None, None
    for propuesta in product(ZONAS, repeat=len(dias)):
        if any(
            ((dias[j] - dias[i]) % 7 in (1, 6))
            and ZONAS[propuesta[i]] & ZONAS[propuesta[j]]
            for i in range(len(dias)) for j in range(i + 1, len(dias))
        ):
            continue
        superior = sum("superior" in ZONAS[p] for p in propuesta)
        inferior = sum("inferior" in ZONAS[p] for p in propuesta)
        preferidos = superior if preferencia == "superior" else inferior if preferencia == "inferior" else 0
        puntos = (min(superior, inferior), superior + inferior, preferidos,
                  -abs(superior - inferior))
        if puntuacion is None or puntos > puntuacion:
            mejor, puntuacion = propuesta, puntos
    return list(mejor)


def resumen_frecuencia(enfoques):
    superior = sum("superior" in ZONAS[p] for p in enfoques)
    inferior = sum("inferior" in ZONAS[p] for p in enfoques)
    texto = f"Distribución semanal: {superior} sesiones con tren superior y {inferior} con tren inferior."
    if min(superior, inferior) < 2:
        texto += (" Tu disponibilidad no permite dos exposiciones por zona con esta separación. "
                  "Puedes empezar así y, si te resulta posible, elegir días más separados. "
                  "No presentamos este horario como cumplimiento completo de las recomendaciones.")
    return texto


def bloques_basicos(enfoque, preferencia=None):
    inferior = [
        ("Sentadilla goblet con mancuerna", "Prensa de piernas en máquina"),
        ("Peso muerto rumano con barra", "Puente de glúteos en suelo"),
    ]
    superior = [
        ("Press de pecho sentado en máquina", "Press de banca con barra"),
        ("Remo sentado en polea", "Jalón al pecho en polea"),
    ]
    if enfoque == "tren_inferior":
        return inferior + [("Elevación de talones de pie en máquina",)]
    if enfoque == "tren_superior":
        return superior + [("Press militar sentado con mancuernas", "Elevaciones laterales con mancuernas")]
    return superior + inferior if preferencia == "superior" else inferior + superior
