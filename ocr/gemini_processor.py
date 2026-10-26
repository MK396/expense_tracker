import os
import time
import json
import re
from dotenv import load_dotenv
from google import genai
from PIL import Image

load_dotenv()

# Maks. dłuższy bok — wystarczy do OCR paragonu, mniejszy upload i szybsza odpowiedź API
MAX_IMAGE_SIDE = int(os.getenv("GEMINI_MAX_IMAGE_SIDE", "1600"))
JPEG_QUALITY = int(os.getenv("GEMINI_JPEG_QUALITY", "85"))

MODEL_LIST = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
]

PROMPT = (
    "Przeanalizuj paragon. Zwróć TYLKO JSON: "
    '{"nip":"...","sklep":"...","suma_calkowita":"...","produkty":[{"name":"...","amount":0.0}]}. '
    "Uwzględnij linie OPUST pod produktami."
)


def _prepare_receipt_image(img: Image.Image) -> Image.Image:
    img = img.convert("RGB")
    w, h = img.size
    longest = max(w, h)
    if longest > MAX_IMAGE_SIDE:
        scale = MAX_IMAGE_SIDE / longest
        img = img.resize(
            (int(w * scale), int(h * scale)),
            Image.Resampling.LANCZOS,
        )
    return img


def _is_transient_error(exc: Exception) -> bool:
    msg = str(exc).upper()
    return any(
        token in msg
        for token in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED", "OVERLOADED")
    )


def analizuj_paragon_gemini(file_path):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Nie znaleziono klucza API! Sprawdź plik .env")

    client = genai.Client(api_key=api_key)
    img = _prepare_receipt_image(Image.open(str(file_path)))

    lista_modeli = MODEL_LIST
    response = None
    used_model = None
    ostatni_blad = None

    for model_name in lista_modeli:
        try:
            print(f"[Gemini AI] Próba analizy za pomocą modelu: {model_name}...")

            response = client.models.generate_content(
                model=model_name,
                contents=[PROMPT, img],
            )
            used_model = model_name
            print(f"[Gemini AI] Sukces! Użyto modelu: {model_name}")
            break

        except Exception as e:
            ostatni_blad = e
            print(f"[Gemini AI] Model {model_name} zwrócił błąd: {e}")
            if _is_transient_error(e):
                time.sleep(0.3)
                continue
            raise

    if not response:
        raise RuntimeError(f"Wszystkie modele z listy zawiodły. Ostatni błąd: {ostatni_blad}")

    text = response.text.strip()
    text = re.sub(r'^```json\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text)

    try:
        data = json.loads(text)

        surowe_produkty = data.get("produkty", [])
        wyczyszczone_produkty = []

        for item in surowe_produkty:
            nazwa = item.get("name", "")
            try:
                kwota = float(item.get("amount", 0.0))
            except (ValueError, TypeError):
                kwota = 0.0

            if "OPUST" in nazwa.upper():
                if wyczyszczone_produkty:
                    wyczyszczone_produkty[-1]["amount"] = round(
                        wyczyszczone_produkty[-1]["amount"] - abs(kwota), 2
                    )
                continue

            item["amount"] = kwota
            wyczyszczone_produkty.append(item)

        data["produkty"] = wyczyszczone_produkty
        data["_model"] = used_model
        return data

    except json.JSONDecodeError:
        print("Nie udało się sparsować JSONa. Otrzymano:", text)
        raise ValueError("Model nie zwrócił poprawnego JSONa")
