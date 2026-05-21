"""
Wrapper seguro de st.cache_data que funciona fuera del contexto de Streamlit.
Permite testear modulos sin tener Streamlit corriendo.
"""

try:
    from streamlit import cache_data as _streamlit_cache_data
except ImportError:
    _streamlit_cache_data = None


def cached(ttl: int = 300, max_entries: int = 32):
    """Cachea resultados con st.cache_data si esta disponible.

    Fuera de Streamlit se comporta como un passthrough (no cachea).

    Args:
        ttl: Tiempo de vida en segundos (default 5 min).
        max_entries: Maximo de entradas en cache.
    """
    def decorator(func):
        if _streamlit_cache_data is not None:
            return _streamlit_cache_data(ttl=ttl, max_entries=max_entries)(func)
        return func
    return decorator
