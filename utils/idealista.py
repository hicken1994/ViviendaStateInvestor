import logging
import os
import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Any

import requests

logger = logging.getLogger(__name__)

RAPIDAPI_HOST = "idealista17.p.rapidapi.com"
CACHE_DB = "real_estate.db"
CACHE_TTL_SECONDS = 3600
FALLBACK_BARRIOS_MADRID = [
    "Salamanca", "Chamberí", "Centro", "Retiro", "Arganzuela",
    "Chamartín", "Tetuán", "Fuencarral", "Moncloa", "Latina",
    "Carabanchel", "Usera", "Ciudad Lineal", "Hortaleza",
    "Villaverde", "Moratalaz", "Vicálvaro", "San Blas",
    "Barajas", "Puente de Vallecas", "Villa de Vallecas",
]


def _get_rapidapi_key() -> str | None:
    try:
        import streamlit as st
        key = st.secrets.get("RAPIDAPI_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("RAPIDAPI_KEY")


def is_configured() -> bool:
    return _get_rapidapi_key() is not None


class IdealistaError(Exception):
    pass


def _ensure_cache_table():
    conn = sqlite3.connect(CACHE_DB)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS idealista_cache (
                cache_key TEXT PRIMARY KEY,
                response_json TEXT NOT NULL,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
    finally:
        conn.close()


def _cache_get(cache_key: str) -> dict | None:
    _ensure_cache_table()
    conn = sqlite3.connect(CACHE_DB)
    try:
        row = conn.execute(
            "SELECT response_json, fetched_at FROM idealista_cache WHERE cache_key = ?",
            (cache_key,),
        ).fetchone()
        if row:
            fetched = datetime.fromisoformat(row[1])
            if datetime.now() - fetched < timedelta(seconds=CACHE_TTL_SECONDS):
                return json.loads(row[0])
    except Exception as e:
        logger.warning("Cache read error: %s", e)
    finally:
        conn.close()
    return None


def _cache_set(cache_key: str, data: dict):
    _ensure_cache_table()
    conn = sqlite3.connect(CACHE_DB)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO idealista_cache (cache_key, response_json, fetched_at) VALUES (?, ?, ?)",
            (cache_key, json.dumps(data), datetime.now().isoformat()),
        )
        conn.commit()
    except Exception as e:
        logger.warning("Cache write error: %s", e)
    finally:
        conn.close()


def _request(endpoint: str, params: dict | None = None) -> dict:
    api_key = _get_rapidapi_key()
    if not api_key:
        raise IdealistaError("RAPIDAPI_KEY not configured")

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }

    url = f"https://{RAPIDAPI_HOST}{endpoint}"
    resp = requests.get(url, headers=headers, params=params, timeout=15)

    if resp.status_code == 429:
        raise IdealistaError("Rate limit exceeded")
    if resp.status_code == 403:
        raise IdealistaError("Invalid API key or plan limit reached")
    if resp.status_code != 200:
        raise IdealistaError(f"API error {resp.status_code}: {resp.text[:200]}")

    return resp.json()


def _cache_key(endpoint: str, params: dict | None = None) -> str:
    raw = endpoint + json.dumps(params or {}, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def property_search(
    location_id: str = "0-EU-ES-01",
    operation: str = "sale",
    property_type: str = "homes",
    max_items: int = 50,
    num_page: int = 1,
    **kwargs,
) -> dict:
    cache_key = _cache_key("/property-search", {
        "locationId": location_id, "operation": operation,
        "propertyType": property_type, "maxItems": max_items,
        "numPage": num_page, **kwargs,
    })

    cached = _cache_get(cache_key)
    if cached:
        return cached

    result = _request("/property-search", {
        "locationId": location_id, "operation": operation,
        "propertyType": property_type, "maxItems": max_items,
        "numPage": num_page, **kwargs,
    })

    _cache_set(cache_key, result)
    return result


def property_details(property_code: str) -> dict:
    cache_key = _cache_key("/property-details", {"propertyCode": property_code})
    cached = _cache_get(cache_key)
    if cached:
        return cached

    result = _request("/property-details", {"propertyCode": property_code})
    _cache_set(cache_key, result)
    return result


def auto_complete(text: str) -> list[dict]:
    cache_key = _cache_key("/auto-complete", {"text": text})
    cached = _cache_get(cache_key)
    if cached:
        return cached.get("locations", [])

    result = _request("/auto-complete", {"text": text})
    _cache_set(cache_key, result)
    return result.get("locations", [])


def search_by_coordinates(
    latitude: float,
    longitude: float,
    radius_meters: int = 1000,
    operation: str = "sale",
    max_items: int = 50,
) -> dict:
    cache_key = _cache_key("/property-search-by-coordinates", {
        "latitude": latitude, "longitude": longitude,
        "radius": radius_meters, "operation": operation,
        "maxItems": max_items,
    })
    cached = _cache_get(cache_key)
    if cached:
        return cached

    result = _request("/property-search-by-coordinates", {
        "latitude": latitude, "longitude": longitude,
        "radius": radius_meters, "operation": operation,
        "maxItems": max_items,
    })
    _cache_set(cache_key, result)
    return result


def _map_idealista_property(item: dict) -> dict:
    price = item.get("price", 0)
    size = item.get("size", 0) or 0
    price_m2 = round(price / size, 2) if size > 0 else 0

    neighborhood = item.get("neighborhood", "")
    district = item.get("district", "")
    property_code = str(item.get("propertyCode", ""))

    rooms = item.get("rooms", 0) or 0
    bathrooms = item.get("bathrooms", 0) or 0
    floor = item.get("floor", "")
    exterior = item.get("exterior", False)
    status = item.get("status", "")
    description = item.get("description", "")
    photos = item.get("multimedia", {}).get("images", [])
    image_url = photos[0].get("url", "") if photos else ""
    latitude = item.get("latitude")
    longitude = item.get("longitude")

    return {
        "propiedad_id": property_code,
        "idealista_id": property_code,
        "barrio": neighborhood or district or "Madrid",
        "distrito": district or "",
        "precio_total": price,
        "precio_m2": price_m2,
        "metros": size,
        "habitaciones": rooms,
        "banos": bathrooms,
        "planta": floor,
        "exterior": exterior,
        "estado": status,
        "descripcion": description,
        "image_url": image_url,
        "latitud": latitude,
        "longitud": longitude,
        "precio_m2_barrio": 0,
        "descuento_pct": 0,
        "dias": 0,
        "noise_score": 50,
        "fuente": "Idealista API",
        "is_premium": 1,
    }


def search_madrid_properties(
    operation: str = "sale",
    max_items: int = 50,
    num_page: int = 1,
) -> list[dict]:
    result = property_search(
        location_id="0-EU-ES-01",
        operation=operation,
        property_type="homes",
        max_items=max_items,
        num_page=num_page,
    )
    element_list = result.get("elementList", [])
    return [_map_idealista_property(item) for item in element_list]


def bulk_search_madrid(
    operation: str = "sale",
    total_desired: int = 100,
) -> list[dict]:
    all_properties = []
    page = 1
    max_pages = 5

    while len(all_properties) < total_desired and page <= max_pages:
        try:
            batch = search_madrid_properties(
                operation=operation,
                max_items=50,
                num_page=page,
            )
            if not batch:
                break
            all_properties.extend(batch)
            page += 1
        except IdealistaError as e:
            logger.warning("Idealista bulk search stopped: %s", e)
            break

    return all_properties[:total_desired]
