import re, sys
sys.path.insert(0, '.')
with open('.streamlit/secrets.toml') as f:
    content = f.read()
url = re.search(r'SUPABASE_URL\s*=\s*"([^"]+)"', content).group(1)
key = re.search(r'SUPABASE_SERVICE_ROLE_KEY\s*=\s*"([^"]+)"', content).group(1)

from supabase import create_client
sb = create_client(url, key)

for attr in sorted(dir(sb)):
    if not attr.startswith('_'):
        print(f'  {attr}')
