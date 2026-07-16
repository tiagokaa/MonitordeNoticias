import requests
import pandas as pd

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote
from html import escape

# ======================================
# CONFIGURACOES
# ======================================

CATEGORY_KEYWORDS = {
    "Inteligência Artificial": [
        "inteligência artificial", "artificial intelligence", "IA generativa",
        "generative AI", "GenAI", "machine learning", "deep learning",
        "computer vision", "large language models", "LLM", "multimodal AI",
        "agentes de IA", "AI agents", "AI ethics", "IA responsável", "IA explicável"
    ],
    "Arte + IA": [
        "AI Art", "arte com IA", "arte generativa", "generative art",
        "arte algorítmica", "algorithmic art", "arte computacional", "arte digital",
        "digital art", "new media art", "media art", "creative AI",
        "AI artist", "artificial creativity", "criatividade computacional"
    ],
    "Imagem, vídeo, som": [
        "text-to-image", "image generation", "AI image", "AI video",
        "text-to-video", "video generation", "AI music", "AI audio",
        "voice cloning", "speech synthesis", "music generation", "Runway",
        "Midjourney", "Flux", "Stable Diffusion", "DALL-E"
    ],
    "XR, Imersão e Espaços Digitais": [
        "XR", "extended reality", "virtual reality", "VR", "augmented reality", "AR",
        "mixed reality", "spatial computing", "immersive art", "immersive experience",
        "metaverse", "digital twin", "volumetric capture"
    ],
    "NFTs, Blockchain e Web3": [
        "NFT", "crypto art", "blockchain art", "Web3", "on-chain art",
        "digital collectibles", "generative NFTs", "digital ownership", "tokenized art"
    ],
    "Museus, Exposições e Instituições": [
        "digital exhibition", "AI exhibition", "immersive exhibition",
        "new media exhibition", "museum technology", "museum innovation",
        "media art festival", "digital culture", "electronic art"
    ],
    "Pesquisa Científica": [
        "computational creativity", "human-AI collaboration", "AI and creativity",
        "creative technologies", "digital humanities", "human computer interaction",
        "HCI", "interactive art", "creative coding"
    ],
    "Educação": [
        "AI education", "creative education", "digital literacy",
        "media literacy", "STEAM", "arte e tecnologia", "educação digital"
    ],
    "Políticas Públicas e Regulação": [
        "AI regulation", "AI Act", "copyright AI", "ethical AI",
        "AI governance", "intellectual property AI"
    ],
    "Chamadas e Fomento": [
        "call for artists", "open call", "artist residency", "residência artística",
        "creative technology grant", "innovation grant", "research funding",
        "XR funding", "digital art award"
    ],
    "Empresas e Plataformas": [
        "OpenAI", "Anthropic", "Google DeepMind", "Adobe Firefly", "Runway",
        "Stability AI", "Midjourney", "Meta AI", "NVIDIA", "Unity", "Unreal Engine",
        "Epic Games", "Autodesk", "Blender", "Hugging Face"
    ],
    "Artistas": [
        "Refik Anadol", "Sougwen Chung", "Mario Klingemann", "Anna Ridler",
        "Memo Akten", "Ian Cheng", "Hito Steyerl", "teamLab"
    ],
    "Termos acadêmicos": [
        "creative technologies", "computational aesthetics", "post-digital", "postdigital",
        "human-machine collaboration", "human-AI collaboration", "algorithmic culture",
        "algorithmic aesthetics", "digital materiality", "technological mediation",
        "presence", "embodiment", "interactive systems", "creative computing"
    ],
    "Pesquisa em português": [
        "arte e tecnologia", "arte digital", "arte imersiva", "criatividade computacional",
        "inteligência artificial", "realidade estendida", "realidade virtual",
        "realidade aumentada", "experiência imersiva", "cultura digital",
        "arte generativa", "arte algorítmica", "instalação interativa"
    ],
    "Pesquisa em inglês": [
        "AI Art", "Generative Art", "Creative AI", "Digital Art", "Immersive Art",
        "Media Art", "Computational Creativity", "Interactive Art", "Extended Reality",
        "Creative Technology", "Human-AI Collaboration", "Artificial Creativity",
        "New Media Art", "Digital Culture", "Creative Coding", "Machine Creativity"
    ]
}

DIAS_RETROATIVOS = 360

