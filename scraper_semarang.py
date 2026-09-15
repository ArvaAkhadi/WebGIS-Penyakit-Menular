# -*- coding: utf-8 -*-
"""
============================================================
 SCRAPER DATA WEBGIS DINAMIKA PENYAKIT MENULAR KOTA SEMARANG
 ------------------------------------------------------------
 Sumber   : https://lekminkes.dinkes.semarangkota.go.id/
 Penyakit : Leptospirosis, TB Baru (kasus_tb_baru), DBD
 Periode  : 2019 – 2026
 Author   : (isi sendiri)

 Cara pakai:
     pip install requests pyproj
     python scraper_semarang.py

 Output (folder "data/"):
     data/
       ├── puskesmas.geojson              <-- SUDAH di-reproject ke WGS84
       ├── leptospirosis/
       │     ├── map_2019.json ... map_2026.json
       │     ├── bar_2019.json ... bar_2026.json
       │     └── line_2019.json ... line_2026.json
       ├── tb_baru/
       │     └── (sama)
       └── dbd/
             └── (sama)
============================================================
"""

import os
import re
import json
import time
import traceback

import requests

# pyproj dipakai untuk reproject GeoJSON dari UTM ke WGS84
try:
    from pyproj import Transformer
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False
    print("[PERINGATAN] pyproj belum terinstall. Jalankan: pip install pyproj")
    print("             GeoJSON akan disimpan mentah (EPSG:32749) dan peta TIDAK akan muncul di Leaflet.\n")

import os
import certifi

# Memaksa requests menggunakan certifi CA bundle yang valid
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
os.environ['CURL_CA_BUNDLE'] = certifi.where()

# ============================================================
# 1. KONFIGURASI
# ============================================================

BASE_URL = "https://lekminkes.dinkes.semarangkota.go.id"

# Tahun yang diminta
TAHUN_LIST = [2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]

# Mapping nama folder  ->  nama endpoint di server
#   - "kasus_tb_baru" sesuai curl yang Anda lampirkan di PDF
PENYAKIT = {
    "leptospirosis": "Leptospirosis",
    "tb_baru":       "kasus_tb_baru",
    "dbd":           "DBD",
}

# Folder output
OUTPUT_DIR = "data"

# ------------------------------------------------------------------
# Cookie session — DIAMBIL DARI "Copy as cURL" yang Anda lampirkan.
# Cookie `dashboard_session` bisa expired. Jika scraper gagal
# (response bukan JSON / status false), buka web, F12 → Network,
# ambil cookie terbaru, lalu ganti nilai di bawah.
# ------------------------------------------------------------------
COOKIES = {
    "_ga": "GA1.1.1704744380.1788183050",
    "dashboard_session": "gp65k95ut22702auq6p1tk7fmg22hbls",
    "_ga_YNR7Y7G61C": "GS2.1.s1789473255$o15$g0$t1789473255$j60$l0$h0",
}

HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Referer": BASE_URL + "/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/152.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": '"Chromium";v="152", "Not?A_Brand";v="24", "Google Chrome";v="152"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

DELAY = 1.0          # jeda antar request (detik)
TIMEOUT = 30         # timeout per request
MAX_RETRY = 2        # retry kalau request gagal


# ============================================================
# 2. SESSION HTTP
# ============================================================

session = requests.Session()
session.headers.update(HEADERS)
session.cookies.update(COOKIES)


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def safe_get(url, params=None, expect_json=False):
    """
    GET dengan retry, timeout, dan deteksi response JSON.
    Return: text (str) atau dict/list (JSON) — None kalau gagal.
    """
    for attempt in range(1, MAX_RETRY + 2):
        try:
            tag = f"(attempt {attempt})" if attempt > 1 else ""
            print(f"    GET {url}  params={params} {tag}")
            r = session.get(url, params=params, timeout=TIMEOUT)
            if r.status_code != 200:
                print(f"    ! HTTP {r.status_code}")
                time.sleep(DELAY * attempt)
                continue

            if expect_json:
                # Coba parse langsung
                try:
                    return r.json()
                except ValueError:
                    # Kadang response JSON dibungkus HTML/JS. Ekstrak objek pertama.
                    text = r.text.strip()
                    m = re.search(r"\{.*\}", text, re.S)
                    if m:
                        try:
                            return json.loads(m.group(0))
                        except Exception:
                            pass
                    # Kadang juga ada response non-JSON saat session expired
                    if "login" in text.lower() or "<html" in text.lower()[:200]:
                        print("    ! Response bukan JSON (kemungkinan session expired)")
                    else:
                        print("    ! Response bukan JSON valid")
                    print("    ! Cuplikan:", text[:180].replace("\n", " "))
                    return None
            return r.text

        except requests.exceptions.RequestException as e:
            print(f"    ! Request error: {e}")
            time.sleep(DELAY * attempt)

    return None


# ============================================================
# 3. REPROJECT GEOJSON: EPSG:32749 (UTM 49S)  ->  EPSG:4326 (WGS84)
# ============================================================

