/**
 * Public MCP server facts.
 * Tool names, titles and descriptions are copied from the server card
 * (supplemental-pl 1.1.0, fetched 2026-11-17). Do not paraphrase them.
 * Connection snippets match https://supplemental.pl/en/tools/mcp-server/.
 */
export const MCP_PAGE = {
  pl: 'https://foodlaw.ai/serwer-mcp/',
  en: 'https://foodlaw.ai/en/mcp-server/',
} as const;

export const MCP_PATH = {
  pl: '/serwer-mcp/',
  en: '/en/mcp-server/',
} as const;

export const mcpServer = {
  "endpoint": "https://mcp.supplemental.pl/mcp",
  "registryName": "pl.supplemental/foodlaw",
  "serverCard": "https://mcp.supplemental.pl/.well-known/mcp/server-card.json",
  "health": "https://mcp.supplemental.pl/health",
  "name": "supplemental-pl",
  "title": "supplemental.pl — EU/PL food law",
  "version": "1.1.0",
  "description": "Read-only EU/Polish food-law reference from supplemental.pl (Tomasz Krawczyk). Tools: knowledge articles (PL/EN/DE), the official EU Register of health claims and the EU Novel Food Catalogue (EC data, CC BY 4.0), C.L.A.I.M.S. claim matching incl. botanicals on hold, the Polish GIS notification procedure, and a deterministic nutrition calculation (Nutrimetr). Rules: an EFSA opinion is not an authorisation; botanicals on hold are not authorised; a GIS notification is not a novel food authorisation. Every result links a supplemental.pl page and a legal source. Not legal advice. No prices.",
  "transport": "streamable-http",
  "authenticationRequired": false,
  "protocolVersions": [
    "2026-07-28",
    "2025-11-25",
    "2025-06-18",
    "2025-03-26"
  ],
  "license": "Content © supplemental.pl; EU register data © European Union, CC BY 4.0",
  "docs": {
    "pl": "https://supplemental.pl/narzedzia/serwer-mcp/",
    "en": "https://supplemental.pl/en/tools/mcp-server/"
  },
  "source": "https://github.com/tomaszkrawczyk-cmd/supplemental-eu-food-law-mcp",
  "claimsTools": [
    "search_claims_foodlaw",
    "get_claim_foodlaw"
  ],
  "tools": [
    {
      "name": "search_articles",
      "title": "Search supplemental.pl knowledge articles",
      "description": "Full-text search of supplemental.pl knowledge articles on EU/PL food law (health claims, novel food, supplements, labelling, CJEU case law) in Polish, English or German. Returns titles, URLs, dates, summaries and language versions. Example: query \"novel food NMN\", lang \"en\"."
    },
    {
      "name": "get_article",
      "title": "Get a supplemental.pl article",
      "description": "Return one supplemental.pl knowledge article by URL or slug: summary, headings, a text excerpt, legal references named in it and its PL/EN/DE versions. Pass lang to get another language version. Example: url \"novel-food-food-supplements-eu\" (slug) or the full URL https://supplemental.pl/en/knowledge/novel-food-food-supplements-eu/."
    },
    {
      "name": "check_health_claim",
      "title": "Check the EU Register of health claims",
      "description": "Look up a nutrient/substance in the official EU Register of nutrition and health claims (European Commission data, refreshed weekly). Shows whether each claim is Authorised, Non-authorised or Revoked, its conditions of use, the EFSA question and the legal act. Example: substance \"vitamin C\", claim_text \"immune system\"."
    },
    {
      "name": "novel_food_status",
      "title": "Check the EU Novel Food Catalogue",
      "description": "Look up a food or ingredient in the EU Novel Food Catalogue (European Commission data, refreshed weekly): status per part/form (Novel food, Not novel in food, Not novel in food supplements, Authorised novel food, consultation request), with links to Reg. 2015/2283 and the Union list. Example: name \"Withania somnifera\" or \"NMN\"."
    },
    {
      "name": "search_claims_foodlaw",
      "title": "Match health claims with C.L.A.I.M.S.",
      "description": "Match an ingredient (and optional dose) against Reg. 432/2012 authorised claims and the SANCO/11074/2013 botanical list via C.L.A.I.M.S. (FOODLAW.ai). Botanical claims are always returned as regulatory_status \"on_hold\" (not authorised). Usage limit: 2000 calls per user per day (10000 for shared Google network addresses). Example: substance \"ashwagandha\" or \"vitamin C\", optional dose \"300 mg\"."
    },
    {
      "name": "get_claim_foodlaw",
      "title": "Get a C.L.A.I.M.S. claim by ID",
      "description": "Fetch one claim from C.L.A.I.M.S. by its numeric ID (from search_claims_foodlaw). Botanicals are always \"on_hold\". Usage limit: 2000 calls per user per day (10000 for shared Google network addresses). Example: id 10 (from search_claims_foodlaw)."
    },
    {
      "name": "gis_notification_steps",
      "title": "Polish GIS notification of a food supplement — steps",
      "description": "Step-by-step procedure for notifying a food supplement to the Polish Chief Sanitary Inspectorate (GIS, Art. 29–30 of the Food and Nutrition Safety Act), from the supplemental.pl article. A GIS notification is not a novel food authorisation. Example: lang \"en\" or \"pl\"."
    },
    {
      "name": "nutrition_calc",
      "title": "Calculate a nutrition declaration (Nutrimetr)",
      "description": "Deterministic nutrition calculation for a recipe (no AI): energy and nutrients per 100 g, micronutrients with %NRV, candidate nutrition claims (withheld if any ingredient is unresolved), allergens and QUID hints. Ingredient lines with mass or volume and the ingredient name in Polish (the food table matches Polish names only; translate other languages first), e.g. \"mąka owsiana 500 g\", \"mleko 200 ml\", \"miód 50 g\". Usage limit: 20 calculations per user per day (500 for shared Google network addresses). Example: ingredients [\"mleko 200 ml\"] or [\"mąka owsiana 500 g\", \"mleko 200 ml\", \"miód 50 g\"]."
    }
  ],
  "configs": {
    "cursor": "{\n  \"mcpServers\": {\n    \"supplemental-foodlaw\": {\n      \"url\": \"https://mcp.supplemental.pl/mcp\"\n    }\n  }\n}\n",
    "claudeDesktop": "{\n  \"mcpServers\": {\n    \"supplemental-foodlaw\": {\n      \"command\": \"npx\",\n      \"args\": [\"-y\", \"mcp-remote\", \"https://mcp.supplemental.pl/mcp\"]\n    }\n  }\n}\n",
    "claudeCode": "claude mcp add --transport http supplemental-foodlaw https://mcp.supplemental.pl/mcp\n",
    "vscode": "{\n  \"servers\": {\n    \"supplemental-foodlaw\": {\n      \"type\": \"http\",\n      \"url\": \"https://mcp.supplemental.pl/mcp\"\n    }\n  }\n}\n"
  },
  "clientDocs": [
    {
      "label": "Claude — custom connectors",
      "href": "https://support.claude.com/en/articles/11175166-get-started-with-custom-connectors-using-remote-mcp"
    },
    {
      "label": "Claude Code — MCP",
      "href": "https://code.claude.com/docs/en/mcp"
    },
    {
      "label": "Cursor — Model Context Protocol",
      "href": "https://cursor.com/docs/mcp"
    },
    {
      "label": "ChatGPT — custom MCP servers",
      "href": "https://help.openai.com/en/articles/12584461"
    }
  ]
} as const;

export type McpLang = keyof typeof MCP_PAGE;