GOOGLE_NEWS_LANGUAGE = "pt-BR"
BING_NEWS_LANGUAGE = "pt-BR"
TIMEZONE = ZoneInfo("America/Sao_Paulo")
DISPLAY_TIMEZONE = "UTC-3"

def unique_terms(values):

    seen = set()
    cleaned = []

    for value in values:
        term = value.strip()
        if not term:
            continue
        normalized = term.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(term)

    return cleaned

SEARCH_TERMS = []
for category, keywords in CATEGORY_KEYWORDS.items():
    for keyword in unique_terms(keywords):
        SEARCH_TERMS.append((category, keyword))

# ======================================
# COLETA DAS NOTICIAS
# ======================================

data_limite = datetime.now(TIMEZONE) - timedelta(days=DIAS_RETROATIVOS)
data_limite_ts = pd.Timestamp(data_limite)

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

def coletar_noticias_rss(category: str, keyword: str, fonte: str, rss_url: str) -> None:

    try:

        response = requests.get(rss_url, timeout=20)

        soup = BeautifulSoup(
            response.content,
            "xml"
        )

        for item in soup.find_all("item"):

            try:

                data_pub = (
                    pd.to_datetime(item.pubDate.text, utc=True)
                    .tz_convert(TIMEZONE)
                )

                if data_pub >= data_limite_ts:

                    titulo = item.title.text.strip()
                    if not noticia_corresponde_keyword(titulo, keyword):
                        continue

                    noticias.append({
                        "Categoria": category,
                        "Palavra-chave": keyword,
                        "Titulo": titulo,
                        "Data": data_pub,
                        "Link": item.link.text.strip()
                    })

            except:
                pass

    except Exception as erro:
        print(f"Erro em '{keyword}' [{category}] ({fonte}): {erro}")

for category, keyword in SEARCH_TERMS:

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

    coletar_noticias_rss(category, keyword, "Google News", google_rss_url)
    coletar_noticias_rss(category, keyword, "Bing News", bing_rss_url)

# ======================================
# DATAFRAME
# ======================================

df = pd.DataFrame(noticias)

if df.empty:
    print("Nenhuma noticia encontrada.")
    raise SystemExit()

df = df.drop_duplicates(subset=["Titulo", "Categoria", "Palavra-chave"])

df = df.sort_values(
    by="Data",
    ascending=False
)

# ======================================
# EXCEL
# ======================================

