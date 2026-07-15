import requests
import pandas as pd

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from urllib.parse import quote
from html import escape

# ======================================
# CONFIGURACOES
# ======================================

KEYWORDS = [
    "calcario agricola",
    "cal agricola",
    "calcario",
    "corretivo de solo",
    "limestone",
    "agricultural lime",
    "Lhoist",
    "Ical",
    "\"Cal Cruzeiro\"",
    "Sibelco",
    "Brasical",
    "CMOC",
    "Mosaic",
    "Ureia",
    "Enxofre",
    "Sufur",
    "Biofragane",
    "Carmeuse"
]

DIAS_RETROATIVOS = 360

GOOGLE_NEWS_LANGUAGE = "pt-BR"
BING_NEWS_LANGUAGE = "pt-BR"

# ======================================
# COLETA DAS NOTICIAS
# ======================================

data_limite = datetime.now() - timedelta(days=DIAS_RETROATIVOS)

noticias = []

def montar_query_google(keyword: str) -> str:

    termo = keyword.strip()

    # Termos entre aspas devem ser buscados como frase exata.
    if termo.startswith("\"") and termo.endswith("\"") and len(termo) > 2:
        termo_limpo = termo[1:-1].strip()
        return f"\"{termo_limpo}\""

    return termo

def noticia_corresponde_keyword(titulo: str, keyword: str) -> bool:

    termo = keyword.strip()
    titulo_normalizado = titulo.casefold()

    # Para termos entre aspas, exigimos frase exata no titulo.
    if termo.startswith("\"") and termo.endswith("\"") and len(termo) > 2:
        termo_limpo = termo[1:-1].strip().casefold()
        return termo_limpo in titulo_normalizado

    return True

def coletar_noticias_rss(keyword: str, fonte: str, rss_url: str) -> None:

    try:

        response = requests.get(rss_url, timeout=20)

        soup = BeautifulSoup(
            response.content,
            "xml"
        )

        for item in soup.find_all("item"):

            try:

                data_pub = pd.to_datetime(
                    item.pubDate.text
                )

                if data_pub.tz_localize(None) >= data_limite:

                    titulo = item.title.text.strip()
                    if not noticia_corresponde_keyword(titulo, keyword):
                        continue

                    noticias.append({
                        "Palavra-chave": keyword,
                        "Titulo": titulo,
                        "Data": data_pub,
                        "Link": item.link.text.strip()
                    })

            except:
                pass

    except Exception as erro:
        print(f"Erro em '{keyword}' ({fonte}): {erro}")

for keyword in KEYWORDS:

    query = montar_query_google(keyword)

    google_rss_url = (
        f"https://news.google.com/rss/search?q={quote(query)}"
        f"&hl={GOOGLE_NEWS_LANGUAGE}"
    )

    bing_rss_url = (
        f"https://www.bing.com/news/search?q={quote(query)}"
        "&format=rss"
        f"&setlang={BING_NEWS_LANGUAGE.lower()}"
        f"&mkt={BING_NEWS_LANGUAGE}"
    )

    coletar_noticias_rss(keyword, "Google News", google_rss_url)
    coletar_noticias_rss(keyword, "Bing News", bing_rss_url)

# ======================================
# DATAFRAME
# ======================================

df = pd.DataFrame(noticias)

if df.empty:
    print("Nenhuma noticia encontrada.")
    raise SystemExit()

df = df.drop_duplicates(
    subset=["Titulo"]
)

df = df.sort_values(
    by="Data",
    ascending=False
)

# ======================================
# EXCEL
# ======================================

arquivo_excel = (
    f"Noticias_Calcario_{datetime.now():%Y%m%d}.xlsx"
)

df_excel = df.copy()

df_excel["Data"] = (
    df_excel["Data"]
    .dt.strftime("%d/%m/%Y %H:%M")
)

df_excel.to_excel(
    arquivo_excel,
    index=False
)

# ======================================
# HTML5 COM DESIGN MODERNO
# ======================================

