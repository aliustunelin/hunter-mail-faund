# -*- coding: utf-8 -*-
"""
Hunter.io Toplu E-Posta Tarayıcı ve BCC Liste Oluşturucu
"""

import json
import time
import urllib.parse
import urllib.request

API_KEY = "api_key"

COMPANY_DOMAINS = {
    "Teknopark Yonetimleri": [
        "bilisimvadisi.com.tr",
        "odtuteknokent.com.tr",
        "cyberpark.com.tr",
        "teknokent.itu.edu.tr",
        "yildizteknopark.com.tr",
        "gasteknopark.com.tr",
        "egeteknopark.com.tr",
        "iyte.edu.tr",
        "samsunteknopark.com",
        "trabzonteknokent.com.tr",
        "giresunteknopark.com.tr",
        "antalyateknokent.com.tr",
        "mersinteknopark.com.tr",
        "cukurovateknokent.com.tr",
        "sakaryateknokent.com.tr",
        "kocaeliteknopark.com",
        "bursateknopark.com",
        "anadoluteknokent.com.tr",
        "erciyesteknopark.com",
        "gaziantepteknopark.com.tr",
    ],
    "E-Ticaret & SaaS Platformlari": [
        "trendyol.com",
        "hepsiburada.com",
        "getir.com",
        "useinsider.com",
        "yemeksepeti.com",
        "n11.com",
        "ciceksepeti.com",
        "letgo.com",
        "sahibinden.com",
        "arabam.com",
        "enuygun.com",
        "obilet.com",
        "armut.com",
        "modanisa.com",
        "lcwaikiki.com",
        "defacto.com",
    ],
    "Bankacilik & Fintek": [
        "garantibbva.com.tr",
        "isbank.com.tr",
        "akbank.com",
        "yapikredi.com.tr",
        "qnbfinansbank.com",
        "denizbank.com",
        "vakifbank.com.tr",
        "halkbank.com.tr",
        "ziraatbank.com.tr",
        "softtech.com.tr",
        "papara.com",
        "param.com.tr",
        "iyzico.com",
        "paytr.com",
        "ininal.com",
        "veripark.com",
        "intertech.com.tr",
        "architecht.com",
        "paycell.com.tr",
        "tosla.com",
    ],
    "Kurumsal Yazilim & Bilisim": [
        "bilgeadam.com",
        "obss.tech",
        "kocsistem.com.tr",
        "d-teknoloji.com.tr",
        "innova.com.tr",
        "logo.com.tr",
        "basarsoft.com.tr",
        "akinsoft.com.tr",
        "diasteknoloji.com",
        "etiya.com",
        "evam.com",
        "commencis.com",
        "foreks.com",
        "matriksdata.com",
        "smartpulse.io",
        "solvoyo.com",
        "bites.com.tr",
        "milsoft.com.tr",
        "simsoft.com.tr",
        "argela.com.tr",
        "netas.com.tr",
        "karel.com.tr",
        "etasbilgisayar.com",
        "mikro.com.tr",
        "zirveyazilim.net",
    ],
    "Telekomunikasyon": [
        "turkcell.com.tr",
        "turktelekom.com.tr",
        "vodafone.com.tr",
        "turknet.net.tr",
        "milleni.com.tr",
        "turksat.com.tr",
    ],
    "Savunma Sanayi & Muhendislik": [
        "aselsan.com.tr",
        "havelsan.com.tr",
        "tusas.com",
        "baykartech.com",
        "roketsan.com.tr",
        "stm.com.tr",
        "tei.com.tr",
        "kalehavacilik.com",
        "fnss.com.tr",
        "otokar.com.tr",
    ],
    "Holdingler": [
        "koc.com.tr",
        "sabanci.com",
        "zorlu.com",
        "vestel.com.tr",
        "demirorengroup.com",
        "eczacibasi.com.tr",
        "dogusgrubu.com.tr",
        "borusan.com",
        "sisecam.com",
        "anadolugrubu.com.tr",
        "kibar.com",
        "akkok.com.tr",
        "yildizholding.com.tr",
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
  total = sum(len(v) for v in COMPANY_DOMAINS.values())
  idx = 0

  print(f"Tarama basliyor... Toplam {total} domain sorgulanacak.\n")

  for cat, domains in COMPANY_DOMAINS.items():
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
