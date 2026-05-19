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
| [`dodatki-do-zywnosci`](./skills/dodatki-do-zywnosci/skill.md) | Dodatki do zywnosci (food additives) - numery E, klasy funkcjonalne, autoryzacja, re-evaluation |
| [`gmo`](./skills/gmo/skill.md) | Genetycznie zmodyfikowana zywnosc i pasza - autoryzacja, etykietowanie, prog 0,9% |
| [`zywnosc-ekologiczna`](./skills/zywnosc-ekologiczna/skill.md) | Produkcja ekologiczna - certyfikacja, logo UE, import, konwersja |
| [`materialy-kontaktowe`](./skills/materialy-kontaktowe/skill.md) | Materialy i wyroby do kontaktu z zywnoscia - migracja, deklaracje zgodnosci |
| [`aromaty`](./skills/aromaty/skill.md) | Srodki aromatyzujace - aromaty naturalne, FTNF, wykaz unijny |
| [`enzymy`](./skills/enzymy/skill.md) | Enzymy spozywcze - autoryzacja, wykaz unijny, substancje pomocnicze |
| [`pestycydy`](./skills/pestycydy/skill.md) | Pozostalosci pestycydow (NDP) w zywnosci - MRL, monitoring, RASFF |
| [`zywnosc-dla-niemowlat`](./skills/zywnosc-dla-niemowlat/skill.md) | Zywnosc dla niemowlat i malych dzieci - Rozp. 609/2013, akty delegowane |
| [`fsmp`](./skills/fsmp/skill.md) | Zywnosc specjalnego przeznaczenia medycznego (FSMP) - kwalifikacja, wymogi, granica z suplementami |
| [`reklama-zywnosci`](./skills/reklama-zywnosci/skill.md) | Reklama i marketing zywnosci - claims w reklamie, influencer marketing, dzieci |
| [`rozporzadzenia-delegowane`](./skills/rozporzadzenia-delegowane/skill.md) | Akty delegowane i wykonawcze w prawie zywnosciowym UE - komitologia, sledzenie zmian |

### Przepisy

| Katalog | Zawartosc |
| --- | --- |
| [`przepisy/unijne/`](./przepisy/unijne/) | Kluczowe rozporzadzenia UE dot. zywnosci (178/2002, 1169/2011, 1924/2006, 1925/2006, 2015/2283, 852/2004, 853/2004, 2023/915, 609/2013, 1333/2008, 1829/2003, 1830/2003, 2018/848, 1935/2004, 10/2011, 1334/2008, 1332/2008) |
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

> **Uwaga**: EUR-Lex, ISAP oraz CURIA stosuja obecnie zabezpieczenia WAF/bot protection, ktore blokuja automatyczne pobieranie tresci. Skrypty ponizej moga wymagac w przyszlosci dostepu przez przegladarke (headless browser) lub uwierzytelnienia kluczem API.

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
| 1333/2008 | Dodatki do zywnosci (Food Additives) | 32008R1333 |
| 1829/2003 | Genetycznie zmodyfikowana zywnosc i pasza | 32003R1829 |
| 1830/2003 | Identyfikowalnosc i etykietowanie GMO | 32003R1830 |
| 2018/848 | Produkcja ekologiczna i znakowanie | 32018R0848 |
| 1935/2004 | Materialy do kontaktu z zywnoscia (FCM framework) | 32004R1935 |
| 10/2011 | Materialy z tworzyw sztucznych do kontaktu z zywnoscia | 32011R0010 |
| 1334/2008 | Srodki aromatyzujace | 32008R1334 |
| 1332/2008 | Enzymy spozywcze | 32008R1332 |
| 396/2005 | Najwyzsze dopuszczalne poziomy pozostalosci pestycydow (MRL) | 32005R0396 |
| 2016/127 | Preparaty do poczatkowego i dalszego zywienia niemowlat (akt del.) | 32016R0127 |
| 2016/128 | Zywnosc specjalnego przeznaczenia medycznego - FSMP (akt del.) | 32016R0128 |
| 2017/1798 | Srodki zastepujace cala diete do kontroli masy ciala (akt del.) | 32017R1798 |

## Dokumenty wytycznych / Guidance

Katalog [`guidance/`](./guidance/) zawiera zestawienia pytan i odpowiedzi (Q&A) opracowane na podstawie wytycznych Komisji Europejskiej i praktyki stosowania prawa zywnosciowego:

| Plik | Temat |
| --- | --- |
| [`qa-food-information-1169-2011.md`](./guidance/qa-food-information-1169-2011.md) | Informacja o zywnosci dla konsumentow |
| [`qa-health-claims-1924-2006.md`](./guidance/qa-health-claims-1924-2006.md) | Oswiadczenia zywieniowe i zdrowotne |
| [`qa-novel-food-2015-2283.md`](./guidance/qa-novel-food-2015-2283.md) | Nowa zywnosc (novel food) |
| [`qa-organic-2018-848.md`](./guidance/qa-organic-2018-848.md) | Produkcja ekologiczna |
| [`qa-food-additives-1333-2008.md`](./guidance/qa-food-additives-1333-2008.md) | Dodatki do zywnosci |
| [`qa-gmo-1829-2003.md`](./guidance/qa-gmo-1829-2003.md) | GMO w zywnosci i paszy |
| [`qa-food-hygiene.md`](./guidance/qa-food-hygiene.md) | Higiena zywnosci |
| [`qa-contaminants.md`](./guidance/qa-contaminants.md) | Zanieczyszczenia w zywnosci |
| [`qa-food-contact-materials.md`](./guidance/qa-food-contact-materials.md) | Materialy do kontaktu z zywnoscia |
| [`qa-flavourings.md`](./guidance/qa-flavourings.md) | Srodki aromatyzujace |
| [`qa-food-enzymes.md`](./guidance/qa-food-enzymes.md) | Enzymy spozywcze |
| [`qa-pesticides.md`](./guidance/qa-pesticides.md) | Pozostalosci pestycydow (NDP/MRL) |
| [`qa-infant-food.md`](./guidance/qa-infant-food.md) | Zywnosc dla niemowlat i malych dzieci |
| [`qa-fsmp.md`](./guidance/qa-fsmp.md) | Zywnosc specjalnego przeznaczenia medycznego (FSMP) |
| [`qa-food-advertising.md`](./guidance/qa-food-advertising.md) | Reklama i marketing zywnosci |

## Dokumentacja techniczna

| Plik | Opis |
| --- | --- |
| [`docs/eurlex-api-access.md`](./docs/eurlex-api-access.md) | Dostep do danych EUR-Lex programowo (SPARQL, REST API) |

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

Licencja: **Apache License 2.0**

`SPDX-License-Identifier: Apache-2.0`

Szczegoly: [LICENSE](./LICENSE)

## Wspoludzial

Wklady sa mile widziane! Szczegoly w [CONTRIBUTING.md](./CONTRIBUTING.md).
