import os
import time
import json
import re
from dotenv import load_dotenv
from google import genai
from PIL import Image

load_dotenv()

def analizuj_paragon_gemini(file_path):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Nie znaleziono klucza API! Sprawdź plik .env")
        
    client = genai.Client(api_key=api_key)
    img = Image.open(str(file_path)).convert('RGB')
    
    lista_modeli = [
        "gemini-2.0-flash",
        "gemini-flash-latest",
        "gemini-2.0-flash-lite",
    ]
    
    response = None
    ostatni_blad = None

    for model_name in lista_modeli:
        try:
            print(f"[Gemini AI] Próba analizy za pomocą modelu: {model_name}...")
            
            # Prompt
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    "Przeanalizuj ten paragon. Wyciągnij strukturę zakupów, uwzględniając linie z opustami / zniżkami dokładnie pod produktami, których dotyczą. Zwróć dane WYŁĄCZNIE w formacie JSON (bez żadnego innego tekstu, bez znaczników markdown): {'nip': '...', 'sklep': '...', 'suma_calkowita': '...', 'produkty': [{'name': '...', 'amount': 0.0}]}",
                    img
                ]
            )
            print(f"[Gemini AI] Sukces! Użyto modelu: {model_name}")
            break
            
        except Exception as e:
            ostatni_blad = e
            print(f"[Gemini AI] Model {model_name} zwrócił błąd: {e}")
            time.sleep(1)
            continue

    if not response:
        raise RuntimeError(f"Wszystkie modele z listy zawiodły. Ostatni błąd: {ostatni_blad}")
    
    text = response.text.strip()
    text = re.sub(r'^```json\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text)
    
    try:
        data = json.loads(text)
        
        # Procesowanie odpustow
        surowe_produkty = data.get("produkty", [])
        wyczyszczone_produkty = []
        
        for item in surowe_produkty:
            nazwa = item.get("name", "")
            try:
                kwota = float(item.get("amount", 0.0))
            except (ValueError, TypeError):
                kwota = 0.0
                
            # Sprawdzamy czy to linia z opustem
            if "OPUST" in nazwa.upper():
                # Jeśli mamy już jakiś produkt na liście, odejmujemy zniżkę od niego
                if wyczyszczone_produkty:
                    wyczyszczone_produkty[-1]["amount"] = round(wyczyszczone_produkty[-1]["amount"] - abs(kwota), 2)
                continue
            else:
                item["amount"] = kwota
                wyczyszczone_produkty.append(item)
                
        data["produkty"] = wyczyszczone_produkty
        return data
        
    except json.JSONDecodeError:
        print("Nie udało się sparsować JSONa. Otrzymano:", text)
        raise ValueError("Model nie zwrócił poprawnego JSONa")