# Fundamento y límites del generador MaikerGym

Versión: MG-EVIDENCIA-2026-09-v1 · revisión documental: 23/09/2026.

## Fuentes primarias

1. OMS (2020), *WHO guidelines on physical activity and sedentary behaviour*.
   https://www.who.int/publications/i/item/9789240015128
   Referencia de salud pública: para adultos, 150–300 minutos aeróbicos moderados
   o 75–150 vigorosos por semana y fortalecimiento de grandes grupos musculares
   al menos dos días. No proporciona las listas de ejercicios del aplicativo.
2. Currier et al. / ACSM (2026), *Resistance Training Prescription for Muscle
   Function, Hypertrophy, and Physical Performance in Healthy Adults: An Overview
   of Reviews*. DOI: 10.1249/MSS.0000000000003897.
   https://pmc.ncbi.nlm.nih.gov/articles/PMC12965823/
   Síntesis para adultos sanos: entrenamiento progresivo, sin necesidad de fallo
   muscular; el esfuerzo puede orientarse mediante repeticiones en reserva.
   Volúmenes mayores favorecen hipertrofia, pero no implican una dosis universal
   ni justifican subir series automáticamente a todo usuario avanzado.

## Traducción al código: decisiones propias, no citas de las organizaciones

| Regla | Implementación y límite |
| --- | --- |
| Calendario real | `distribuir_enfoques` explora combinaciones superior/inferior/completo. Evita repetir zona en días consecutivos, también domingo/lunes; maximiza la menor frecuencia de ambas zonas. Es una heurística de recuperación, no prueba clínica de que 48 h basten. |
| Preferencia corporal | Desempate de frecuencia y orden de movimientos/accesorios. Nunca elimina la otra zona ni presupone preferencias por sexo. |
| Cobertura | Rodilla, cadera, empuje y tracción obligatorios en cuerpo completo; versiones superior/inferior conservan sus básicos. Un catálogo incompleto o tiempo insuficiente produce un error, no un plan incompleto silencioso. Son patrones, no una auditoría anatómica de todos los músculos. |
| Volumen inicial | 2 series principiantes; 3 otros niveles; máximo 6 ejercicios/sesión. No se multiplica por las horas libres. Estos números son valores de aplicación, no una dosis óptima demostrada para cada usuario. |
| Repeticiones | Se conserva 10–12 para aprender y 8–12 en los demás niveles como rango operativo; no se exige llegar al máximo de repeticiones posible. |
| Descansos | Mínimo operativo de 120 s en rutinas automáticas; se respeta un descanso elegido mayor si cabe en el tiempo. El usuario ve el valor aplicado. No se presenta como un mínimo oficial ni válido para toda disciplina. |
| Progresión | Orientación escrita para revisar pequeños aumentos según técnica y tolerancia. No se prescribe carga en kg, pruebas de 1RM ni aumentos automáticos. |
| Tiempo | 10 min reservados para preparación/transiciones y duración estimada. Mínimo 45 min es una restricción existente de producto, no una exigencia OMS/ACSM. |
| Objetivos | Salud y pérdida de peso no eliminan la fuerza; estética/hipertrofia cambian prioridades. No garantiza pérdida de grasa localizada ni hipertrofia óptima. |
| Insuficiente frecuencia | Se informa si alguna zona queda con menos de 2 exposiciones. Un fin de semana puede ser superior/inferior; no se declara que eso cubre toda la recomendación semanal. |
| Aeróbico | Caminata/remo siguen siendo complementos, no garantía de cumplir la meta OMS. Pesas, descansos y calentamiento no se suman automáticamente como minutos aeróbicos. |

## Trazabilidad y preservación

Cada nueva rutina automática lleva la versión y distribución en `plan.descripcion`.
Las rutinas ya guardadas, personales y el historial no se reescriben ni reciben
retroactivamente la etiqueta. La regeneración es una elección del usuario mediante
el flujo existente. Las fuentes son visibles en Mi entrenamiento.

## Pendientes que impiden llamarlo validación clínica

No hay aval, certificación ni revisión profesional de los planes concretos.
El catálogo, las sustituciones, las estimaciones de tiempo, el esfuerzo por nivel
y esta traducción de evidencia necesitan revisión de un profesional del ejercicio.
No hay cribado clínico; el aviso visible no sustituye ese cribado. No se ha validado
para menores, embarazo, rehabilitación o enfermedades. Falta un protocolo específico
de equilibrio para quien lo necesite y una auditoría de volumen por músculo (las
series multiarticulares no se pueden contar automáticamente como equivalentes).
No afirmar cumplimiento íntegro de OMS/ACSM, seguridad individual ni resultados
garantizados. Las pruebas de software verifican reglas, no eficacia fisiológica.
