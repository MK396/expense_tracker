from datetime import datetime
from pathlib import Path
import cv2
import easyocr
import re
import requests
import sqlite3

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "ocr_cache.db"

# ==========================================
# INICJALIZACJA MODELU EASYOCR
# ==========================================
print("Ładowanie modelu EasyOCR... (może to zająć kilka sekund)")
reader = easyocr.Reader(['pl'])
print("Model gotowy!")

# ==========================================
# FUNKCJE OBSLUGI BAZY DANYCH
# ==========================================
def sprawdz_nip_w_bazie(nip):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute("SELECT nazwa_firmy FROM znane_firmy WHERE nip = ?", (str(nip),))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def zapisz_nip_do_bazy(nip, nazwa_firmy):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    dzis = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute(
            "INSERT INTO znane_firmy (nip, nazwa_firmy, data_zapisu) VALUES (?, ?, ?)",
            (str(nip), str(nazwa_firmy), dzis),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

# ==========================================
# FUNKCJE PRZETWARZANIA OBRAZU I OCR
# ==========================================
def crop_receipt_by_bbox(image):
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w_cont, h_cont = cv2.boundingRect(largest_contour)
        margin = 15
        x_min, y_min = max(0, x - margin), max(0, y - margin)
        x_max, y_max = min(w, x + w_cont + margin), min(h, y + h_cont + margin)
        return image[y_min:y_max, x_min:x_max]
    return image

def read_receipt(file_path):
    image = cv2.imread(str(file_path))
    if image is None:
        return "Nie wczytano obrazu"
    
    cropped_image = crop_receipt_by_bbox(image)
    gray = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)

    folder_preprocessed = BASE_DIR / "preprocessed"
    folder_preprocessed.mkdir(exist_ok=True)
    output_name = folder_preprocessed / f"{file_path.stem}_preprocessed{file_path.suffix}"
    cv2.imwrite(str(output_name), gray)

    results = reader.readtext(gray, detail=1)
    if not results:
        return ""

    parsed_items = []
    for bbox, text, conf in results:
        center_x = (bbox[0][0] + bbox[1][0]) / 2
        center_y = (bbox[0][1] + bbox[2][1]) / 2
        parsed_items.append({"text": text, "x": center_x, "y": center_y})

    parsed_items.sort(key=lambda item: item["y"])
    
    
    # Zamiast wpisywać "y_tolerance = 15" na sztywno, obliczamy ją dynamicznie:
    
    grouped_lines = []
    if parsed_items:
        # 1. WYLICZANIE DYNAMICZNEJ TOLERANCJI Y
        wysokosci = [bbox[2][1] - bbox[0][1] for bbox, text, conf in results]
        srednia_wysokosc = sum(wysokosci) / len(wysokosci) if wysokosci else 20
        y_tolerance = srednia_wysokosc * 0.55 
        
        # 2. TWOJA ORYGINALNA PĘTLA GRUPUJĄCA LINIE
        current_line = [parsed_items[0]]
        for item in parsed_items[1:]:
            if abs(item["y"] - current_line[0]["y"]) <= y_tolerance:
                current_line.append(item)
            else:
                grouped_lines.append(current_line)
                current_line = [item]
        if current_line:
            grouped_lines.append(current_line)

    final_text_lines = []
    for group in grouped_lines:
        group.sort(key=lambda item: item["x"])
        line_str = " ".join(item["text"] for item in group)
        final_text_lines.append(line_str)

    return "\n".join(final_text_lines)

# ==========================================
# PARSOWANIE TEKSTU I API
# ==========================================
def waliduj_nip(nip):
    if not nip or len(nip) != 10 or not nip.isdigit(): return False
    wagi = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    suma = sum(int(nip[i]) * wagi[i] for i in range(9))
    return (suma % 11) == int(nip[9])

