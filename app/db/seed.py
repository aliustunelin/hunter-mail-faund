# -*- coding: utf-8 -*-
"""Başlangıç kategori/şirket verisini yükler (eski main.py'deki COMPANY_NAMES)."""

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.core.logging import get_logger
from app.models.entities import Category, Company

logger = get_logger(__name__)

SEED_CATEGORIES = {
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


def run(session_factory: sessionmaker) -> None:
    """Kategori ve şirketleri idempotent şekilde ekler; var olanları atlar."""
    db: Session = session_factory()
    try:
        added = 0
        for category_name, company_names in SEED_CATEGORIES.items():
            category = db.scalars(
                select(Category).where(Category.name == category_name)
            ).first()
            if category is None:
                category = Category(name=category_name)
                db.add(category)
                db.flush()

            existing = set(
                db.scalars(
                    select(Company.name).where(Company.category_id == category.id)
                ).all()
            )
            for name in company_names:
                if name in existing:
                    continue
                db.add(Company(name=name, category_id=category.id))
                added += 1
        db.commit()
        if added:
            logger.info("Seed tamamlandi: %d yeni sirket eklendi.", added)
    finally:
        db.close()
