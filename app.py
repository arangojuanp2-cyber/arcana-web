from __future__ import annotations

import os
import re
import unicodedata
from collections import Counter
from io import BytesIO
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, UnidentifiedImageError

app = FastAPI(title="ARCANA", version="0.1.0",
              description="Laboratorio experimental de análisis y descifrado de escrituras")
app.mount("/static", StaticFiles(directory="static"), name="static")

MAX_IMAGE_BYTES = 8 * 1024 * 1024
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def normalize_text(text: str, mode: str = "preserve") -> str:
    text = unicodedata.normalize("NFC", text)
    if mode == "uppercase":
        return text.upper()
    if mode == "lowercase":
        return text.lower()
    if mode == "strip_spaces":
        return re.sub(r"\s+", "", text)
    return text


def reverse_text(text: str) -> str:
    return text[::-1]


def reverse_words(text: str) -> str:
    return " ".join(text.split()[::-1])


def mirror_characters(text: str) -> str:
    # Unicode includes only a partial set of reliable mirror glyphs.
    mapping = str.maketrans({
        "a":"ɒ", "b":"d", "c":"ɔ", "d":"b", "e":"ɘ", "f":"ꟻ",
        "h":"ɥ", "j":"ɾ", "k":"ʞ", "m":"m", "n":"u", "p":"q",
        "q":"p", "r":"ɿ", "s":"ƨ", "t":"ƚ", "u":"n", "v":"ʌ",
        "w":"ʍ", "y":"ʎ", "A":"Ǝ", "b":"d", "E":"Ǝ", "J":"Ⴑ",
        "L":"⅃", "M":"Ɯ", "N":"И", "P":"ꟼ", "R":"Я",
        "S":"Ƨ", "T":"⊥", "U":"Ո", "V":"Ʌ", "Y":"⅄",
        "(" : ")", ")" : "(", "[" : "]", "]" : "[",
        "{" : "}", "}" : "{", "<" : ">", ">" : "<"
    })
    return text.translate(mapping)[::-1]


def caesar(text: str, shift: int) -> str:
    out = []
    for ch in text:
        if ch.isascii() and ch.isalpha():
            base = ord("A") if ch.isupper() else ord("a")
            out.append(chr((ord(ch) - base + shift) % 26 + base))
        else:
            out.append(ch)
    return "".join(out)


def atbash(text: str) -> str:
    out = []
    for ch in text:
        if ch.isascii() and ch.isalpha():
            base = ord("A") if ch.isupper() else ord("a")
            out.append(chr(base + 25 - (ord(ch) - base)))
        else:
            out.append(ch)
    return "".join(out)


def frequencies(text: str) -> dict:
    chars = [c for c in text if not c.isspace()]
    counts = Counter(chars)
    total = sum(counts.values()) or 1
    char_rows = [{"symbol": k, "count": v, "percent": round(v * 100 / total, 2)}
                 for k, v in counts.most_common(30)]
    compact = re.sub(r"\s+", "", text)
    bigrams = Counter(compact[i:i+2] for i in range(max(0, len(compact)-1)))
    trigrams = Counter(compact[i:i+3] for i in range(max(0, len(compact)-2)))
    return {
        "characters": char_rows,
        "bigrams": [{"pattern": k, "count": v} for k, v in bigrams.most_common(12)],
        "trigrams": [{"pattern": k, "count": v} for k, v in trigrams.most_common(12)],
        "character_count": len(chars),
        "word_count": len(text.split()),
        "unique_symbols": len(counts),
    }


def heuristic_score(text: str) -> float:
    """Transparent exploratory score, not a language probability."""
    if not text:
        return 0.0
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    ratio = sum(c.isascii() for c in letters) / len(letters)
    spaces = text.count(" ")
    space_score = min(spaces / max(len(text) * 0.12, 1), 1.0)
    vowel_ratio = sum(c.lower() in "aeiou" for c in letters) / len(letters)
    vowel_score = max(0, 1 - abs(vowel_ratio - 0.38) / 0.38)
    return round(100 * (0.45 * ratio + 0.25 * space_score + 0.30 * vowel_score), 1)


def build_candidates(text: str, shift: int = 3) -> list[dict]:
    candidates = [
        ("Texto original", text, "Sin transformación"),
        ("Orden de caracteres invertido", reverse_text(text), "Invierte toda la secuencia; útil para probar lectura en sentido inverso"),
        ("Orden de palabras invertido", reverse_words(text), "Invierte el orden de las palabras"),
        ("Espejo aproximado", mirror_characters(text), "Invierte la secuencia y sustituye algunos caracteres por glifos visualmente parecidos"),
        (f"César +{shift}", caesar(text, shift), "Desplazamiento alfabético latino configurable"),
        (f"César -{shift}", caesar(text, -shift), "Desplazamiento alfabético latino en sentido contrario"),
        ("Atbash", atbash(text), "Sustituye A↔Z, B↔Y, etc. en el alfabeto latino"),
        ("ROT13", caesar(text, 13), "Rotación de 13 posiciones en el alfabeto latino"),
    ]
    results = []
    for name, value, description in candidates:
        results.append({
            "name": name,
            "text": value,
            "description": description,
            "heuristic_score": heuristic_score(value),
        })
    return sorted(results, key=lambda x: x["heuristic_score"], reverse=True)


def ocr_image(data: bytes) -> tuple[str, Optional[str]]:
    try:
        image = Image.open(BytesIO(data))
        image.verify()
        image = Image.open(BytesIO(data)).convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError):
        raise HTTPException(status_code=400, detail="El archivo no parece ser una imagen válida.")
    try:
        import pytesseract
        # Basic preprocessing. Advanced manuscript OCR is future work.
        gray = ImageOps.grayscale(image)
        gray = ImageOps.autocontrast(gray)
        text = pytesseract.image_to_string(gray, config="--psm 6")
        return text.strip(), None
    except Exception:
        return "", "No fue posible ejecutar OCR. Instala Tesseract OCR y verifica que esté disponible en el sistema."


@app.get("/", response_class=HTMLResponse)
def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/health")
def health():
    return {"status": "ok", "name": "ARCANA", "version": "0.1.0"}


@app.post("/api/analyze")
async def analyze(
    text: str = Form(""),
    shift: int = Form(3),
    normalization: str = Form("preserve"),
    image: Optional[UploadFile] = File(None),
):
    if not 0 <= shift <= 25:
        raise HTTPException(status_code=400, detail="El desplazamiento debe estar entre 0 y 25.")
    if len(text) > 100_000:
        raise HTTPException(status_code=413, detail="El texto supera el límite de 100.000 caracteres.")

    warnings = [
        "Las puntuaciones son heurísticas exploratorias, no probabilidades de traducción.",
        "El alfabeto César y Atbash de esta versión se aplican al alfabeto latino A–Z.",
        "Un resultado visualmente legible no demuestra que sea el descifrado correcto."
    ]
    extracted = ""
    if image is not None and image.filename:
        data = await image.read()
        if len(data) > MAX_IMAGE_BYTES:
            raise HTTPException(status_code=413, detail="La imagen supera el límite de 8 MB.")
        extracted, ocr_warning = ocr_image(data)
        if ocr_warning:
            warnings.append(ocr_warning)
        if extracted:
            text = (text + "\n" + extracted).strip() if text.strip() else extracted

    text = normalize_text(text, normalization)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Introduce texto o carga una imagen con texto legible.")

    return {
        "input_text": text,
        "ocr_text": extracted,
        "statistics": frequencies(text),
        "candidates": build_candidates(text, shift),
        "warnings": warnings,
        "status": "experimental",
    }