def reproject_geojson_to_wgs84(input_path, output_path):
    """
    Baca GeoJSON dengan CRS EPSG:32749 (UTM Zone 49S),
    reproject koordinat ke WGS84 (lon, lat), lalu simpan.
    """
    if not PYPROJ_AVAILABLE:
        raise RuntimeError("pyproj belum terinstall")

    transformer = Transformer.from_crs(
        "EPSG:32749",   # from: WGS84 / UTM Zone 49S
        "EPSG:4326",    # to:   WGS84 lat/lng
        always_xy=True  # pastikan input (x, y) = (easting, northing)
    )

    with open(input_path, "r", encoding="utf-8") as f:
        gj = json.load(f)

    def transform_coords(coords):
        # Titik tunggal [x, y]
        if isinstance(coords[0], (int, float)):
            lon, lat = transformer.transform(coords[0], coords[1])
            return [lon, lat]
        # Array of points (rekursif)
        return [transform_coords(c) for c in coords]

    count = 0
    for feat in gj.get("features", []):
        geom = feat.get("geometry")
        if geom and geom.get("coordinates"):
            geom["coordinates"] = transform_coords(geom["coordinates"])
            count += 1

    # Ganti CRS ke WGS84 (OGC:CRS84 = sama dgn EPSG:4326, urutan lon, lat)
    gj["crs"] = {
        "type": "name",
        "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False, indent=2)

    print(f"  ✓ Reproject {count} feature berhasil")
    return count


# ============================================================
# 4. SCRAPER: GEOJSON BATAS PUSKESMAS (satu kali saja)
# ============================================================

def scrape_geojson_puskesmas():
    print("\n" + "=" * 60)
    print("[1] GEOJSON BATAS PUSKESMAS")
    print("=" * 60)

    url = f"{BASE_URL}/assets/geojson/puskesmas.json"
    raw_path   = os.path.join(OUTPUT_DIR, "puskesmas_raw.geojson")
    final_path = os.path.join(OUTPUT_DIR, "puskesmas.geojson")

    data = safe_get(url, expect_json=True)
    if data is None:
        print("  ! Gagal mengambil GeoJSON puskesmas.")
        return False

    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ Raw tersimpan: {raw_path}")

    # Cek CRS asli
    crs_name = (data.get("crs", {}) or {}).get("properties", {}).get("name", "")
    print(f"  CRS asli: {crs_name}")

    # Jika CRS bukan WGS84, reproject
    if "32749" in crs_name or "32749" in str(crs_name):
        print("  → Reproject EPSG:32749 → EPSG:4326 ...")
        try:
            reproject_geojson_to_wgs84(raw_path, final_path)
            os.remove(raw_path)
        except Exception as e:
            print(f"  ! Gagal reproject: {e}")
            print("  ! Pakai file mentah (peta kemungkinan TIDAK muncul).")
            os.replace(raw_path, final_path)
    else:
        # Sudah WGS84, langsung pakai
        os.replace(raw_path, final_path)
        print("  → Sudah WGS84, tidak perlu reproject.")

    # Verifikasi
    try:
        with open(final_path, "r", encoding="utf-8") as f:
            gj_check = json.load(f)
        first = gj_check["features"][0]["geometry"]["coordinates"][0][0]
        print(f"  Sample koordinat pertama: {first}")
        if isinstance(first[0], (int, float)) and abs(first[0]) > 180:
            print("  ! PERINGATAN: koordinat masih UTM (Leaflet tidak akan menampilkan).")
        elif isinstance(first[0], (int, float)) and 90 < abs(first[1]) < 180:
            # Lon bisa 110, lat -6 → salah urutan
            print("  ! PERINGATAN: urutan koordinat mungkin terbalik (lat, lon).")
        else:
            print("  ✓ Koordinat WGS84 valid (lon, lat).")
    except Exception as e:
        print(f"  ! Verifikasi gagal: {e}")

    print(f"  ✓ Final: {final_path}")
    return True


# ============================================================
# 5. SCRAPER: graph/map  ->  map_{tahun}.json
# ============================================================

def scrape_graph_map(penyakit_folder, penyakit_endpoint, tahun):
    """
    Response JSON: {status, geojson, title, subtitle, key, label, data}
    data: [["P01", 77], ["P02", 65], ...]
    """
    url = f"{BASE_URL}/graph/map/{penyakit_endpoint}"
    params = {"tahun": tahun, "tingkat": "puskesmas"}
    data = safe_get(url, params=params, expect_json=True)

    if data is None:
        print(f"    ! map {tahun}: response kosong")
        return False
    if not data.get("status"):
        print(f"    ! map {tahun}: status=false (mungkin tahun ini tidak ada data)")
        return False

    out_dir = os.path.join(OUTPUT_DIR, penyakit_folder)
    ensure_dir(out_dir)
    out_path = os.path.join(out_dir, f"map_{tahun}.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    n = len(data.get("data", []))
    print(f"    ✓ map_{tahun}.json  ({n} puskesmas)")
    return True


# ============================================================
# 6. SCRAPER: graph/line  ->  line_{tahun}.json
# ============================================================

def scrape_graph_line(penyakit_folder, penyakit_endpoint, tahun):
    """
    Response JSON: {status, title, subtitle, category, data:[{name,data:[12 bln]}], datatab}
    """
    url = f"{BASE_URL}/graph/line/{penyakit_endpoint}"
    params = {"tahun": tahun}
    data = safe_get(url, params=params, expect_json=True)

    if data is None:
        print(f"    ! line {tahun}: response kosong")
        return False
    if not data.get("status"):
        print(f"    ! line {tahun}: status=false")
        return False

    out_dir = os.path.join(OUTPUT_DIR, penyakit_folder)
    ensure_dir(out_dir)
    out_path = os.path.join(out_dir, f"line_{tahun}.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    n_series = len(data.get("data", []))
    print(f"    ✓ line_{tahun}.json  ({n_series} seri)")
    return True


# ============================================================
# 7. SCRAPER: ajax/bar2  ->  bar_{tahun}.json
# ============================================================

# Response berbentuk HTML + "<script>var dat = [ {...}, ... ];</script>"
RE_VAR_DAT = re.compile(r"var\s+dat\s*=\s*(\[.*?\]);", re.S)


def scrape_ajax_bar(penyakit_folder, penyakit_endpoint, tahun):
    """
    Ekstrak `var dat = [...]` dari response HTML, lalu normalisasi.
    Field:
      - data   = Penderita Perempuan
      - datal  = Penderita Laki-laki
      - dataml = Meninggal Laki-laki
      - datamp = Meninggal Perempuan
    (Tidak semua penyakit punya dataml/datamp — default 0.)
    """
    url = f"{BASE_URL}/ajax/bar2/{penyakit_endpoint}"
    params = {"tahun": tahun, "tingkat": "puskesmas"}
    text = safe_get(url, params=params, expect_json=False)

    if not text:
        print(f"    ! bar {tahun}: response kosong")
        return False

    m = RE_VAR_DAT.search(text)
    if not m:
        print(f"    ! bar {tahun}: pola `var dat` tidak ditemukan")
        return False

    try:
        arr = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        print(f"    ! bar {tahun}: gagal parse JSON ({e})")
        return False

    # Normalisasi field
    normalized = []
    for item in arr:
        normalized.append({
            "name":                 item.get("name"),
            "perempuan":            item.get("data", 0),
            "laki_laki":            item.get("datal", 0),
            "meninggal_laki_laki":  item.get("dataml", 0),
            "meninggal_perempuan":  item.get("datamp", 0),
        })

    out_dir = os.path.join(OUTPUT_DIR, penyakit_folder)
    ensure_dir(out_dir)
    out_path = os.path.join(out_dir, f"bar_{tahun}.json")

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)

    print(f"    ✓ bar_{tahun}.json  ({len(normalized)} puskesmas)")
    return True


# ============================================================
# 8. MAIN
# ============================================================

def main():
    print("=" * 60)
    print(" SCRAPER WEBGIS PENYAKIT MENULAR KOTA SEMARANG")
    print(f" Sumber : {BASE_URL}")
    print(f" Tahun  : {TAHUN_LIST[0]} – {TAHUN_LIST[-1]}")
    print(f" Jumlah : {len(PENYAKIT)} penyakit × {len(TAHUN_LIST)} tahun")
    print("=" * 60)

    ensure_dir(OUTPUT_DIR)

    # --- Step 1: GeoJSON puskesmas ---
    ok_geojson = scrape_geojson_puskesmas()
    time.sleep(DELAY)

    # --- Step 2: Loop penyakit × tahun ---
    summary = {}

    for idx, (folder, endpoint) in enumerate(PENYAKIT.items(), start=1):
        print("\n" + "=" * 60)
        print(f"[{idx+1}] PENYAKIT: {folder.upper()}  (endpoint: {endpoint})")
        print("=" * 60)

        summary[folder] = {"map": 0, "bar": 0, "line": 0}

        for tahun in TAHUN_LIST:
            print(f"\n  Tahun {tahun}")
            try:
                if scrape_graph_map(folder, endpoint, tahun):
                    summary[folder]["map"] += 1
                time.sleep(DELAY)

                if scrape_graph_line(folder, endpoint, tahun):
                    summary[folder]["line"] += 1
                time.sleep(DELAY)

                if scrape_ajax_bar(folder, endpoint, tahun):
                    summary[folder]["bar"] += 1
                time.sleep(DELAY)
            except Exception:
                print(f"    ! Error pada {folder} {tahun}:")
                traceback.print_exc()
                time.sleep(DELAY)

    # --- Ringkasan akhir ---
    print("\n" + "=" * 60)
    print(" SELESAI")
    print("=" * 60)
    print(f" GeoJSON puskesmas: {'OK' if ok_geojson else 'GAGAL'}")
    for p, s in summary.items():
        print(f"   {p:15s} : map={s['map']}, bar={s['bar']}, line={s['line']} "
              f"(dari {len(TAHUN_LIST)} tahun)")
    print("\n Semua file tersimpan di folder:", OUTPUT_DIR)
    print("=" * 60)


if __name__ == "__main__":
    main()