def wyciagnij_czysty_nip(tekst):
    # 1. Usuwamy białe znaki i myślniki, bo OCR często rozbija NIP (np. "899 236-72-73")
    tekst_zbity = re.sub(r'[\s\-]', '', tekst)
    
    # 2. Szukamy po słowie kluczowym (np. NIP8992367273)
    mecz = re.search(r'NIP.*?(\d{10})', tekst_zbity, re.IGNORECASE)
    if mecz and waliduj_nip(mecz.group(1)):
        return mecz.group(1)
        
    # 3. ZAPASOWY RADAR: OCR mógł źle przeczytać słowo "NIP". 
    # Szukamy WSZYSTKICH 10-cyfrowych ciągów w całym tekście.
    potencjalne_nipy = re.findall(r'(?<!\d)(\d{10})(?!\d)', tekst_zbity)
    for kandydat in potencjalne_nipy:
        # Test matematyczny (suma kontrolna). Jeśli przejdzie, na 100% mamy NIP.
        if waliduj_nip(kandydat):
            return kandydat
            
    return None

def wyciagnij_suma_pln(tekst):
    # 1. Wzorzec priorytetowy: szuka konkretnych haseł: "SUMA PLN", "RAZEM", "DO ZAPŁATY"
    # (Toleruje drobne błędy OCR, np. SUHA, SUNA zamiast SUMA)
    wzorzec_glowny = r"(?:SU[MHN]A\s*PLN|RAZEM|ZAP[LŁ]ATY)[\s\S]{0,40}?(\d+[\s,.]+\d{2})"
    mecz = re.search(wzorzec_glowny, tekst, re.IGNORECASE)
    if mecz:
        # Trik: usuwamy wszystko oprócz cyfr i odcinamy 2 ostatnie na grosze
        cyfry = re.sub(r'\D', '', mecz.group(1))
        return f"{cyfry[:-2]}.{cyfry[-2:]} PLN"
        
    # 2. Drugi krok: samo słowo "SUMA", ale kategorycznie wykluczamy "SUMA PTU" 
    # (bo PTU to podatek VAT, a nie ostateczna łączna kwota)
    wzorzec_fallback = r"SU[MHN]A(?!\s*PTU)[\s\S]{0,40}?(\d+[\s,.]+\d{2})"
    mecz_fb = re.search(wzorzec_fallback, tekst, re.IGNORECASE)
    if mecz_fb:
        cyfry = re.sub(r'\D', '', mecz_fb.group(1))
        return f"{cyfry[:-2]}.{cyfry[-2:]} PLN"
        
    # 3. Ostatnia deska ratunku: szukamy formatu "XX,XX PLN" na samym dole paragonu 
    # (Na paragonie z Mai Lan złapie w ten sposób napis "GOTÓWKA 92,00 PLN")
    wzorzec_pln = r"(\d+[\s,.]+\d{2})\s*PLN"
    mecze_pln = re.findall(wzorzec_pln, tekst, re.IGNORECASE)
    if mecze_pln:
        # Bierzemy ostatnie wystąpienie (z dołu tekstu)
        cyfry = re.sub(r'\D', '', mecze_pln[-1])
        return f"{cyfry[:-2]}.{cyfry[-2:]} PLN"

    return "Nie znaleziono kwoty"

def pobierz_nazwe_firmy_po_nip(nip):
    url = f"https://wl-api.mf.gov.pl/api/search/nip/{nip}?date={datetime.now().strftime('%Y-%m-%d')}"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=7)
        if response.status_code == 200:
            return response.json().get("result", {}).get("subject", {}).get("name")
    except requests.exceptions.RequestException: pass
    return None

def mapuj_na_prosta_nazwe(pelna_nazwa):
    if not pelna_nazwa or "Błędny NIP" in pelna_nazwa: return "Nieznany Sklep"
    nazwa_lower = pelna_nazwa.lower()
    if "jeronimo" in nazwa_lower or "biedronka" in nazwa_lower: return "Biedronka"
    if "kaufland" in nazwa_lower: return "Kaufland"
    if "lidl" in nazwa_lower: return "Lidl"
    return pelna_nazwa.split("SPÓŁKA")[0].strip().title()

