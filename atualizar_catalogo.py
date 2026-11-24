import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

ARQUIVO_SAIDA = "catalogo.json"

# Adicione aqui feeds RSS oficiais de programas gratuitos ou lançamentos do GitHub
FEEDS_PROGRAMAS = [
    "https://github.com",
    "https://github.com",
    "https://github.com"
]

# Adicione aqui feeds RSS de jogos gratuitos ou plataformas indie (ex: itch.io)
FEEDS_JOGOS = [
    "https://itch.io"
]

def ler_feed_rss(url, categoria_padrao, limite=6):
    itens = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ReliquiasDoGilBot/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_dados = resp.read()
        raiz = ET.fromstring(xml_dados)

        # Suporte para RSS 2.0 (<item>) e Atom/GitHub (<entry>)
        entradas = raiz.findall(".//item") or raiz.findall(".//{http://w3.org}entry")

        for entrada in entradas[:limite]:
            titulo = (
                entrada.findtext("title")
                or entrada.findtext("{http://w3.org}title")
                or "Sem título"
            ).strip()

            link_el = entrada.find("link")
            if link_el is not None and link_el.text:
                link = link_el.text.strip()
            else:
                atom_link = entrada.find("{http://w3.org}link")
                link = atom_link.attrib.get("href", "") if atom_link is not None else ""

            descricao = (
                entrada.findtext("description")
                or entrada.findtext("{http://w3.org}summary")
                or "Clique no botão abaixo para acessar a página oficial de download."
            ).strip()

            # Remove tags HTML básicas da descrição e limita o tamanho
            texto_limpo = "".join(ET.fromstring(f"<r>{descricao}</r>").itertext()) if "<" in descricao else descricao
            texto_limpo = (texto_limpo[:140] + "...") if len(texto_limpo) > 140 else texto_limpo

            data_pub = (
                entrada.findtext("pubDate")
                or entrada.findtext("{http://w3.org}updated")
                or datetime.now().strftime("%Y-%m-%d")
            )[:10]

            itens.append({
                "title": titulo,
                "description": texto_limpo or "Acesse a página oficial para mais detalhes.",
                "link": link,
                "image": "",
                "tag": categoria_padrao,
                "date": data_pub
            })
    except Exception as erro:
        print(f"Aviso ao ler {url}: {erro}")
    return itens

def carregar_existente():
    try:
        with open(ARQUIVO_SAIDA, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"programas": [], "jogos": [], "achadinhos": []}

def main():
    atual = carregar_existente()

    novos_programas = []
    for feed in FEEDS_PROGRAMAS:
        novos_programas.extend(ler_feed_rss(feed, "Programa Oficial", limite=4))

    novos_jogos = []
    for feed in FEEDS_JOGOS:
        novos_jogos.extend(ler_feed_rss(feed, "Jogo Gratuito", limite=8))

    catalogo = {
        "atualizado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "programas": novos_programas if novos_programas else atual.get("programas", []),
        "jogos": novos_jogos if novos_jogos else atual.get("jogos", []),
        # Mantém seus achadinhos cadastrados manualmente intactos
        "achadinhos": atual.get("achadinhos", [])
    }

    with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
        json.dump(catalogo, f, ensure_ascii=False, indent=2)

    print("Catálogo atualizado com sucesso!")

if __name__ == "__main__":
    main()
