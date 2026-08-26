# -*- coding: utf-8 -*-
"""
Tavily Web Search Servisi

Sirket isimlerinden Tavily arama API'si ile web'de arama yapip
resmi site domain'lerini dinamik olarak getirir.

API dokumani: https://docs.tavily.com/documentation/api-reference/endpoint/search
"""

import json
import os
import urllib.parse
import urllib.request

TAVILY_SEARCH_URL = "https://api.tavily.com/search"
REQUEST_TIMEOUT = 15


def load_env(env_path=".env"):
  """Basit .env loader — KEY=VALUE satirlarini ortam degiskenlerine yukler."""
  if not os.path.exists(env_path):
    return
  with open(env_path, "r", encoding="utf-8") as f:
    for line in f:
      line = line.strip()
      if not line or line.startswith("#") or "=" not in line:
        continue
      key, _, value = line.partition("=")
      os.environ.setdefault(key.strip(), value.strip())


def get_tavily_api_key():
  api_key = os.environ.get("TAVILY_API_KEY")
  if not api_key:
    raise ValueError(
        "TAVILY_API_KEY bulunamadi. .env dosyasinda tanimlayin."
    )
  return api_key


def _tavily_search(query, max_results=5):
  """Tavily search API'sine istek atip sonuclari dondurur."""
  payload = {
      "api_key": get_tavily_api_key(),
      "query": query,
      "search_depth": "basic",
      "max_results": max_results,
      "include_answer": False,
  }
  req = urllib.request.Request(
      TAVILY_SEARCH_URL,
      data=json.dumps(payload).encode("utf-8"),
      headers={"Content-Type": "application/json"},
      method="POST",
  )
  with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
    return json.loads(response.read().decode("utf-8"))


def extract_domain(url):
  """URL'den scheme/path temizlenmis domain dondurur."""
  parsed = urllib.parse.urlparse(url)
  host = parsed.netloc or parsed.path
  return host.lower().removeprefix("www.")


def find_company_domain(company_name, max_results=5):
  """
  Sirket adiyla Tavily'de arar, resmi siteyi bulmaya calisir.

  Oncelik "official site" sorgusuyla gelen ilk sonuca verilir;
  bulunamazsa None dondurur.
  """
  query = f"{company_name} official website Turkey"
  try:
    results = _tavily_search(query, max_results=max_results)
  except urllib.error.HTTPError as e:
    print(f"  [!] Tavily HTTP hatasi ({company_name}): {e.code}")
    return None
  except Exception as e:
    print(f"  [!] Tavily hatasi ({company_name}): {e}")
    return None

  for item in results.get("results", []):
    domain = extract_domain(item.get("url", ""))
    if domain:
      return domain
  return None


def find_domains_for_companies(company_names):
  """
  {kategori: [sirket_adi, ...]} yapisi alir,
  {kategori: [domain, ...]} yapisi dondurur.
  """
  resolved = {}
  for category, names in company_names.items():
    print(f"\n--- {category} (Tavily ile domain cozumleniyor) ---")
    domains = []
    for name in names:
      domain = find_company_domain(name)
      if domain:
        print(f"  + {name} -> {domain}")
        domains.append(domain)
      else:
        print(f"  - {name} -> bulunamadi")
    resolved[category] = domains
  return resolved