def wytnij_od_paragonu_fiskalnego(tekst):
    linie = tekst.split("\n")
    indeks_start = next((i for i, l in enumerate(linie) if "SKAL" in l.upper() or "PARAGON" in l.upper()), None)
    if indeks_start is None: return tekst

    linie_wynikowe = []
    wzorzec_bledu_cyfry = r"(\d+[\s,.]+\d{2})\d\s*([A-Ga-g])?\s*$"

    for linia in linie[indeks_start:]:
        linia_stripped = linia.strip()
        if not linia_stripped: continue
        if any(h in linia_stripped.upper() for h in ["PODSUMA", "OPODATKOWANA", "PTU", "SUMA", "RAZEM"]): break

        mecz_cyfry = re.search(wzorzec_bledu_cyfry, linia_stripped)
        if mecz_cyfry:
            litera = mecz_cyfry.group(2) if mecz_cyfry.group(2) else ""
            linia_stripped = re.sub(wzorzec_bledu_cyfry, rf"\1 {litera}", linia_stripped).strip()

        linia_stripped = linia_stripped.replace("€", "C")
        linia_stripped = re.sub(r"[@©®ĘŚĆŻŹ]\s*$", "", linia_stripped).strip()
        linie_wynikowe.append(linia_stripped)

    return "\n".join(linie_wynikowe)

def wyciagnij_pozycje_z_paragonu(tekst_paragonu):
    linie = tekst_paragonu.split('\n')
    pozycje = []
    
    # ULTIMATE REGEX: Wymaga x lub *, pozwala na literówki (l, I, O), wyciąga ilość tuż sprzed znaku mnożenia.
