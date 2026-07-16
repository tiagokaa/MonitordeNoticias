# 📰 Monitor de Notícias de Arte Digital e IA

Este projeto coleta notícias automaticamente (Google News RSS + Bing News RSS) sobre arte digital, inteligência artificial e temas relacionados, e publica uma página web com os resultados organizados para leitura rápida.

## O que o site faz

- Busca notícias por um conjunto amplo de termos dividido por categorias (IA, Arte + IA, XR, Web3, Museus, Educação, Regulação, Empresas, Artistas, etc.).
- Exibe os resultados em cards com:
  - categoria,
  - palavra-chave usada na busca,
  - título da notícia,
  - data de publicação,
  - link para a fonte.
- Oferece filtro instantâneo com autocomplete por categoria, palavra-chave e título.
- Atualiza o contador de notícias exibidas em tempo real.

## Atualização automática

O workflow do GitHub Actions executa o scraper várias vezes ao dia e atualiza:

- `index.html` (site publicado)

## Arquivos principais

- `news_scraper.py`: coleta, consolida e gera o HTML.
- `index.html`: página final publicada.
- `.github/workflows/update-news.yml`: agenda e automação de atualização.
