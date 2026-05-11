"""
Banco de imágenes inmobiliarias realistas para Madrid.
Cada barrio tiene múltiples opciones; se elige una por propiedad
usando un hash determinístico basado en el índice de la fila.
"""

import hashlib

# Imágenes de edificios y apartamentos reales (Unsplash)
# Prioridad: fotos de Madrid + edificios residenciales realistas
IMAGE_POOL = [
    # Verified working Unsplash photos (buildings + apartments realistas)
    "https://images.unsplash.com/photo-1580587771525-78b9dba3b914",  # building facade
    "https://images.unsplash.com/photo-1568605114967-8130f3a36994",  # modern building
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c",  # luxury home
    "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9",  # modern house
    "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c",  # architectural house
    "https://images.unsplash.com/photo-1505691938895-1758d7feb511",  # bedroom (verified)
    "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde",  # white building
    "https://images.unsplash.com/photo-1493809842364-78817add7ffb",  # living room (verified)
    "https://images.unsplash.com/photo-1564013799919-ab600027ffc6",  # beautiful home
    "https://images.unsplash.com/photo-1484154218962-a197022b5858",  # kitchen (verified)
    "https://images.unsplash.com/photo-1507089947368-19c1da9775ae",  # bathroom (verified)
    "https://images.unsplash.com/photo-1600585153490-76fb20a32601",  # modern apartment
    "https://images.unsplash.com/photo-1600573472550-8090b5e0745e",  # city building
    "https://images.unsplash.com/photo-1600585154084-4e5fe7c39198",  # luxury villa
    "https://images.unsplash.com/photo-1508609349937-5ec4ae374ebf",  # window view (verified)
    "https://images.unsplash.com/photo-1523217582562-09d0def993a6",  # apartment (verified)
    "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2",  # cozy apartment (verified)
    "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267",  # colorful room (verified)
    "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688",  # modern loft (verified)
    "https://images.unsplash.com/photo-1554995207-c18c203602cb",  # couch (verified)
]

# Agrupación por barrio — cada uno tiene un subset del pool
# Así propiedades del mismo barrio comparten estilo visual
BARRIO_IMAGE_INDICES = {
    "Salamanca": [0, 3, 12, 8],
    "Chamberí": [1, 7, 10, 16],
    "Centro": [2, 9, 13, 17],
    "Retiro": [0, 5, 14, 18],
    "Arganzuela": [3, 6, 11, 19],
    "Chamartín": [4, 8, 15, 0],
    "Tetuán": [5, 9, 12, 1],
    "Fuencarral": [6, 10, 13, 2],
    "Moncloa": [7, 11, 14, 3],
    "Latina": [1, 4, 8, 16],
    "Carabanchel": [2, 5, 9, 17],
    "Usera": [3, 6, 10, 18],
    "Ciudad Lineal": [4, 7, 11, 19],
    "Hortaleza": [0, 8, 12, 15],
    "Villaverde": [1, 9, 13, 14],
    "Moratalaz": [2, 10, 14, 16],
    "Vicálvaro": [3, 11, 15, 17],
    "San Blas": [4, 12, 16, 18],
    "Barajas": [5, 13, 17, 19],
    "Puente de Vallecas": [6, 14, 18, 0],
    "Villa de Vallecas": [7, 15, 19, 1],
}

DEFAULT_IMAGE = IMAGE_POOL[0]


def _pick_image(barrio: str, seed: int) -> str:
    """Elige una imagen del barrio usando un seed determinístico."""
    indices = BARRIO_IMAGE_INDICES.get(barrio)
    if not indices:
        return DEFAULT_IMAGE
    # Hash determinístico para variedad entre propiedades
    idx = indices[seed % len(indices)]
    return IMAGE_POOL[idx]


def add_images(df):
    """Agrega columna image_url con imágenes realistas por barrio."""
    df = df.copy()
    df["image_url"] = df.apply(
        lambda row: _pick_image(
            row.get("barrio", ""),
            row.name if hasattr(row, "name") and isinstance(row.name, int) else hash(str(row.get("precio_total", ""))),
        ),
        axis=1,
    )
    return df