arquivo_excel = (
    f"Noticias_Arte_Digital_{datetime.now(TIMEZONE):%Y%m%d}.xlsx"
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

ultima_atualizacao = datetime.now(TIMEZONE).strftime(
    "%d/%m/%Y %H:%M:%S"
) + f" ({DISPLAY_TIMEZONE})"

cards_html = ""

for idx, (_, row) in enumerate(df.iterrows(), 1):

    titulo = escape(str(row["Titulo"]))
    categoria = escape(str(row["Categoria"]))
    keyword = escape(str(row["Palavra-chave"]))
    data = row["Data"].strftime("%d/%m/%Y %H:%M")
    link = escape(str(row["Link"]))

    cards_html += f"""
    <article class="card" data-category="{categoria}" data-keyword="{keyword}">

        <div class="card-header">
            <span class="card-number">#{idx}</span>
            <div class="card-tags">
                <span class="badge badge-category">{categoria}</span>
                <span class="badge badge-keyword">{keyword}</span>
            </div>
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
    <title>Monitor de Notícias de Arte Digital e IA</title>

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            background-color: #f3f5f7;
            background-image:
                radial-gradient(circle at 20% 20%, rgba(0, 170, 255, 0.16) 0 180px, transparent 181px),
                radial-gradient(circle at 80% 10%, rgba(123, 92, 255, 0.14) 0 220px, transparent 221px),
                linear-gradient(120deg, rgba(0, 0, 0, 0.04) 0%, rgba(0, 0, 0, 0) 45%),
                linear-gradient(rgba(24, 28, 39, 0.08) 1px, transparent 1px),
                linear-gradient(90deg, rgba(24, 28, 39, 0.08) 1px, transparent 1px);
            background-size: auto, auto, auto, 28px 28px, 28px 28px;
            background-attachment: fixed;
            min-height: 100vh;
            padding: 20px;
            color: #222;
        }}

        header {{
            max-width: 1200px;
            margin: 0 auto 40px;
            text-align: center;
            color: white;
            background: #202020;
            padding: 40px 20px;
            border-radius: 12px;
            border: 1px solid #343434;
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
            background: #ffffff;
            padding: 15px 25px;
            border-radius: 8px;
            font-size: 1.1rem;
            color: #222;
            border: 1px solid #d8d8d8;
        }}

        .stat strong {{
            display: block;
            font-size: 1.8rem;
            margin-top: 5px;
            color: #111;
        }}

        .search-container {{
            max-width: 1200px;
            margin: 0 auto 24px;
        }}

        .search-label {{
            display: block;
            color: #222;
            font-weight: 600;
            margin-bottom: 10px;
        }}

        .search-input {{
            width: 100%;
            padding: 14px 16px;
            border: 1px solid #c8c8c8;
            border-radius: 10px;
            background: #FFFFFF;
            font-size: 1rem;
            color: #222;
            outline: none;
            transition: box-shadow 0.2s, border-color 0.2s;
        }}

        .search-input:focus {{
            border-color: #777;
            box-shadow: 0 0 0 3px rgba(34, 34, 34, 0.15);
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
            border: 1px solid #d8d8d8;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}

        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.14);
        }}

        .card.is-hidden {{
            display: none;
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 10px;
        }}

        .card-tags {{
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 8px;
        }}

        .card-number {{
            font-weight: 700;
            color: #666;
            font-size: 0.9rem;
        }}

        .badge {{
            color: #fff;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            white-space: nowrap;
        }}

        .badge-category {{
            background: #333;
        }}

        .badge-keyword {{
            background: #666;
        }}

        .card-title-link {{
            text-decoration: none;
            color: inherit;
            cursor: pointer;
        }}

        .card-title {{
            font-size: 1.2rem;
            line-height: 1.4;
            color: #222;
            font-weight: 600;
            transition: all 0.2s;
        }}

        .card-title-link:hover .card-title {{
            color: #000;
        }}

        .card-meta {{
            display: flex;
            align-items: center;
            gap: 8px;
            color: #666;
            font-size: 0.95rem;
        }}

        .meta-icon {{
            font-size: 1.1rem;
        }}

        time {{
            font-weight: 500;
            color: #444;
        }}

        footer {{
            text-align: center;
            margin-top: 50px;
            color: #666;
            font-size: 0.95rem;
        }}

        .no-results {{
            max-width: 1200px;
            margin: 0 auto 24px;
            background: #e9e9e9;
            color: #222;
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
        <h1>📰 Monitor de Notícias de Arte Digital e IA</h1>
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
        <label class="search-label" for="news-search">Buscar notícias por categoria, palavra-chave ou título</label>
        <input id="news-search" class="search-input" type="search" placeholder="Digite para filtrar..." list="keyword-suggestions" autocomplete="off">
        <datalist id="keyword-suggestions"></datalist>
    </section>

    <p id="no-results-message" class="no-results" hidden>Nenhuma notícia encontrada.</p>

    <main>
        {cards_html}
    </main>

    <footer>
        <p>Monitor automático de arte digital e IA • Atualizado em {ultima_atualizacao}</p>
    </footer>

    <script>
        const searchInput = document.getElementById("news-search");
        const suggestionsList = document.getElementById("keyword-suggestions");
        const cards = Array.from(document.querySelectorAll("main .card"));
        const noResultsMessage = document.getElementById("no-results-message");
        const newsCount = document.getElementById("news-count");

        const normalizeText = (value) => value.toLocaleLowerCase("pt-BR");

        const suggestionMap = new Map();
        for (const card of cards) {{
            const terms = [
                card.dataset.keyword?.trim(),
                card.dataset.category?.trim()
            ];

            for (const term of terms) {{
                if (!term) {{
                    continue;
                }}

                const normalizedTerm = normalizeText(term);
                if (!suggestionMap.has(normalizedTerm)) {{
                    suggestionMap.set(normalizedTerm, term);
                }}
            }}
        }}

        Array
            .from(suggestionMap.values())
            .sort((a, b) => a.localeCompare(b, "pt-BR", {{ sensitivity: "base" }}))
            .forEach((term) => {{
                const option = document.createElement("option");
                option.value = term;
                suggestionsList.appendChild(option);
            }});

        const applyFilter = () => {{
            const filterText = normalizeText(searchInput.value.trim());
            let visibleCards = 0;

            for (const card of cards) {{
                const title = card.querySelector(".card-title")?.textContent ?? "";
                const keyword = card.dataset.keyword ?? "";
                const category = card.dataset.category ?? "";
                const searchableText = normalizeText(`${{title}} ${{keyword}} ${{category}}`);
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
