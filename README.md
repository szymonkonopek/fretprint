# Fretprint

Zamienia zdjęcie wykresu skali gitarowej (12 pozycji na stronie) na czysty, kolorowy wykres A4 gotowy do druku. Potrafi też wygenerować wykres dowolnej skali z listy bez zdjęcia.

## Uruchomienie

macOS: kliknij dwukrotnie `start.command`. Przy pierwszym uruchomieniu instaluje zależności, potem otwiera przeglądarkę na `http://127.0.0.1:5050/`.

Ręcznie:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python app.py
```

Zmienne środowiskowe: `PORT` (domyślnie 5050), `OPEN_BROWSER=0` wyłącza automatyczne otwieranie przeglądarki.

## Jak to działa

1. Wgrywasz zdjęcie całej strony z 12 diagramami (PNG, JPG, HEIC).
2. Program znajduje 12 siatek, odczytuje kropki i rozpoznaje skalę na podstawie tytułu (OCR), układu kropek i kolorów.
3. Wybierasz skalę wykresu wyjściowego: tę ze zdjęcia albo dowolną inną.
4. Pobierasz PNG lub PDF w formacie A4 (300 dpi). Przycisk „Wszystkie skale (ZIP)” pobiera komplet.

Komplet gotowych wykresów bez uruchamiania serwera:

```bash
.venv/bin/python generate_all.py wykresy
```

## Model wykresu

Każdy diagram pokazuje to samo okno sześciu progów w innej tonacji: pozycja `n+1` to ta sama skala przesunięta o jeden próg w dół. Struny biegną od lewej E A D G B e. Pierwszy i ostatni rząd (szare) to progi sąsiadujące z pozycją; w tych rzędach pomijane są dźwięki, które powtarzają się na sąsiedniej strunie w białej części diagramu.

Kolory oznaczają stopnie skali: 1 czerwony, 2 pomarańczowy, 3 żółty, 4 zielony, 5 niebieski, 6 granatowy, 7 fioletowy. Stopień obniżony lub podwyższony ma na kropce `b` albo `#`.

Mody skali durowej (Ionian, Dorian, Phrygian, Lydian, Mixolydian, Aeolian, Locrian) mają identyczne kształty i różnią się tylko tym, który dźwięk jest pierwszym stopniem. Harmonic Minor i Minor Pentatonic używają prymy skali Aeolian, Major Pentatonic i Diminished prymy skali Ionian.

Skale są zdefiniowane w `converter/scales.py`; nową skalę dodaje jeden wpis w `SCALES`.

## Ograniczenia rozpoznawania zdjęć

- Na zdjęciu musi być cała strona: 4 kolumny po 3 diagramy, w miarę prosto i wypełniająca kadr.
- Wyblakłe zdjęcia modów bez czytelnego tytułu nie pozwalają ustalić skali (kształty są wspólne); wtedy skalę wybiera się z listy.
- Wykres, który nie pasuje do żadnej znanej skali, można odtworzyć kropka w kropkę z kolorami odczytanymi ze zdjęcia.

## Testy

```bash
.venv/bin/python -m pytest
```
