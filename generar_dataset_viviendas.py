import pandas as pd
import random

barrios = [
"Salamanca","Chamberí","Retiro","Chamartín","Tetuán",
"Centro","Arganzuela","Moncloa","Latina","Carabanchel",
"Usera","Puente de Vallecas","Moratalaz","Ciudad Lineal",
"Hortaleza","Villaverde","Villa de Vallecas","Vicálvaro",
"San Blas","Barajas"
]

data = []

for i in range(3000):

    barrio = random.choice(barrios)
    metros = random.randint(40,150)
    habitaciones = random.randint(1,5)

    precio_m2_barrio = random.randint(2500,7000)

    variacion = random.uniform(-0.2,0.2)

    precio_m2 = precio_m2_barrio * (1+variacion)

    precio_total = int(precio_m2 * metros)

    data.append({
        "BARRIO": barrio,
        "METROS": metros,
        "HABITACIONES": habitaciones,
        "PRECIO_TOTAL": precio_total,
        "PRECIO_M2": round(precio_m2,2),
        "PRECIO_M2_BARRIO": precio_m2_barrio,
        "DIFERENCIA": round(precio_m2-precio_m2_barrio,2)
    })

df = pd.DataFrame(data)

df["DESCRIPCION_IA"] = (
    "Vivienda en " + df["BARRIO"] +
    ". Precio " + df["PRECIO_TOTAL"].astype(str) +
    " euros. " + df["METROS"].astype(str) +
    " metros cuadrados. " + df["HABITACIONES"].astype(str) +
    " habitaciones. Precio m2 " + df["PRECIO_M2"].astype(str)
)

df.to_csv("dataset_viviendas_madrid_3000.csv", index=False)

print("Dataset creado con 3000 viviendas")