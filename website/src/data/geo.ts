export const NAP = {
  name: 'Tomasz Krawczyk',
  org: 'FOODLAW.ai',
  phone: '+48608699845',
  phoneDisplay: '+48 608 699 845',
  email: 'tomaszkrawczyk@supplemental.pl',
  streetAddress: 'ul. Floriańska 6/1',
  postalCode: '03-707',
  addressLocality: 'Warszawa',
  addressRegion: 'Mazowieckie',
  addressCountry: 'PL',
  url: 'https://foodlaw.ai',
  // sameAs asserts identity. FOODLAW.ai is not the kancelaria and not C.L.A.I.M.S.
  sameAs: [
    'https://github.com/tomaszkrawczyk-cmd/foodlaw.ai',
  ],
  legalService: {
    name: 'Supple Mental',
    url: 'https://supplemental.pl',
    id: 'https://supplemental.pl/#org',
  },
  personSameAs: [
    'https://www.linkedin.com/in/tomasz-krawczyk-23059a245',
    'https://x.com/tomasztadeo',
  ],
} as const;

export type FaqItem = {
  slug: string;
  altSlug: string;
  question: string;
  answer: string;
  hubSlug: string;
};

export type HubItem = {
  slug: string;
  altSlug: string;
  title: string;
  description: string;
  body: string[];
  related: string[];
  ctaHref: string;
  ctaLabel: string;
};

export const faqs = {
  pl: [
    {
      slug: 'czym-jest-prawo-zywnosciowe',
      altSlug: 'what-is-food-law',
      question: 'Czym jest prawo żywnościowe?',
      answer:
        'Prawo żywnościowe to zespół przepisów regulujących produkcję, przetwarzanie, dystrybucję i sprzedaż żywności. W UE ramą jest rozporządzenie 178/2002 (General Food Law); w Polsce — ustawa o bezpieczeństwie żywności i żywienia oraz akty wykonawcze. Obejmuje m.in. znakowanie, oświadczenia, nową żywność, dodatki, higienę i nadzór GIS.',
      hubSlug: 'prawo-zywnosciowe',
    },
    {
      slug: 'jak-notyfikowac-suplement-diety',
      altSlug: 'how-to-notify-a-food-supplement',
      question: 'Jak notyfikować suplement diety?',
      answer:
        'W Polsce powiadomienie o wprowadzeniu suplementu diety składa się do Głównego Inspektora Sanitarnego (GIS) przez system elektroniczny. W zgłoszeniu podaje się skład, dawkowanie i załącza etykietę. GIS może wezwać do uzupełnień lub zakwestionować kwalifikację produktu (np. jako FSMP albo nową żywność). To nie jest zezwolenie — to powiadomienie z możliwością sprzeciwu.',
      hubSlug: 'suplementy-diety',
    },
    {
      slug: 'co-to-sa-oswiadczenia-zdrowotne',
      altSlug: 'what-are-health-claims',
      question: 'Co to są oświadczenia zdrowotne?',
      answer:
        'Oświadczenia zdrowotne to komunikaty sugerujące związek między żywnością a zdrowiem. W UE reguluje je rozporządzenie 1924/2006. Dozwolone oświadczenia są w unijnym rejestrze; każde ma warunki użycia (składnik, dawka, populacja). Oświadczenia botaniczne i on-hold nie są automatycznie legalne — wymagają oceny ryzyka i kontekstu etykiety.',
      hubSlug: 'oswiadczenia-zdrowotne',
    },
    {
      slug: 'czym-jest-novel-food',
      altSlug: 'what-is-novel-food',
      question: 'Czym jest novel food?',
      answer:
        'Novel food (nowa żywność) to żywność, która nie była w znacznym stopniu spożywana w UE przed 15 maja 1997 r. Wprowadzenie na rynek wymaga autoryzacji na podstawie rozporządzenia 2015/2283 (EFSA + Komisja). Typowe ryzyka: ekstrakty roślinne, grzyby, peptydy, składniki z tradycji pozaunijnej bez udokumentowanej historii spożycia.',
      hubSlug: 'nowa-zywnosc',
    },
    {
      slug: 'jak-dziala-system-rasff',
      altSlug: 'how-does-rasff-work',
      question: 'Jak działa system RASFF?',
      answer:
        'RASFF (Rapid Alert System for Food and Feed) to unijny system wczesnego ostrzegania o zagrożeniach związanych z żywnością i paszami. Państwa członkowskie zgłaszają powiadomienia (alert, information, border rejection). Dla przedsiębiorcy oznacza to m.in. wycofanie, powiadomienie konsumentów i dokumentację identyfikowalności. Nie jest to samodzielna podstawa kary — ale jest sygnałem nadzoru.',
      hubSlug: 'znakowanie-zywnosci',
    },
  ] satisfies FaqItem[],
  en: [
    {
      slug: 'what-is-food-law',
      altSlug: 'czym-jest-prawo-zywnosciowe',
      question: 'What is food law?',
      answer:
        'Food law is the body of rules governing production, processing, distribution and sale of food. At EU level the framework is Regulation 178/2002 (General Food Law); in Poland it is the Food Safety and Nutrition Act plus implementing acts. It covers labelling, claims, novel food, additives, hygiene and sanitary-inspection supervision.',
      hubSlug: 'food-law',
    },
    {
      slug: 'how-to-notify-a-food-supplement',
      altSlug: 'jak-notyfikowac-suplement-diety',
      question: 'How to notify a dietary supplement?',
      answer:
        'In Poland a notification of a food supplement is filed with the Chief Sanitary Inspector (GIS) through the electronic system. The file includes composition, posology and the label. GIS may request supplements or challenge the product’s classification (e.g. as FSMP or novel food). It is a notification, not an authorisation — GIS may still object.',
      hubSlug: 'dietary-supplements',
    },
    {
      slug: 'what-are-health-claims',
      altSlug: 'co-to-sa-oswiadczenia-zdrowotne',
      question: 'What are health claims?',
      answer:
        'Health claims are messages that imply a relationship between food and health. In the EU they are governed by Regulation 1924/2006. Authorised claims sit in the Union register and each has conditions of use (substance, dose, target population). Botanical and on-hold claims are not automatically lawful — they need a risk assessment and label context.',
      hubSlug: 'health-claims',
    },
    {
      slug: 'what-is-novel-food',
      altSlug: 'czym-jest-novel-food',
      question: 'What is novel food?',
      answer:
        'Novel food is food not consumed to a significant degree in the EU before 15 May 1997. Placing it on the market requires authorisation under Regulation 2015/2283 (EFSA + Commission). Typical risk areas: plant extracts, fungi, peptides, and ingredients from non-EU traditions without a documented history of consumption.',
      hubSlug: 'novel-food',
    },
    {
      slug: 'how-does-rasff-work',
      altSlug: 'jak-dziala-system-rasff',
      question: 'How does the RASFF system work?',
      answer:
        'RASFF (Rapid Alert System for Food and Feed) is the EU early-warning system for food and feed hazards. Member States file alerts, information notifications and border rejections. For a business this can mean withdrawal, consumer notification and traceability records. RASFF is not a standalone penalty — it is a supervision signal.',
      hubSlug: 'food-labelling',
    },
  ] satisfies FaqItem[],
} as const;