ultima_atualizacao = datetime.now().strftime(
    "%d/%m/%Y %H:%M:%S"
)

cards_html = ""

for idx, (_, row) in enumerate(df.iterrows(), 1):

    titulo = escape(str(row["Titulo"]))
    keyword = escape(str(row["Palavra-chave"]))
    data = row["Data"].strftime("%d/%m/%Y %H:%M")
    link = escape(str(row["Link"]))

    cards_html += f"""
    <article class="card">

        <div class="card-header">
            <span class="card-number">#{idx}</span>
            <span class="badge">{keyword}</span>
        </div>

        <a href="{link}" target="_blank" rel="noopener noreferrer" class="card-title-link" title="Abrir noticia">
            <h3 class="card-title">{titulo}</h3>
        </a>

        <div class="card-meta">
            <span class="meta-icon">📅</span>
            <time>{data}</time>
        </div>

    </article>
    """

html = f"""
<!DOCTYPE html>

<html lang="pt-BR">

<head>

    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor de Noticias de Calcario</title>

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            background-color: #EFF4F9;
            background-image:
                linear-gradient(rgba(239, 244, 249, 0.68), rgba(214, 227, 239, 0.68)),
                url("https://raw.githubusercontent.com/tiagokaa/MonitordeNoticias/main/BACKDROP.jpg");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
            min-height: 100vh;
            padding: 20px;
            color: #323E48;
        }}

        header {{
            max-width: 1200px;
            margin: 0 auto 40px;
            text-align: center;
            color: white;
            background: linear-gradient(135deg, #10497C 0%, #0067B3 100%);
            padding: 40px 20px;
            border-radius: 12px;
            border: 1px solid #248DC1;
        }}

        header h1 {{
            font-size: 2.5rem;
            margin-bottom: 15px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
        }}

        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            flex-wrap: wrap;
            margin-top: 20px;
        }}

        .stat {{
            background: #EFF4F9;
            padding: 15px 25px;
            border-radius: 8px;
            font-size: 1.1rem;
            color: #1C2325;
            border: 1px solid #CFD2D3;
        }}

        .stat strong {{
            display: block;
            font-size: 1.8rem;
            margin-top: 5px;
            color: #10497C;
        }}

        .search-container {{
            max-width: 1200px;
            margin: 0 auto 24px;
        }}

        .search-label {{
            display: block;
            color: #10497C;
            font-weight: 600;
            margin-bottom: 10px;
        }}

        .search-input {{
            width: 100%;
            padding: 14px 16px;
            border: 1px solid #A2A9AD;
            border-radius: 10px;
            background: #FFFFFF;
            font-size: 1rem;
            color: #323E48;
            outline: none;
            transition: box-shadow 0.2s, border-color 0.2s;
        }}

        .search-input:focus {{
            border-color: #248DC1;
            box-shadow: 0 0 0 3px rgba(36, 141, 193, 0.22);
        }}

        main {{
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }}

        .card {{
            background: #FFFFFF;
            border-radius: 12px;
            padding: 24px;
            border: 1px solid #CFD2D3;
            box-shadow: 0 8px 24px rgba(16, 73, 124, 0.12);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}

        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 28px rgba(16, 73, 124, 0.2);
        }}

        .card.is-hidden {{
            display: none;
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
        }}

        .card-number {{
            font-weight: 700;
            color: #0067B3;
            font-size: 0.9rem;
        }}

        .badge {{
            background: linear-gradient(135deg, #0098A7 0%, #248DC1 100%);
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            white-space: nowrap;
        }}

        .card-title-link {{
            text-decoration: none;
            color: inherit;
            cursor: pointer;
        }}

        .card-title {{
            font-size: 1.2rem;
            line-height: 1.4;
            color: #323E48;
            font-weight: 600;
            transition: all 0.2s;
        }}

        .card-title-link:hover .card-title {{
            color: #F58220;
        }}

        .card-meta {{
            display: flex;
            align-items: center;
            gap: 8px;
            color: #5F6B6D;
            font-size: 0.95rem;
        }}

        .meta-icon {{
            font-size: 1.1rem;
        }}

        time {{
            font-weight: 500;
            color: #10497C;
        }}

        footer {{
            text-align: center;
            margin-top: 50px;
            color: #5F6B6D;
            font-size: 0.95rem;
        }}

        .no-results {{
            max-width: 1200px;
            margin: 0 auto 24px;
            background: #F58220;
            color: #FFFFFF;
            text-align: center;
            font-weight: 600;
            border-radius: 10px;
            padding: 14px 16px;
        }}

        @media (max-width: 768px) {{
            header h1 {{
                font-size: 1.8rem;
            }}

            main {{
                grid-template-columns: 1fr;
            }}

            .stats {{
                flex-direction: column;
                gap: 15px;
            }}
        }}
    </style>

</head>

<body>

    <header>
        <h1>📰 Monitor de Noticias de Calcario</h1>
        <div class="stats">
            <div class="stat">
                Noticias encontradas
                <strong id="news-count">{len(df)}</strong>
            </div>
            <div class="stat">
                Ultima atualizacao
                <strong>{ultima_atualizacao}</strong>
            </div>
        </div>
    </header>

    <section class="search-container" aria-label="Filtro de noticias">
        <label class="search-label" for="news-search">Buscar noticias por palavra-chave ou titulo</label>
        <input id="news-search" class="search-input" type="search" placeholder="Digite para filtrar..." list="keyword-suggestions" autocomplete="off">
        <datalist id="keyword-suggestions"></datalist>
    </section>

    <p id="no-results-message" class="no-results" hidden>Nenhuma notícia encontrada.</p>

    <main>
        {cards_html}
    </main>

    <footer>
        <p>Monitor de noticias automatico • Atualizado em {ultima_atualizacao}</p>
    </footer>

    <script>
        const searchInput = document.getElementById("news-search");
        const suggestionsList = document.getElementById("keyword-suggestions");
        const cards = Array.from(document.querySelectorAll("main .card"));
        const noResultsMessage = document.getElementById("no-results-message");
        const newsCount = document.getElementById("news-count");

        const normalizeText = (value) => value.toLocaleLowerCase("pt-BR");

        const keywordMap = new Map();
        for (const card of cards) {{
            const keywordText = card.querySelector(".badge")?.textContent?.trim();
            if (!keywordText) {{
                continue;
            }}

            const normalizedKeyword = normalizeText(keywordText);
            if (!keywordMap.has(normalizedKeyword)) {{
                keywordMap.set(normalizedKeyword, keywordText);
            }}
        }}

        Array
            .from(keywordMap.values())
            .sort((a, b) => a.localeCompare(b, "pt-BR", {{ sensitivity: "base" }}))
            .forEach((keyword) => {{
                const option = document.createElement("option");
                option.value = keyword;
                suggestionsList.appendChild(option);
            }});

        const applyFilter = () => {{
            const filterText = normalizeText(searchInput.value.trim());
            let visibleCards = 0;

            for (const card of cards) {{
                const title = card.querySelector(".card-title")?.textContent ?? "";
                const keyword = card.querySelector(".badge")?.textContent ?? "";
                const searchableText = normalizeText(`${{title}} ${{keyword}}`);
                const isMatch = !filterText || searchableText.includes(filterText);

                card.classList.toggle("is-hidden", !isMatch);
                if (isMatch) {{
                    visibleCards += 1;
                }}
            }}

            newsCount.textContent = String(visibleCards);
            noResultsMessage.hidden = visibleCards > 0;
        }};

        searchInput.addEventListener("input", applyFilter);
    </script>

</body>

</html>
"""

arquivo_html = "index.html"

with open(
    arquivo_html,
    "w",
    encoding="utf-8"
) as f:

    f.write(html)

print(f"Sucesso! Excel gerado: {arquivo_excel}")
print(f"Sucesso! HTML gerado : {arquivo_html}")
print(f"Sucesso! Noticias encontradas: {len(df)}")
