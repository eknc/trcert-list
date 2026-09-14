import urllib.request
import json
import os
import time

def load_existing_indicators(file_path):
    """Mevcut dosyayı okur, ABP format sembollerini (|| ve ^) temizleyerek ham veri kümesi döner."""
    if not os.path.exists(file_path):
        return set()
    indicators = set()
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Başındaki || ve sonundaki ^ işaretlerini temizleyip ham halini hafızaya alıyoruz
            cleaned = line.lstrip('|').rstrip('^')
            indicators.add(cleaned)
    return indicators

def test_fetch_usom_data():
    output_file = "usom-hourly.txt"
    
    existing_indicators = load_existing_indicators(output_file)
    combined_indicators = existing_indicators.copy()
    
    target_types = ["domain", "ip"]
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    total_new_added = 0
    MAX_TEST_PAGES = 300  # İhtiyaca göre sayfa limiti
    
    for data_type in target_types:
        try:
            print(f"\n--- Testing {data_type.upper()} ---")
            url = f"https://siberguvenlik.gov.tr/api/address/index?type={data_type}&page=0"
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                actual_page_count = data.get("pageCount", 0)
            
            pages_to_scan = min(actual_page_count, MAX_TEST_PAGES)
            print(f"Total pages in API: {actual_page_count}. Scanning first {pages_to_scan} pages.")
            
            for i in range(pages_to_scan):
                print(f"Fetching page {i}...")
                page_url = f"https://siberguvenlik.gov.tr/api/address/index?type={data_type}&page={i}"
                page_req = urllib.request.Request(page_url, headers=headers)
                
                with urllib.request.urlopen(page_req) as p_res:
                    p_data = json.loads(p_res.read().decode())
                    models = p_data.get("models", [])
                    
                    if not models:
                        break
                        
                    page_has_new_data = False
                    for model in models:
                        indicator = model.get("url")
                        if indicator:
                            indicator = indicator.strip()
                            if indicator not in existing_indicators:
                                combined_indicators.add(indicator)
                                total_new_added += 1
                                page_has_new_data = True
                    
                    # Optimizasyon Tetikleyicisi:
                    # Sayfadaki tüm veriler zaten eskiyse döngü kırılır.
                    if not page_has_new_data and len(existing_indicators) > 0:
                        print(f"-> Optimization hit at page {i}. Stopping.")
                        break
                
                # USOM Sunucularını yormamak ve banlanmamak için 0.2 saniye bekleme
                time.sleep(0.2)
                        
        except Exception as e:
            print(f"Error ({data_type}): {e}")
            
    # Dosyaya yazma aşaması
    if total_new_added > 0:
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                for item in sorted(combined_indicators):
                    # IP ve Domain ayırt etmeksizin tüm girdileri ABP formatında yazıyoruz
                    f.write(f"||{item}^\n")
            print(f"\n[SUCCESS] Added {total_new_added} new items. Total items: {len(combined_indicators)}")
        except Exception as e:
            print(f"File write error: {e}")
    else:
        print("\n[INFO] No new items found.")

if __name__ == "__main__":
    test_fetch_usom_data()
