# -*- coding: utf-8 -*-
"""
Hunter.io Toplu E-Posta Tarayıcı ve BCC Liste Oluşturucu
"""

import json
import os
import time
import urllib.parse
import urllib.request

import tavily_service

tavily_service.load_env()
API_KEY = os.environ.get("HUNTER_API_KEY", "api_key")

COMPANY_NAMES = {
    "Teknopark Yonetimleri": [
        "Bilisim Vadisi",
        "ODTU Teknokent",
        "Cyberpark Ankara",
        "ITU Teknokent",
        "Yildiz Teknopark",
        "Gaziantep Teknopark",
        "Ege Teknopark",
        "IYTE Teknopark",
        "Samsun Teknopark",
        "Trabzon Teknokent",
        "Giresun Teknopark",
        "Antalya Teknokent",
        "Mersin Teknopark",
        "Cukurova Teknokent",
        "Sakarya Teknokent",
        "Kocaeli Teknopark",
        "Bursa Teknopark",
        "Anadolu Teknokent",
        "Erciyes Teknopark",
        "Gaziantepteknopark",
    ],
    "E-Ticaret & SaaS Platformlari": [
        "Trendyol",
        "Hepsiburada",
        "Getir",
        "Insider",
        "Yemeksepeti",
        "N11",
        "Ciceksepeti",
        "Letgo",
        "Sahibinden",
        "Arabam",
        "Enuygun",
        "Obilet",
        "Armut",
        "Modanisa",
        "LC Waikiki",
        "Defacto",
    ],
    "Bankacilik & Fintek": [
        "Garanti BBVA",
        "Isbank",
        "Akbank",
        "Yapi Kredi",
        "QNB Finansbank",
        "Denizbank",
        "Vakifbank",
        "Halkbank",
        "Ziraat Bankasi",
        "Softtech",
        "Papara",
        "Param",
        "Iyzico",
        "PayTR",
        "Ininal",
        "Veripark",
        "Intertech",
        "Architecht",
        "Paycell",
        "Tosla",
    ],
    "Kurumsal Yazilim & Bilisim": [
        "Bilgeadam",
        "OBSS",
        "Koc Sistem",
        "D Teknoloji",
        "Innova",
        "Logo Yazilim",
        "Basarsoft",
        "Akinsoft",
        "Dias Teknoloji",
        "Etiya",
        "Evam",
        "Commencis",
        "Foreks",
        "Matriks Data",
        "Smartpulse",
        "Solvoyo",
        "Bites",
        "Milsoft",
        "Simsoft",
        "Argela",
        "Netaş",
        "Karel",
        "Etas Bilgisayar",
        "Mikro Yazilim",
        "Zirve Yazilim",
    ],
    "Telekomunikasyon": [
        "Turkcell",
        "Turk Telekom",
        "Vodafone Turkey",
        "Turknet",
        "Millenicom",
        "Turksat",
    ],
    "Savunma Sanayi & Muhendislik": [
        "Aselsan",
        "Havelsan",
        "TUSAŞ",
        "Baykar",
        "Roketsan",
        "STM",
        "TEI",
        "Kale Havacilik",
        "FNSS",
        "Otokar",
    ],
    "Holdingler": [
        "Koc Holding",
        "Sabanci Holding",
        "Zorlu Holding",
        "Vestel",
        "Demiroren Group",
        "Eczacibasi",
        "Dogus Group",
        "Borusan",
        "Sisecam",
        "Anadolu Group",
        "Kibar Holding",
        "Akkim Akkok Holding",
        "Yildiz Holding",
    ],
}


def fetch_company_emails(domain):
  url = (
      f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={API_KEY}"
  )
  req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
  try:
    with urllib.request.urlopen(req, timeout=10) as response:
      data = json.loads(response.read().decode("utf-8"))
      return data.get("data", {}).get("emails", [])
  except urllib.error.HTTPError as e:
    if e.code == 429:
      print("  [!] Rate Limit. 5 sn bekleniyor...")
      time.sleep(5)
    else:
      print(f"  [-] HTTP Hatasi ({domain}): {e.code}")
    return []
  except Exception as e:
    print(f"  [-] Hata ({domain}): {e}")
    return []


def main():
  all_emails = []
  company_domains = tavily_service.find_domains_for_companies(COMPANY_NAMES)
  total = sum(len(v) for v in company_domains.values())
  idx = 0

  print(f"\nTarama basliyor... Toplam {total} domain sorgulanacak.\n")

  for cat, domains in company_domains.items():
    print(f"\n--- {cat} ---")
    for domain in domains:
      idx += 1
      print(f"[{idx}/{total}] {domain} taraniyor...")
      emails = fetch_company_emails(domain)
      for item in emails:
        email_addr = item.get("value")
        pos = item.get("position") or "Belirtilmemis"
        if email_addr:
          all_emails.append(email_addr)
          print(f"   + {email_addr} ({pos})")
      time.sleep(0.4)

  unique_emails = sorted(list(set(all_emails)))
  with open("toplu_bcc_listesi.txt", "w", encoding="utf-8") as f:
    f.write(", ".join(unique_emails))

  print(f"\n[+] Tamamlandi! {len(unique_emails)} adres toplu_bcc_listesi.txt dosyasina yazildi.")


if __name__ == "__main__":
  main()