export const hubs = {
  pl: [
    {
      slug: 'oswiadczenia-zdrowotne',
      altSlug: 'health-claims',
      title: 'Oświadczenia zdrowotne (rozporządzenie 1924/2006)',
      description:
        'Hub: oświadczenia żywieniowe i zdrowotne w UE — rejestr Komisji, warunki użycia, botanicals, narzędzie app.foodlaw.ai.',
      body: [
        'Rozporządzenie 1924/2006 zakazuje oświadczeń żywieniowych i zdrowotnych, które nie są dozwolone i nie spełniają warunków użycia. Rejestr unijny jest źródłem „co wolno”, nie „co brzmi wiarygodnie”.',
        'Najczęstsze błędy: parafraza oświadczenia spoza rejestru, dawka poniżej warunku, oświadczenie botaniczne na etykiecie PL bez oceny ryzyka, mylenie oświadczenia zdrowotnego z oświadczeniem żywieniowym.',
        'Do weryfikacji konkretnego składnika służy app.foodlaw.ai (C.L.A.I.M.S.). Opinia prawna i etykieta: supplemental.pl. C.L.A.I.M.S. nie jest urzędowym rejestrem KE (2318 = 2078 SANCO on-hold + 240 rozp. 432/2012).',
      ],
      related: ['co-to-sa-oswiadczenia-zdrowotne'],
      ctaHref: 'https://app.foodlaw.ai',
      ctaLabel: 'Sprawdź oświadczenie w C.L.A.I.M.S.',
    },
    {
      slug: 'suplementy-diety',
      altSlug: 'dietary-supplements',
      title: 'Suplementy diety — notyfikacja GIS i kwalifikacja',
      description:
        'Hub: powiadomienie GIS, granica suplement / FSMP / nowa żywność, etykieta i skład.',
      body: [
        'Suplement diety w Polsce podlega powiadomieniu do GIS, nie „rejestracji zezwoleniowej”. GIS może zakwestionować skład, dawkę, nową żywność albo prezentację leczniczą.',
        'Kwalifikacja produktu (suplement vs FSMP vs żywność wzbogacana vs lek) jest decyzją prawną, nie marketingową. Błąd na starcie kosztuje wycofanie i spór administracyjny.',
        'Praktycznie: etykieta, skład i notyfikacja powinny być spięte zanim produkt wejdzie do sprzedaży. Wsparcie: supplemental.pl.',
      ],
      related: ['jak-notyfikowac-suplement-diety'],
      ctaHref: 'https://supplemental.pl',
      ctaLabel: 'Notyfikacja i etykieta — supplemental.pl',
    },
    {
      slug: 'nowa-zywnosc',
      altSlug: 'novel-food',
      title: 'Nowa żywność (rozporządzenie 2015/2283)',
      description:
        'Hub: status novel food, katalog unijny, tradycyjna żywność z państw trzecich, ekstrakty.',
      body: [
        'Składnik bez znaczącej historii spożycia w UE przed 15 maja 1997 r. jest nową żywnością, dopóki nie wykażesz inaczej. Ciężar dowodu leży na wprowadzającym.',
        'Katalog unijny i wcześniejsze autoryzacje są punktem startu, nie tarczą. Ekstrakt standaryzowany to często inny produkt niż ziele spożywane tradycyjnie.',
        'Przed notyfikacją suplementu sprawdź novel food — GIS robi to jako pierwsze. Konsultacja: supplemental.pl.',
      ],
      related: ['czym-jest-novel-food'],
      ctaHref: 'https://supplemental.pl',
      ctaLabel: 'Ocena statusu novel food',
    },
    {
      slug: 'znakowanie-zywnosci',
      altSlug: 'food-labelling',
      title: 'Znakowanie żywności (rozporządzenie 1169/2011)',
      description:
        'Hub: etykieta, alergeny, nazwa, wartości odżywcze, prezentacja wprowadzająca w błąd.',
      body: [
        'Rozporządzenie 1169/2011 ustala obowiązkowe informacje na żywności, w tym alergeny, nazwę, wykaz składników i wartości odżywcze. Prezentacja nie może wprowadzać w błąd co do cech, składu albo skutków zdrowotnych.',
        'Dla suplementów dochodzą przepisy krajowe i zakaz przypisywania właściwości leczniczych. Błąd na froncie opakowania jest częstszy niż błąd w tabeli.',
        'RASFF i kontrole GIS często startują od etykiety. Audyt: supplemental.pl.',
      ],
      related: ['jak-dziala-system-rasff', 'czym-jest-prawo-zywnosciowe'],
      ctaHref: 'https://supplemental.pl',
      ctaLabel: 'Audyt etykiety',
    },
    {
      slug: 'prawo-zywnosciowe',
      altSlug: 'food-law',
      title: 'Prawo żywnościowe UE i Polski',
      description:
        'Hub: 178/2002, ustawa o bezpieczeństwie żywności i żywienia, nadzór GIS, orzecznictwo.',
      body: [
        'FOODLAW.ai zbiera narzędzia AI do prawa żywnościowego UE i polskiego: oświadczenia, skład, notyfikacje, odwołania. Twórca: Tomasz Krawczyk. Kancelaria (encja odrębna): supplemental.pl.',
        'Źródła: rozporządzenia UE, polskie ustawy i akty wykonawcze, orzecznictwo NSA/WSA/TSUE, decyzje GIS. Baza otwarta: github.com/tomaszkrawczyk-cmd/foodlaw.ai.',
        'To nie jest porada prawna. Do sprawy indywidualnej — konsultacja na supplemental.pl albo 15 min w kalendarzu.',
      ],
      related: ['czym-jest-prawo-zywnosciowe'],
      ctaHref: 'https://supplemental.pl/kontakt/',
      ctaLabel: 'Konsultacja na supplemental.pl',
    },
  ] satisfies HubItem[],
  en: [
    {
      slug: 'health-claims',
      altSlug: 'oswiadczenia-zdrowotne',
      title: 'Health claims (Regulation 1924/2006)',
      description:
        'Hub: EU nutrition and health claims — Union register, conditions of use, botanicals, app.foodlaw.ai.',
      body: [
        'Regulation 1924/2006 prohibits nutrition and health claims that are not authorised and do not meet conditions of use. The Union register is the source of “what is allowed”, not “what sounds plausible”.',
        'Typical failures: paraphrasing a claim outside the register, dose below the condition, a botanical claim on a PL label without risk assessment, mixing health and nutrition claims.',
        'To check a specific substance use C.L.A.I.M.S. at app.foodlaw.ai (2318 records: 2078 SANCO on-hold + 240 Reg. 432/2012). Not the official EU Register. Legal opinion: supplemental.pl.',
      ],
      related: ['what-are-health-claims'],
      ctaHref: 'https://app.foodlaw.ai',
      ctaLabel: 'Check a claim in C.L.A.I.M.S.',
    },
    {
      slug: 'dietary-supplements',
      altSlug: 'suplementy-diety',
      title: 'Food supplements — GIS notification and classification',
      description:
        'Hub: GIS notification, the supplement / FSMP / novel-food boundary, label and composition.',
      body: [
        'In Poland a food supplement is notified to GIS; it is not an authorisation. GIS may challenge composition, dose, novel-food status or medicinal presentation.',
        'Classification (supplement vs FSMP vs fortified food vs medicinal product) is a legal call, not a marketing one. A mistake at launch means withdrawal and an administrative dispute.',
        'Label, composition and notification should be aligned before first sale. Support: supplemental.pl.',
      ],
      related: ['how-to-notify-a-food-supplement'],
      ctaHref: 'https://supplemental.pl',
      ctaLabel: 'Notification and label — supplemental.pl',
    },
    {
      slug: 'novel-food',
      altSlug: 'nowa-zywnosc',
      title: 'Novel food (Regulation 2015/2283)',
      description:
        'Hub: novel-food status, Union list, traditional foods from third countries, extracts.',
      body: [
        'An ingredient without a significant history of consumption in the EU before 15 May 1997 is novel food until you prove otherwise. The burden sits on the operator.',
        'The Union list and prior authorisations are a starting point, not a shield. A standardised extract is often a different product from the traditionally consumed herb.',
        'Check novel-food status before GIS notification — inspectors do. Consult: supplemental.pl.',
      ],
      related: ['what-is-novel-food'],
      ctaHref: 'https://supplemental.pl',
      ctaLabel: 'Novel-food status review',
    },
    {
      slug: 'food-labelling',
      altSlug: 'znakowanie-zywnosci',
      title: 'Food labelling (Regulation 1169/2011)',
      description:
        'Hub: label, allergens, name, nutrition declaration, misleading presentation.',
      body: [
        'Regulation 1169/2011 sets mandatory food information, including allergens, name, ingredients list and nutrition declaration. Presentation must not mislead as to characteristics, composition or health effects.',
        'Supplements add national rules and a ban on attributing medicinal properties. Front-of-pack errors are more common than table errors.',
        'RASFF and GIS inspections often start from the label. Audit: supplemental.pl.',
      ],
      related: ['how-does-rasff-work', 'what-is-food-law'],
      ctaHref: 'https://supplemental.pl',
      ctaLabel: 'Label audit',
    },
    {
      slug: 'food-law',
      altSlug: 'prawo-zywnosciowe',
      title: 'EU and Polish food law',
      description:
        'Hub: 178/2002, the Polish Food Safety and Nutrition Act, GIS supervision, case law.',
      body: [
        'FOODLAW.ai is a set of AI tools for EU and Polish food law: claims, composition, notifications, appeals. Author: Tomasz Krawczyk. The law firm (separate entity) is supplemental.pl.',
        'Sources: EU regulations, Polish statutes and implementing acts, NSA/WSA/CJEU case law, GIS decisions. Open collection: github.com/tomaszkrawczyk-cmd/foodlaw.ai.',
        'This is not legal advice. For an individual matter — consult supplemental.pl or book a 15-minute slot.',
      ],
      related: ['what-is-food-law'],
      ctaHref: 'https://supplemental.pl/kontakt/',
      ctaLabel: 'Consult on supplemental.pl',
    },
  ] satisfies HubItem[],
} as const;

export function faqUrl(lang: 'pl' | 'en', slug: string) {
  return lang === 'pl' ? `https://foodlaw.ai/faq/${slug}/` : `https://foodlaw.ai/en/faq/${slug}/`;
}

export function hubUrl(lang: 'pl' | 'en', slug: string) {
  return lang === 'pl' ? `https://foodlaw.ai/huby/${slug}/` : `https://foodlaw.ai/en/hubs/${slug}/`;
}

export function faqIndexUrl(lang: 'pl' | 'en') {
  return lang === 'pl' ? 'https://foodlaw.ai/faq/' : 'https://foodlaw.ai/en/faq/';
}

export function hubIndexUrl(lang: 'pl' | 'en') {
  return lang === 'pl' ? 'https://foodlaw.ai/huby/' : 'https://foodlaw.ai/en/hubs/';
}
