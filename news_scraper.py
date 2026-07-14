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
    "Cal Cruzeiro",
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

# ======================================
# COLETA DAS NOTICIAS
# ======================================

data_limite = datetime.now() - timedelta(days=DIAS_RETROATIVOS)

noticias = []

for keyword in KEYWORDS:

    rss_url = (
        f"https://news.google.com/rss/search?q={quote(keyword)}"
        "&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    )

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

                    noticias.append({
                        "Palavra-chave": keyword,
                        "Titulo": item.title.text.strip(),
                        "Data": data_pub,
                        "Link": item.link.text.strip()
                    })

            except:
                pass

    except Exception as erro:
        print(f"Erro em '{keyword}': {erro}")

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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}

        header {{
            max-width: 1200px;
            margin: 0 auto 40px;
            text-align: center;
            color: white;
            background: rgba(0, 0, 0, 0.1);
            padding: 40px 20px;
            border-radius: 12px;
            backdrop-filter: blur(10px);
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
            background: rgba(255, 255, 255, 0.2);
            padding: 15px 25px;
            border-radius: 8px;
            font-size: 1.1rem;
            backdrop-filter: blur(10px);
        }}

        .stat strong {{
            display: block;
            font-size: 1.8rem;
            margin-top: 5px;
        }}

        main {{
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }}

        .card {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            display: flex;
            flex-direction: column;
            gap: 15px;
        }}

        .card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
        }}

        .card-number {{
            font-weight: 700;
            color: #667eea;
            font-size: 0.9rem;
        }}

        .badge {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
            color: #1a1a1a;
            font-weight: 600;
            transition: all 0.2s;
        }}

        .card-title-link:hover .card-title {{
            color: #667eea;
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
            color: #764ba2;
        }}

        footer {{
            text-align: center;
            margin-top: 50px;
            color: rgba(255, 255, 255, 0.7);
            font-size: 0.95rem;
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
                <strong>{len(df)}</strong>
            </div>
            <div class="stat">
                Ultima atualizacao
                <strong>{ultima_atualizacao}</strong>
            </div>
        </div>
    </header>

    <main>
        {cards_html}
    </main>

    <footer>
        <p>Monitor de noticias automatico • Atualizado em {ultima_atualizacao}</p>
    </footer>

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
