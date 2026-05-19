# Dostep do danych EUR-Lex programowo

Dokumentacja praktyczna dotyczaca programowego dostepu do tresci aktow prawnych
Unii Europejskiej publikowanych na EUR-Lex. Przydatna przy rozbudowie skryptow
w katalogu `scripts/` niniejszego repozytorium.

---

## 1. CELLAR SPARQL endpoint

### Informacje ogolne
- **URL**: https://publications.europa.eu/webapi/rdf/sparql
- **Dostep**: publiczny, bezplatny, BEZ rejestracji
- **Format odpowiedzi**: JSON, XML, CSV, TSV
- **Dokumentacja**: https://op.europa.eu/en/web/cellar

### Mozliwosci
- Wyszukiwanie dokumentow po numerze CELEX, tytule, dacie
- Pobieranie metadanych (tytul, data, jezyk, URI dokumentu)
- Uzyskanie URI manifestacji (HTML, PDF, XML) do bezposredniego pobrania
- Zapytania o powiazania miedzy aktami (akty zmieniane, akty zmieniajace)

### Przykladowe zapytanie SPARQL

Zapytanie pobierajace metadane i URI polskiej wersji jezykowej rozporzadzenia
na podstawie numeru CELEX (wzor z `scripts/fetch_eurlex.py`):

```sparql
PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT DISTINCT ?title ?date ?expression ?manifestation
WHERE {
    ?work cdm:resource_legal_id_celex "32002R0178"^^xsd:string .
    ?work cdm:work_date_document ?date .
    ?expression cdm:expression_belongs_to_work ?work .
    ?expression cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/PL> .
    ?expression cdm:expression_title ?title .
    OPTIONAL {
        ?manifestation cdm:manifestation_manifests_expression ?expression .
        ?manifestation cdm:manifestation_type <http://publications.europa.eu/resource/authority/file-type/HTML> .
    }
}
LIMIT 10
```

### Uzycie z Python (SPARQLWrapper)

```python
from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("https://publications.europa.eu/webapi/rdf/sparql")
sparql.setQuery(query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
```

---

## 2. EUR-Lex REST/SOAP web services

### Informacje ogolne
- **Rejestracja**: https://eur-lex.europa.eu/content/help/data-reuse/reuse-contents-eurlex-details.html
- **Kontakt**: EURLEX-HELPDESK@publications.europa.eu
- **Dostep**: wymaga rejestracji i akceptacji warunkow uzycia

### Proces rejestracji
1. Wypelnij formularz rejestracyjny na stronie EUR-Lex (link powyzej)
2. Podaj cel wykorzystania danych (badania, edukacja, aplikacja prawna)
3. Otrzymaj dane dostepu (login/haslo lub klucz API)
4. Akceptuj warunki ponownego wykorzystania

### Mozliwosci
- Pobieranie pelnych tekstow aktow prawnych w formatach: HTML, PDF, XML (Formex), DOC
- Wyszukiwanie zaawansowane (po datach, dziedzinach, autorach, statusie)
- Pobieranie masowe (bulk download) z ograniczeniami rate-limiting
- Dostep do wersji skonsolidowanych
- Dostep do metadanych Dublin Core

### Formaty danych
- **HTML** - tekst sformatowany, gotowy do wyswietlenia
- **PDF** - wersja drukowana Dz.Urz. UE
- **Formex XML** - struktura logiczna dokumentu (artykuly, ustepy, punkty)
- **AKN (Akoma Ntoso)** - nowy format XML dla aktow prawnych UE

---

## 3. Open Data Portal

### Informacje ogolne
- **URL**: https://data.europa.eu/
- **Dostep**: publiczny, bezplatny
- **CELLAR**: repozytorium tresci lezace u podstaw EUR-Lex

### Mozliwosci
- Przegladanie datasetow prawnych UE
- Pobieranie metadanych w formatach RDF, JSON-LD
- Dostep do niektorych zbiorow danych bez rejestracji
- Laczenie z innymi bazami danych UE (DG SANTE, EFSA, RASFF)

### Powiazanie z CELLAR
CELLAR to wewnetrzne repozytorium tresci Urzedu Publikacji UE. Endpoint SPARQL
(sekcja 1 powyzej) daje dostep do metadanych przechowywanych w CELLAR.
Pelne teksty sa dostepne przez URI manifestacji uzyskane z zapytan SPARQL.

---

## 4. Praktyczne wskazowki dla skryptow

### SPARQL jako najlatwiejszy punkt wejscia
- Nie wymaga rejestracji - mozna zaczac natychmiast
- Pozwala uzyskac URI do bezposredniego pobrania dokumentu
- Odpowiedni do pobierania metadanych i wyszukiwania

### Wzorzec URL pelnego tekstu
```
https://eur-lex.europa.eu/legal-content/PL/TXT/?uri=CELEX:{celex_number}
```
Przyklad: `https://eur-lex.europa.eu/legal-content/PL/TXT/?uri=CELEX:32002R0178`

### Wzorzec URL wersji skonsolidowanej
```
https://eur-lex.europa.eu/legal-content/PL/TXT/?uri=CELEX:0{celex_number}-{data_RRRRMMDD}
```
Przyklad: `https://eur-lex.europa.eu/legal-content/PL/TXT/?uri=CELEX:02011R1169-20240514`

### Rate limiting i dobre praktyki
- Dodawaj opoznienia miedzy zadaniami (min. 2 sekundy)
- Ustawiaj wlasciwy naglowek User-Agent (identyfikacja projektu)
- Nie pobieraj wiecej niz kilkadziesiat dokumentow naraz
- Korzystaj z wersji skonsolidowanych (aktualnych) zamiast oryginalnych
- Cachuj pobrane dokumenty lokalnie

### Alternatywa: Formex XML z CELLAR
1. Uzyj SPARQL aby uzyskac URI manifestacji XML
2. Pobierz plik Formex XML bezposrednio z CELLAR
3. Parsuj strukture XML (artykuly, ustepy, punkty)
4. Konwertuj na Markdown za pomoca `scripts/convert_to_markdown.py`

### Znane ograniczenia (stan na 2025)
- EUR-Lex stosuje zabezpieczenia WAF/bot protection - automatyczne pobieranie HTML
  moze byc blokowane (kody 403/429)
- CELLAR SPARQL endpoint jest stabilniejszy (rzadziej blokowany)
- Niektorych starszych aktow brak w wersji polskiej w CELLAR
- Wersje skonsolidowane moga miec opoznienie wzgledem nowelizacji
