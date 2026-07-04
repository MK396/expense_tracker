from datetime import datetime
from pathlib import Path
import cv2
import pytesseract
import re
import requests
import sqlite3

BASE_DIR = Path(__file__).resolve().parent

# sciezka do bazy danych
DB_PATH = BASE_DIR / "ocr_cache.db"

# FUNKCJE OBSLUGI BAZY DANYCH

def sprawdz_nip_w_bazie(nip):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT nazwa_firmy FROM znane_firmy WHERE nip = ?", (str(nip),)
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None


def zapisz_nip_do_bazy(nip, nazwa_firmy):
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    dzis = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute(
            """
            INSERT INTO znane_firmy (nip, nazwa_firmy, data_zapisu)
            VALUES (?, ?, ?)
        """,
            (str(nip), str(nazwa_firmy), dzis),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

# FUNKCJE PRZETWARZANIA OBRAZU I TEKSTU

def crop_receipt_by_bbox(image):
    h, w = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[
        1
    ]
    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

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
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[
        1
    ]

    folder_preprocessed = BASE_DIR / "preprocessed"
    folder_preprocessed.mkdir(exist_ok=True)
    output_name = (
        folder_preprocessed / f"{file_path.stem}_preprocessed{file_path.suffix}"
    )
    cv2.imwrite(str(output_name), thresh)

    # Czytanie blokowe (tu trzeba poprawic aby lepiej dopsaowac)
    custom_config = r"--oem 3 --psm 6 -c preserve_interword_spaces=1 -l pol"
    return pytesseract.image_to_string(thresh, config=custom_config)


def waliduj_nip(nip):
    """Sprawdza matematycznie poprawność NIP-u (Suma kontrolna)."""
    if not nip or len(nip) != 10 or not nip.isdigit():
        return False
    wagi = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    suma = sum(int(nip[i]) * wagi[i] for i in range(9))
    return (suma % 11) == int(nip[9])


def wyciagnij_czysty_nip(tekst):
    wzorzec_nip = r"NIP.{0,15}?(\d{9,11})"
    mecz = re.search(wzorzec_nip, tekst, re.IGNORECASE)
    return mecz.group(1) if mecz else None


def wyciagnij_suma_pln(tekst):
    wzorzec_sumy = r"SUMA[AĄ]?\s*(?:PLN)?[\s\S]{0,50}?(\d+[\s,.]+\d{2})\s*PLN"
    mecz = re.search(wzorzec_sumy, tekst, re.IGNORECASE)
    if mecz:
        kwota = mecz.group(1).replace(" ", "").replace(",", ".")
        return f"{kwota} PLN"
        
    wzorzec_fallback = r"SUMA[AĄ]?\s*(?:PLN)?[\s\S]{0,40}?(\d+[\s,.]+\d{2})"
    mecz_fb = re.search(wzorzec_fallback, tekst, re.IGNORECASE)
    if mecz_fb:
        kwota = mecz_fb.group(1).replace(" ", "").replace(",", ".")
        return f"{kwota} PLN"

    return "Nie znaleziono kwoty"


def pobierz_nazwe_firmy_po_nip(nip):
    dzisiejsza_data = datetime.now().strftime("%Y-%m-%d")
    url = f"https://wl-api.mf.gov.pl/api/search/nip/{nip}?date={dzisiejsza_data}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
        "Connection": "keep-alive"
    }
    try:
        response = requests.get(url, headers=headers, timeout=7)
        if response.status_code == 200:
            data = response.json()
            subject = data.get("result", {}).get("subject")
            if subject:
                return subject.get("name")
        return None
    except requests.exceptions.RequestException:
        return None


def mapuj_na_prosta_nazwe(pelna_nazwa):
    if not pelna_nazwa or "Błędny NIP" in pelna_nazwa:
        return "Nieznany Sklep"
    nazwa_lower = pelna_nazwa.lower()
    if "jeronimo" in nazwa_lower or "biedronka" in nazwa_lower:
        return "Biedronka"
    elif "kaufland" in nazwa_lower:
        return "Kaufland"
    elif "lidl" in nazwa_lower:
        return "Lidl"
    elif "sfinks" in nazwa_lower or "sphinx" in nazwa_lower or "tien" in nazwa_lower or "mai lan" in nazwa_lower:
        return "Restauracja Mai Lan"
    return pelna_nazwa.split("SPÓŁKA")[0].strip().title()

# FUNKCJA FILTRUJACA

def wytnij_od_paragonu_fiskalnego(tekst):
    linie = tekst.split("\n")

    indeks_start = None
    for indeks, linia in enumerate(linie):
        if "SKAL" in linia.upper() or "PARAGON" in linia.upper():
            indeks_start = indeks
            break

    if indeks_start is None:
        return tekst

    linie_wynikowe = []
    
    wzorzec_bledu_cyfry = r"(\d+[\s,.]+\d{2})\d\s*([A-Ga-g])?\s*$"

    for linia in linie[indeks_start:]:
        linia_stripped = linia.strip()

        if not linia_stripped:
            continue

        if any(h in linia_stripped.upper() for h in ["PODSUMA", "OPODATKOWANA", "PTU A", "SUMA", "RAZEM"]):
            break

        mecz_cyfry = re.search(wzorzec_bledu_cyfry, linia_stripped)
        if mecz_cyfry:
            litera = mecz_cyfry.group(2) if mecz_cyfry.group(2) else ""
            linia_stripped = re.sub(wzorzec_bledu_cyfry, rf"\1 {litera}", linia_stripped).strip()

        linia_stripped = linia_stripped.replace("€", "C")

        linia_stripped = re.sub(r"[@©®ĘŚĆŻŹ]\s*$", "", linia_stripped).strip()

        linie_wynikowe.append(linia_stripped)

    return "\n".join(linie_wynikowe)

# GLOWNY BLOK

if __name__ == "__main__":
    # TUTAJ NAZWE ZMIENIC PLKU
    file_name = "paragon3.jpeg"
    file_path = BASE_DIR / "original" / file_name

    if not file_path.exists():
        print(f"Błąd: Brak pliku w folderze: {file_path.parent}/")
    else:
        full_text = read_receipt(file_path)
        czysty_nip = wyciagnij_czysty_nip(full_text)
        wykryta_suma = wyciagnij_suma_pln(full_text)

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

        folder_txt = BASE_DIR / "txt"
        folder_txt.mkdir(exist_ok=True)
        txt_output_name = folder_txt / f"{file_path.stem}_output.txt"
        with open(txt_output_name, "w", encoding="utf-8") as file:
            file.write(filtered_text)

        print("\n=== METADANE PARAGONU ===")
        print(f"WYKRYTY NIP:               {czysty_nip}")
        print(f"REJESTROWA NAZWA:          {oficjalna_nazwa}")
        print(f"PRZYJAZNA NAZWA (APKA):    {sklep_w_aplikacji}")
        print(f"ODCZYTANA SUMA RAZEM:      {wykryta_suma}")
        print(f"ŹRÓDŁO DANYCH O FIRMIE:    {źródło_danych}")
        print("=========================")

        print("\n--- ODCZYTANY TEKST (PEŁNA TREŚĆ OD NAGŁÓWKA) ---")
        print(filtered_text)
        print("-----------------------------------------------------")
