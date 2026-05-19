# Prawo Zywnosciowe PL/EU - Baza Wiedzy dla AI

> **Baza wiedzy i zestaw umiejetnosci AI** zoptymalizowany dla duzych modeli jezykowych (LLM) - obejmuje prawo zywnosciowe Unii Europejskiej i Polski, skrypty do pobierania aktow prawnych, umiejetnosci analityczne i automatyzacje. Przeznaczony dla prawnikow specjalizujacych sie w prawie zywnosciowym.

## O projekcie

To repozytorium stanowi **kompletna baze wiedzy prawa zywnosciowego PL/EU**, zoptymalizowana do uzycia z Claude, ChatGPT i innymi asystentami AI. Zawiera:

- Ustrukturyzowane opisy kluczowych rozporzadzen UE i ustaw polskich
- Umiejetnosci (skills) definiujace role eksperckie AI dla poszczegolnych obszarow prawa zywnosciowego
- Skrypty Python do automatycznego pobierania aktow prawnych z EUR-Lex, ISAP, CBOSA i CURIA
- Przewodnik po cytowaniu zrodel prawnych
- Metodologie analizy prawa zywnosciowego

Projekt inspirowany repozytorium [claude-fuer-deutsches-recht](https://github.com/Klotzkette/claude-fuer-deutsches-recht) i dostosowany do polskiego prawa zywnosciowego.

## Zawartosc repozytorium

### Umiejetnosci AI (Skills)

| Skill | Opis |
| --- | --- |
| [`suplementy-diety`](./skills/suplementy-diety/skill.md) | Regulacje dotyczace suplementow diety - notyfikacja, sklad, oznakowanie, reklama |
| [`etykietowanie`](./skills/etykietowanie/skill.md) | Znakowanie i etykietowanie zywnosci wg Rozp. 1169/2011 |
| [`oswiadczenia-zdrowotne`](./skills/oswiadczenia-zdrowotne/skill.md) | Oswiadczenia zywieniowe i zdrowotne wg Rozp. 1924/2006 |
| [`novel-food`](./skills/novel-food/skill.md) | Nowa zywnosc wg Rozp. 2015/2283 - procedura autoryzacji, wykaz unijny |
| [`higiena-zywnosci`](./skills/higiena-zywnosci/skill.md) | Higiena srodkow spozywczych - HACCP, rejestracja, zatwierdzanie zakladow |
| [`zanieczyszczenia`](./skills/zanieczyszczenia/skill.md) | Zanieczyszczenia w zywnosci - najwyzsze dopuszczalne poziomy wg Rozp. 2023/915 |
| [`fortyfikacja`](./skills/fortyfikacja/skill.md) | Wzbogacanie zywnosci w witaminy i skladniki mineralne wg Rozp. 1925/2006 |
| [`postepowania-gis`](./skills/postepowania-gis/skill.md) | Postepowania administracyjne GIS/Sanepid - decyzje, odwolania, skarga do WSA/NSA |

### Przepisy

| Katalog | Zawartosc |
| --- | --- |
| [`przepisy/unijne/`](./przepisy/unijne/) | Kluczowe rozporzadzenia UE dot. zywnosci (178/2002, 1169/2011, 1924/2006, 1925/2006, 2015/2283, 852/2004, 853/2004, 2023/915, 609/2013) |
| [`przepisy/krajowe/`](./przepisy/krajowe/) | Polskie ustawy (o bezpieczenstwie zywnosci i zywienia, o PIS) |

### Orzecznictwo

| Katalog | Zawartosc |
| --- | --- |
| [`orzecznictwo/nsa/`](./orzecznictwo/nsa/) | Wyroki Naczelnego Sadu Administracyjnego |
| [`orzecznictwo/wsa/`](./orzecznictwo/wsa/) | Wyroki Wojewodzkich Sadow Administracyjnych |
| [`orzecznictwo/tsue/`](./orzecznictwo/tsue/) | Wyroki Trybunalu Sprawiedliwosci UE |
| [`orzecznictwo/gis-decyzje/`](./orzecznictwo/gis-decyzje/) | Decyzje Glownego Inspektora Sanitarnego |

### Materialy referencyjne

| Plik | Opis |
| --- | --- |
| [`references/cytowanie.md`](./references/cytowanie.md) | Zasady cytowania zrodel prawa zywnosciowego PL/EU |
| [`references/metodyka.md`](./references/metodyka.md) | Metodyka analizy prawa zywnosciowego |

### Skrypty

| Skrypt | Opis |
| --- | --- |
| [`scripts/fetch_eurlex.py`](./scripts/fetch_eurlex.py) | Pobieranie rozporzadzen UE z EUR-Lex (CELLAR SPARQL) |
| [`scripts/fetch_isap.py`](./scripts/fetch_isap.py) | Pobieranie polskich aktow prawnych z ISAP |
| [`scripts/fetch_cbosa.py`](./scripts/fetch_cbosa.py) | Wyszukiwanie orzeczen NSA/WSA w CBOSA |
| [`scripts/fetch_curia.py`](./scripts/fetch_curia.py) | Wyszukiwanie orzeczen TSUE w CURIA |
| [`scripts/convert_to_markdown.py`](./scripts/convert_to_markdown.py) | Konwersja pobranych plikow HTML/XML na Markdown |

## Jak korzystac z tego repozytorium

### Z Claude lub innym LLM

1. Sklonuj repozytorium lub pobierz jako ZIP
2. Wskaz LLM na odpowiedni plik `skill.md` jako kontekst
3. Zadaj pytanie dotyczace prawa zywnosciowego

Przykladowe uzycie:
```
Zaladuj skill: skills/suplementy-diety/skill.md
Pytanie: Czy produkt zawierajacy 5-HTP moze byc notyfikowany jako suplement diety w Polsce?
```

### Pobieranie aktualnych tekstow prawnych

```bash
# Zainstaluj zaleznosci
pip install -r scripts/requirements.txt

# Pobierz rozporzadzenia UE (wersje polskie)
python scripts/fetch_eurlex.py --output przepisy/unijne/raw/

# Pobierz ustawy z ISAP
python scripts/fetch_isap.py --output przepisy/krajowe/raw/

# Konwertuj na Markdown
python scripts/convert_to_markdown.py --input przepisy/unijne/raw/ --output przepisy/unijne/
```

### Automatyzacja (GitHub Actions)

Repozytorium zawiera workflow `.github/workflows/update-laws.yml`, ktory co miesiac automatycznie pobiera najnowsze wersje aktow prawnych i aktualizuje pliki Markdown.

## Objete rozporzadzenia UE

| Nr | Tytul | CELEX |
| --- | --- | --- |
| 178/2002 | Ogolne prawo zywnosciowe (General Food Law) | 32002R0178 |
| 1169/2011 | Informacja o zywnosci dla konsumentow | 32011R1169 |
| 1924/2006 | Oswiadczenia zywieniowe i zdrowotne | 32006R1924 |
| 1925/2006 | Wzbogacanie zywnosci | 32006R1925 |
| 2015/2283 | Nowa zywnosc (Novel Food) | 32015R2283 |
| 852/2004 | Higiena srodkow spozywczych | 32004R0852 |
| 853/2004 | Higiena zywnosci pochodzenia zwierzecego | 32004R0853 |
| 2023/915 | Zanieczyszczenia w zywnosci | 32023R0915 |
| 609/2013 | Zywnosc dla szczegolnych grup | 32013R0609 |

## Wazne zastrzezenia

> **UWAGA: To repozytorium NIE stanowi porady prawnej.**
>
> - Tresc ma charakter wylacznie informacyjny i edukacyjny
> - Kazdy wynik generowany przez AI wymaga weryfikacji przez prawnika
> - LLM moga generowac nieprawidlowe cytowania i sygnatury - zawsze sprawdzaj zrodla
> - Akty prawne moga ulec zmianie - weryfikuj aktualnosc przywolywanych przepisow
> - Autor nie ponosi odpowiedzialnosci za wykorzystanie tresci w praktyce

## Autor

**Tomasz Krawczyk** - prawnik specjalizujacy sie w prawie zywnosciowym z ponad 15-letnim doswiadczeniem. Wiecej na [supplemental.pl](https://supplemental.pl).

## Licencja

Podwojna licencja: **Apache License 2.0** LUB **MIT License**, do wyboru uzytkownika.

`SPDX-License-Identifier: Apache-2.0 OR MIT`

Szczegoly: [LICENSE](./LICENSE) | [LICENSE-APACHE](./LICENSE-APACHE) | [LICENSE-MIT](./LICENSE-MIT)

## Wspoludzial

Wklady sa mile widziane! Szczegoly w [CONTRIBUTING.md](./CONTRIBUTING.md).
