
import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path
from datetime import datetime, timezone

BASE = "https://rsshub.app/lrepacks"
CATEGORIAS = [
    "",
    "novye-repaki-elchupacabra",
    "repaki-sistemnyh-programm",
    "repaki-programm-dlya-grafiki",
    "repaki-programm-dlya-interneta",
    "repaki-multimedia-programm",
    "repaki-programm-dlya-ofisa",
    "repaki-raznyh-programm",
    "sistemnye-biblioteki",
]

def nome_tag(elemento):
    return elemento.tag.split("}")[-1].lower()

def texto(elemento, nomes):
    for filho in elemento.iter():
        if nome_tag(filho) in nomes and filho.text:
            return filho.text.strip()
    return ""

def extrair_imagem(item):
    # Primeiro tenta imagens fornecidas como mídia/enclosure no feed.
    for filho in item.iter():
        tag = nome_tag(filho)
        if tag in ("thumbnail", "content", "enclosure"):
            url = filho.attrib.get("url") or filho.attrib.get("href")
            tipo = filho.attrib.get("type", "")
            if url and (tipo.startswith("image/") or tag == "thumbnail"):
                return url

    # Depois procura uma imagem dentro do HTML da descrição.
    html = texto(item, {"content", "summary", "description"})
    padrao = r'<img[^>]+(?:src|data-src)=["\']([^"\']+)'
    resultado = re.search(padrao, html, re.IGNORECASE)
    if resultado:
        return unescape(resultado.group(1))

    return ""

def baixar_feed(categoria):
    caminho = f"/{categoria}" if categoria else ""
    url = BASE + caminho + "?format=atom&limit=20"
    pedido = urllib.request.Request(
        url,
        headers={"User-Agent": "ReliquiasDoGil/1.0"}
    )
    with urllib.request.urlopen(pedido, timeout=35) as resposta:
        return ET.fromstring(resposta.read())

def processar_feed(raiz):
    itens = []
    for item in raiz.iter():
        if nome_tag(item) not in ("entry", "item"):
            continue

        titulo = texto(item, {"title"})
        link = ""

        for filho in item:
            if nome_tag(filho) == "link":
                rel = filho.attrib.get("rel", "alternate")
                if rel == "alternate" or not link:
                    link = filho.attrib.get("href") or filho.text or ""

        if not link:
            link = texto(item, {"guid"})

        if not titulo or not link.startswith("https://lrepacks.net/"):
            continue

        resumo = texto(item, {"summary", "description"})
        resumo = re.sub(r"<[^>]+>", " ", resumo)
        resumo = unescape(re.sub(r"\s+", " ", resumo)).strip()
        resumo = resumo[:260]

        data = texto(item, {"published", "updated", "pubdate"})
        imagem = extrair_imagem(item)

        itens.append({
            "title": titulo,
            "link": link,
            "description": resumo,
            "image": imagem,
            "date": data
        })

    return itens

def main():
    catalogo = {}
    feeds_ok = 0

    for categoria in CATEGORIAS:
        try:
            raiz = baixar_feed(categoria)
            itens = processar_feed(raiz)
            feeds_ok += 1

            for item in itens:
                # A URL é a chave para evitar publicações duplicadas.
                catalogo[item["link"]] = item

            print(f"OK: {categoria or 'página inicial'} - {len(itens)} itens")
        except Exception as erro:
            print(f"Falha na categoria {categoria or 'inicial'}: {erro}")
        time.sleep(1)

    if feeds_ok == 0:
        raise RuntimeError("Nenhum feed foi consultado. Catálogo antigo preservado.")

    resultado = list(catalogo.values())
    resultado.sort(key=lambda x: x.get("date", ""), reverse=True)

    destino = Path("catalogo.json")
    destino.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"Catálogo salvo com {len(resultado)} publicações.")
    print("Atualizado em:", datetime.now(timezone.utc).isoformat())

if __name__ == "__main__":
    main()