# Ulepszony wzorzec: lepiej radzi sobie z wagami typu "0,496KG" lub "120g" przed znakiem X
    wzorzec_ceny = re.compile(r'(?:([0-9Oo]+[.,\'][0-9Oo]{1,3})\s*(?:kg|g|szt\.?|opak\.?)?\s*)?[xX\*]\s*([0-9lI|Oo]+[.,\'][0-9lI|Oo]{2})\s+(?:[A-Za-z]\s*)?([0-9lI|Oo]+[.,\'][0-9lI|Oo]{2})', re.IGNORECASE)

    # NOWY REGEX: Szuka słowa "opust" lub "rabat" i ujemnej kwoty na końcu
    wzorzec_opustu = re.compile(r'(?i)(opust|rabat).*?(?:-)?\s*([0-9lI|Oo]+[.,\'][0-9lI|Oo]{2})\s*[A-Za-z]?$')

    def napraw_cyfry(tekst):
        return tekst.replace('l', '1').replace('I', '1').replace('|', '1').replace('O', '0').replace('o', '0').replace(',', '.').replace("'", '.').replace(' ', '')
        
    def wyczysc_nazwe(tekst_surowy):
        slowa = tekst_surowy.split()
        czyste = []
        for w in slowa:
            # Wyciągamy tylko litery polskiego alfabetu, żeby odrzucić numeryczne szumy jak 125g, 720ml2
            w_litery = re.sub(r'[^A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż]', '', w)
            if len(w_litery) < 3: 
                continue
            
            w_low = w.lower()
            if any(j in w_low for j in ['szt', 'opak', 'draż', 'opust', 'cena', 'kartą', 'łączn', 'rabat']): 
                continue
            
            # Usuwamy dziwne znaki z brzegów słowa (np. "Chipsy~" na "Chipsy")
            w_czyste = re.sub(r'^[^a-zA-ZĄĆĘŁŃÓŚŹŻąćęłńóśźż]+|[^a-zA-ZĄĆĘŁŃÓŚŹŻąćęłńóśźż]+$', '', w)
            if w_czyste:
                czyste.append(w_czyste)
        return " ".join(czyste)

    for i, linia in enumerate(linie):
        # Usuwamy ewentualne spacje przy przecinkach
        linia_naprawiona = re.sub(r'\s*([.,\'])\s*', r'\1', linia)
        
        mecz_opust = wzorzec_opustu.search(linia_naprawiona)
        # Wykluczamy podsumowania typu "OPUSTY ŁĄCZNIE", żeby nie policzyć rabatu podwójnie
        if mecz_opust and not any(x in linia_naprawiona.lower() for x in ["łączn", "lacznie", "suma"]):
            kwota_str = mecz_opust.group(2)
            kwota = float(napraw_cyfry(kwota_str))
            
            # Pobieramy to, co było przed kwotą, jako nazwę opustu
            nazwa_opustu = linia_naprawiona[:mecz_opust.start(2)].replace('-', '').strip()
            if len(nazwa_opustu) < 3:
                nazwa_opustu = "Opust / Rabat"
                
            pozycje.append({
                "nazwa": nazwa_opustu.title(),
                "ilosc": 1.0,
                "cena_jedn": -kwota,
                "suma": -kwota
            })
            continue # Znaleźliśmy opust, pomijamy resztę pętli i idziemy do kolejnej linii
        # --------------------------------------

        # Tutaj zaczyna się Twój stary kod sprawdzający produkty
        mecz = wzorzec_ceny.search(linia_naprawiona)

        if mecz:
            ilosc_str = mecz.group(1)
            cena_str = mecz.group(2)
            suma_str = mecz.group(3)
            
            ilosc = float(napraw_cyfry(ilosc_str)) if ilosc_str else 1.0
            cena_jedn = float(napraw_cyfry(cena_str))
            suma = float(napraw_cyfry(suma_str))
            
            lewa_strona = linia_naprawiona[:mecz.start()].strip()
            nazwa = wyczysc_nazwe(lewa_strona)
            
            # RADAR: Szukamy nazwy dookoła, jeśli w linii z ceną same śmieci
            if not nazwa:
                kandydaci_indeksy = [i-1, i+1, i-2, i+2]
                for idx in kandydaci_indeksy:
                    if 0 <= idx < len(linie):
                        linia_kandydat = linie[idx]
                        if any(x in linia_kandydat.upper() for x in ["OPUST", "RABAT"]):
                            continue
                        # Upewniamy się, że nie kradniemy nazwy od innej ceny
                        linia_kandydat_naprawiona = re.sub(r'\s*([.,\'])\s*', r'\1', linia_kandydat)
                        if wzorzec_ceny.search(linia_kandydat_naprawiona):
                            continue
                            
                        kandydat_nazwa = wyczysc_nazwe(linia_kandydat)
                        if kandydat_nazwa:
                            nazwa = kandydat_nazwa
                            break
                
            if not nazwa:
                nazwa = "Nieznany Produkt"
                
            pozycje.append({
                "nazwa": nazwa.title(),
                "ilosc": ilosc,
                "cena_jedn": cena_jedn,
                "suma": suma
            })

    return pozycje

def analizuj_paragon_dla_api(file_path):
    """Funkcja do wywoływania przez API Django"""
    file_path = Path(file_path) 
    full_text = read_receipt(file_path)
    
    czysty_nip = wyciagnij_czysty_nip(full_text)
    sklep_w_aplikacji = "Nieznany Sklep"
    
    # --- NOWE: Odczytanie łącznej sumy z paragonu ---
    wykryta_suma = wyciagnij_suma_pln(full_text)

    # Skoro wyciagnij_czysty_nip coś zwróciło, to NIP jest na 100% poprawny
    if czysty_nip:
        oficjalna_nazwa = sprawdz_nip_w_bazie(czysty_nip)
        if not oficjalna_nazwa:
            oficjalna_nazwa = pobierz_nazwe_firmy_po_nip(czysty_nip)
            if oficjalna_nazwa:
                zapisz_nip_do_bazy(czysty_nip, oficjalna_nazwa)
        
        sklep_w_aplikacji = mapuj_na_prosta_nazwe(oficjalna_nazwa)

    filtered_text = wytnij_od_paragonu_fiskalnego(full_text)
    lista_produktow = wyciagnij_pozycje_z_paragonu(filtered_text)
    
    formatted_list = []
    for p in lista_produktow:
        formatted_list.append({
            "name": p["nazwa"][:200], 
            "amount": p["suma"]
        })
        
    return {
        "nip": czysty_nip if czysty_nip else "Brak",
        "sklep": sklep_w_aplikacji,
        "suma_calkowita": wykryta_suma, # Przekazujemy sumę do API
        "produkty": formatted_list
    }


