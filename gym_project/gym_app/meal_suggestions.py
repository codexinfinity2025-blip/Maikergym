"""Ideas culinarias flexibles: ingredientes y dos alternativas, no prescripciones."""

IDEAS = {
    'Desayuno': [
        ('Huevo|Aguacate|Pan integral|Tomate', 'Tostadas con huevo y aguacate', 'Sándwich de huevo y tomate con aguacate'),
        ('Avena|Yogur natural|Banano|Maní', 'Avena fría con yogur y banano', 'Bowl de yogur, avena y maní con banano'),
        ('Arepa|Pollo desmechado|Tomate|Queso fresco', 'Arepa rellena de pollo y tomate', 'Arepa con queso fresco y pollo desmechado'),
        ('Atún|Pan integral|Pepino|Aguacate', 'Tostadas de atún con aguacate', 'Sándwich de atún y pepino'),
        ('Huevo|Espinaca|Tortilla de maíz|Tomate', 'Tacos de huevo con espinaca', 'Omelette de espinaca y tomate con tortilla'),
        ('Leche|Avena|Manzana|Canela', 'Avena cocida con manzana y canela', 'Batido de leche, avena y manzana'),
        ('Fríjoles cocidos|Arroz cocido|Huevo|Tomate', 'Calentado de arroz y fríjoles con huevo', 'Bowl de fríjoles y arroz con huevo revuelto y tomate'),
    ],
    'Almuerzo': [
        ('Pollo|Arroz|Zanahoria|Brócoli', 'Bowl de pollo, arroz y verduras', 'Arroz salteado con pollo, zanahoria y brócoli'),
        ('Lentejas|Papa|Zanahoria|Tomate', 'Lentejas guisadas con papa y zanahoria', 'Ensalada tibia de lentejas y papa con tomate'),
        ('Pescado|Papa|Pepino|Limón', 'Pescado a la plancha con papa y ensalada de pepino', 'Bowl de pescado desmenuzado y papa con pepino y limón'),
        ('Carne magra|Arroz|Pimentón|Calabacín', 'Carne salteada con verduras y arroz', 'Pimentones rellenos de carne y arroz con calabacín'),
        ('Garbanzos|Arroz|Espinaca|Tomate', 'Garbanzos salteados con espinaca y arroz', 'Bowl de arroz y garbanzos con tomate y espinaca'),
        ('Atún|Pasta integral|Tomate|Zanahoria', 'Pasta con atún y tomate', 'Ensalada de pasta con atún y zanahoria'),
        ('Pollo|Batata|Lechuga|Aguacate', 'Pollo al horno con batata y ensalada', 'Ensalada de pollo y aguacate con batata asada'),
    ],
    'Merienda': [
        ('Yogur natural|Fresas|Avena', 'Yogur con fresas y avena', 'Batido de yogur y fresas con avena'),
        ('Manzana|Maní|Yogur natural', 'Manzana en trozos con yogur y maní', 'Vasito de yogur con manzana rallada y maní'),
        ('Queso fresco|Pan integral|Tomate', 'Tostada con queso fresco y tomate', 'Sándwich pequeño de queso y tomate'),
        ('Banano|Leche|Cacao sin azúcar', 'Batido de banano, leche y cacao', 'Banano con cacao y un vaso de leche'),
        ('Garbanzos cocidos|Limón|Pepino|Pan integral', 'Crema de garbanzos al limón con pepino', 'Tostada con garbanzos machacados y pepino'),
        ('Papaya|Yogur natural|Semillas de chía', 'Bowl de papaya con yogur y chía', 'Batido de papaya y yogur con chía hidratada'),
        ('Pera|Queso fresco|Nueces', 'Pera con queso fresco y nueces', 'Ensalada de pera y queso con nueces picadas'),
    ],
    'Cena': [
        ('Huevo|Papa|Espinaca|Tomate', 'Tortilla de papa y espinaca con tomate', 'Papa cocida con huevo revuelto y ensalada de espinaca'),
        ('Pollo|Tortilla integral|Lechuga|Aguacate', 'Wrap de pollo y aguacate', 'Tacos de pollo con lechuga y aguacate'),
        ('Fríjoles|Arepa|Queso fresco|Tomate', 'Arepa con fríjoles y queso', 'Bowl de fríjoles y tomate con arepa y queso'),
        ('Pescado|Arroz|Calabacín|Zanahoria', 'Pescado al horno con arroz y verduras', 'Arroz con pescado desmenuzado y verduras salteadas'),
        ('Garbanzos|Papa|Tomate|Espinaca', 'Guiso de garbanzos con papa y espinaca', 'Ensalada tibia de papa y garbanzos con tomate'),
        ('Atún|Huevo|Lechuga|Pan integral', 'Ensalada de atún y huevo con tostada', 'Sándwich de atún, huevo y lechuga'),
        ('Pollo|Auyama|Zanahoria|Papa', 'Sopa de pollo con papa y verduras', 'Crema de auyama y zanahoria con pollo y papa'),
    ],
}


def comidas_del_dia(indice, objetivo):
    # Rotación determinista por objetivo, conservando variedad durante los siete días.
    desplazamiento = {'salud': 0, 'hipertrofia': 1, 'estetico': 2, 'perder_peso': 3}.get(objetivo, 0)
    resultado = []
    for nombre, ideas in IDEAS.items():
        alimentos, opcion_a, opcion_b = ideas[(indice + desplazamiento) % len(ideas)]
        resultado.append({'nombre': nombre, 'alimentos': alimentos.split('|'), 'opciones': [opcion_a, opcion_b]})
    return resultado
