# 🕸️ IYTE Web Scraper & Search Engine

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-5-C51A4A?style=for-the-badge&logo=raspberry-pi&logoColor=white)](https://www.raspberrypi.com)

**İzmir Yüksek Teknoloji Enstitüsü** web ekosistemini tarayan, verileri indeksleyen ve milisaniyeler içinde arama yapabilen profesyonel bir veri madenciliği aracıdır.

---

### 🚀 Temel Yetenekler

> [!TIP]
> **Kaldığı Yerden Devam Etme:** Elektrik kesilse veya tarama durdurulsa bile, sistem veritabanını kontrol ederek otomatik olarak en son bulduğu taranmamış linke döner.

- **🎯 Akıllı Filtreleme:** Sadece `iyte.edu.tr` domainine odaklanır, dış bağlantıları sadece referans olarak tutar.
- **⚡ Hızlı Sorgu:** SQL `LIKE` operatörü ve optimize edilmiş sorgularla devasa veri içinde anlık arama.
- **🛡️ Hata Toleransı:** `urllib3` ve `requests` katmanlarında otomatik yeniden deneme (retry) yapılandırması.

---

### 📂 Dosya Mimarisi

| Dosya Adı | Rolü | Teknoloji |
| :--- | :--- | :--- |
| `scrapermain.py` | **Crawler Engine** | BeautifulSoup4, Requests |
| `search_engine.py` | **Search UI** | SQLite3, Sys |
| `usedb.py` | **Data Checker** | SQLite3 |
| `.gitignore` | **Safety** | Git Rules |

---

### 🛠️ Kurulum Rehberi

1️⃣ **Bağımlılıkları Yükleyin:**
```bash
pip install beautifulsoup4 requests urllib3
2️⃣ Tarama Motorunu Çalıştırın:

Bash

python3 scrapermain.py
3️⃣ Verilerde Arama Yapın:

Bash

python3 search_engine.py "akademik takvim"
📊 Veritabanı Yapısı
Kod snippet'i

graph LR
    A[HTML Content] --> B{Parser}
    B --> C[(Pages Table)]
    B --> D[(Links Table)]
    C --> E[Search Engine]
[!IMPORTANT] Bu uygulama eğitim amaçlıdır. Sunucu yükünü minimize etmek için istekler arasında 0.5s bekleme süresi (delay) eklenmiştir.