# ==========================================
# GLOWNY BLOK
# ==========================================
if __name__ == "__main__":
    file_name = "paragon3.jpeg"  # Sprawdź dla Lidla, a potem przetestuj Kaufland!
    file_path = BASE_DIR / "original" / file_name

    if not file_path.exists():
        print(f"Błąd: Brak pliku w folderze: {file_path.parent}/")
    else:
        full_text = read_receipt(file_path)
        czysty_nip = wyciagnij_czysty_nip(full_text)
        wykryta_suma = wyciagnij_suma_pln(full_text)

        # ROZBUDOWANA OBSŁUGA METADANYCH Z ocr_processor.py
        if czysty_nip:
            # Weryfikacja matematyczna
            if not waliduj_nip(czysty_nip):
                oficjalna_nazwa = "Błędny NIP (odrzucony)"
                sklep_w_aplikacji = "Nieznany Sklep"
                źródło_danych = "ODRZUCONO - Niepoprawna suma kontrolna (Zużycie API = 0)"
            else:
                oficjalna_nazwa = sprawdz_nip_w_bazie(czysty_nip)
                if oficjalna_nazwa:
                    źródło_danych = "LOKALNA BAZA DANYCH (Zużycie API Ministerstwa = 0!)"
                else:
                    print(f"Brak NIP {czysty_nip} w bazie. Odpytuję Ministerstwo Finansów...")
                    oficjalna_nazwa = pobierz_nazwe_firmy_po_nip(czysty_nip)
                    if oficjalna_nazwa:
                        zapisz_nip_do_bazy(czysty_nip, oficjalna_nazwa)
                        źródło_danych = "API MINISTERSTWA FINANSÓW (Pobrano i zapisano do Twojej bazy)"
                    else:
                        oficjalna_nazwa = "Nie udało się pobrać z MF (Prawdopodobny limit zapytań IP)"
                        źródło_danych = "BŁĄD POBIERANIA"
                sklep_w_aplikacji = mapuj_na_prosta_nazwe(oficjalna_nazwa)
        else:
            czysty_nip = "Nie znaleziono"
            oficjalna_nazwa = "Brak NIP"
            sklep_w_aplikacji = "Nieznany Sklep"
            źródło_danych = "Brak danych"

        filtered_text = wytnij_od_paragonu_fiskalnego(full_text)
        lista_produktow = wyciagnij_pozycje_z_paragonu(filtered_text)

        folder_txt = BASE_DIR / "txt"
        folder_txt.mkdir(exist_ok=True)
        with open(folder_txt / f"{file_path.stem}_output.txt", "w", encoding="utf-8") as file:
            file.write(filtered_text)

        # WYŚWIETLANIE METADANYCH
        print("\n=== METADANE PARAGONU ===")
        print(f"WYKRYTY NIP:               {czysty_nip}")
        print(f"REJESTROWA NAZWA:          {oficjalna_nazwa}")
        print(f"PRZYJAZNA NAZWA (APKA):    {sklep_w_aplikacji}")
        print(f"ODCZYTANA SUMA RAZEM:      {wykryta_suma}")
        print(f"ŹRÓDŁO DANYCH O FIRMIE:    {źródło_danych}")
        print("=========================")

        # WYŚWIETLANIE PRODUKTÓW
        print("\n=== ZAKUPIONE PRODUKTY ===")
        if lista_produktow:
            for p in lista_produktow:
                nazwa = p['nazwa'][:25].ljust(25)
                print(f"{nazwa} | {p['ilosc']} x {p['cena_jedn']} PLN = {p['suma']} PLN")
        else:
            print("Nie udało się rozpoznać żadnych produktów.")
        print("=========================")