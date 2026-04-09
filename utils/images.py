BARRIO_IMAGES = {
    "Salamanca": "https://images.unsplash.com/photo-1505691938895-1758d7feb511",
    "Chamberí": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2",
    "Centro": "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267",
    "Tetuán": "https://images.unsplash.com/photo-1493809842364-78817add7ffb",
    "Carabanchel": "https://images.unsplash.com/photo-1484154218962-a197022b5858",
    "Usera": "https://images.unsplash.com/photo-1507089947368-19c1da9775ae",
    "Retiro": "https://images.unsplash.com/photo-1508609349937-5ec4ae374ebf",
    "Arganzuela": "https://images.unsplash.com/photo-1523217582562-09d0def993a6",
    "Latina": "https://images.unsplash.com/photo-1560185008-5f44982808b6",
    "Moncloa": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688",
    "Fuencarral": "https://images.unsplash.com/photo-1554995207-c18c203602cb",
    "Hortaleza": "https://images.unsplash.com/photo-1505691723518-36a5ac3b2d52",
    "Chamartín": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750",
    "Villaverde": "https://images.unsplash.com/photo-1570129477492-45c003edd2be",
    "Moratalaz": "https://images.unsplash.com/photo-1487014679447-9f8336841d58",
    "Vicálvaro": "https://images.unsplash.com/photo-1501870190083-5a25e7a1e072",
    "San Blas": "https://images.unsplash.com/photo-1449844908441-8829872d2607",
    "Barajas": "https://images.unsplash.com/photo-1501183638710-841dd1904471",
    "Puente de Vallecas": "https://images.unsplash.com/photo-1519710164239-da123dc03ef4",
    "Villa de Vallecas": "https://images.unsplash.com/photo-1507086182423-c8b20045fd2a",
    "Ciudad Lineal": "https://images.unsplash.com/photo-1560448075-bb485b067938",
}

DEFAULT_IMAGE = "https://images.unsplash.com/photo-1560448075-bb485b067938"


def add_images(df):
    df = df.copy()
    df["image_url"] = df.apply(
        lambda row: BARRIO_IMAGES.get(row.get("barrio", ""), DEFAULT_IMAGE),
        axis=1
    )
    return df
