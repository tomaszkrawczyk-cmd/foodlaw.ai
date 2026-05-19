# Wspolpraca / Contributing

Dziekujemy za zainteresowanie wspoltworzeniem tego projektu! Ponizej znajdziesz wytyczne dotyczace wkladow.

## Jak mozesz pomoc

- Aktualizacja tresci prawnych (nowe akty, nowelizacje)
- Dodanie nowych umiejetnosci (skills) dla kolejnych obszarow prawa zywnosciowego
- Uzupelnienie orzecznictwa
- Poprawa skryptow (nowe zrodla danych, lepsza konwersja)
- Poprawki bledow i literowek
- Tlumaczenia na inne jezyki

## Proces wkladu

1. Sforkuj repozytorium
2. Stworz branch (`git checkout -b feature/nowa-funkcja`)
3. Wprowadz zmiany
4. Upewnij sie, ze skrypty dzialaja (`python scripts/fetch_eurlex.py --help`)
5. Stworz commit z opisowym komunikatem
6. Wyslij Pull Request

## Standardy tresci prawnych

### Pliki przepisow (`przepisy/`)

Kazdy plik rozporzadzenia/ustawy powinien zawierac:

```markdown
---
celex: "numer CELEX (dla aktow UE)"
tytul_pl: "Pelny tytul po polsku"
tytul_en: "Full title in English"
dziennik_urzedowy: "Odniesienie do Dz.Urz. UE lub Dz.U."
data_wejscia: "Data wejscia w zycie"
ostatnia_konsolidacja: "Data ostatniej wersji skonsolidowanej"
link_eurlex: "URL do EUR-Lex lub ISAP"
---
```

### Pliki umiejetnosci (`skills/`)

Kazdy `skill.md` powinien zawierac:

1. **Definicja roli** - kim jest ekspert AI
2. **Kluczowe przepisy** - z numerami artykulow
3. **Typowe pytania** - 5-10 reprezentatywnych pytan
4. **Metodologia** - krokowa procedura analizy
5. **Wymagania cytowania** - format i zrodla
6. **Pulapki** - czeste bledy i nieporozumienia

### Orzecznictwo

Pliki orzecznicze powinny zawierac:
- Sygnature
- Date
- Skiad orzekajacy
- Teze
- Kluczowe fragmenty uzasadnienia
- Przepisy, ktorych dotyczy

## Standardy skryptow Python

- Python 3.9+
- Kazdy skrypt musi miec interfejs argparse
- Obsluga bledow sieciowych z logowaniem
- Docstringi w jezyku polskim lub angielskim
- Formatowanie zgodne z PEP 8
- Zaleznosci dodawane do `scripts/requirements.txt`

## Licencja wkladow

O ile nie zaznaczono inaczej, wszelkie wklady sa licencjonowane na warunkach
Apache-2.0, zgodnie z sekcja 5 licencji Apache 2.0.

## Kontakt

W razie pytan otworz Issue na GitHubie.
