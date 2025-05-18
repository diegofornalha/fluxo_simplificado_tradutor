#!/usr/bin/env python3
"""
Script principal para execução do pipeline de blog
Implementa o fluxo completo sem depender de chaves da OpenAI
"""

import os
import json
import logging
import feedparser
import uuid
import re
import unicodedata
from datetime import datetime
from pathlib import Path
import requests
import shutil
import time
import argparse
from urllib.parse import quote

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("pipeline")

# Definir diretórios
SCRIPT_DIR = Path(__file__).parent
FEEDS_FILE = SCRIPT_DIR / "feeds.json"
POSTS_PARA_TRADUZIR_DIR = SCRIPT_DIR / "posts_para_traduzir"
POSTS_TRADUZIDOS_DIR = SCRIPT_DIR / "posts_traduzidos"
POSTS_FORMATADOS_DIR = SCRIPT_DIR / "posts_formatados"
POSTS_PUBLICADOS_DIR = SCRIPT_DIR / "posts_publicados"

# Criar diretórios se não existirem
POSTS_PARA_TRADUZIR_DIR.mkdir(exist_ok=True)
POSTS_TRADUZIDOS_DIR.mkdir(exist_ok=True)
POSTS_FORMATADOS_DIR.mkdir(exist_ok=True)
POSTS_PUBLICADOS_DIR.mkdir(exist_ok=True)

# Função para obter artigos já publicados no Sanity
def obter_artigos_publicados():
    """Obtém lista de títulos de artigos já publicados no Sanity"""
    try:
        # Obter token do Sanity
        sanity_token = os.environ.get("SANITY_API_TOKEN")
        if not sanity_token:
            logger.warning("Token do Sanity não encontrado, não será possível verificar artigos já publicados")
            return set()
        
        # Configurações do Sanity
        project_id = os.environ.get("SANITY_PROJECT_ID", "brby2yrg")
        dataset = "production"
        api_version = "2023-05-03"
        
        # Query para obter apenas títulos dos posts
        query = '*[_type == "post"]{ title }'
        encoded_query = quote(query)
        
        # URL da API do Sanity
        url = f"https://{project_id}.api.sanity.io/v{api_version}/data/query/{dataset}?query={encoded_query}"
        
        # Headers
        headers = {
            "Authorization": f"Bearer {sanity_token}"
        }
        
        # Fazer a requisição
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Extrair títulos
        result = response.json().get("result", [])
        published_titles = set()
        
        for doc in result:
            if doc.get("title"):
                published_titles.add(doc["title"].lower())
        
        logger.info(f"Encontrados {len(published_titles)} artigos já publicados no Sanity")
        return published_titles
        
    except Exception as e:
        logger.error(f"Erro ao obter artigos publicados: {str(e)}")
        return set()

# 1. MONITORAR: Ler feeds RSS
def monitorar_feeds(max_articles=3):
    """Lê os feeds RSS e seleciona artigos relevantes"""
    logger.info("1. MONITORANDO FEEDS RSS...")
    
    # Carregar configuração de feeds
    try:
        with open(FEEDS_FILE, "r") as f:
            feeds_config = json.load(f)
    except Exception as e:
        logger.error(f"Erro ao carregar feeds: {str(e)}")
        return []
    
    results = []
    processed_titles = set()  # Para evitar duplicatas por título
    processed_urls = set()    # Para evitar duplicatas por URL
    
    # Obter a lista de palavras na blacklist
    blacklist_keywords = feeds_config.get("settings", {}).get("blacklist_keywords", [])
    logger.info(f"Palavras na blacklist: {blacklist_keywords}")
    
    # Obter lista de artigos já publicados no Sanity
    published_titles = obter_artigos_publicados()
    logger.info(f"Artigos já publicados no Sanity: {len(published_titles)}")
    
    # Processar cada feed
    feeds_list = feeds_config.get("feeds", [])
    for feed in feeds_list:
        try:
            logger.info(f"Lendo feed: {feed['name']} ({feed['url']})")
            parsed_feed = feedparser.parse(feed["url"])
            
            # Verificar se o feed foi parseado corretamente
            if not hasattr(parsed_feed, "entries"):
                logger.warning(f"Feed sem entradas: {feed['name']}")
                continue
            
            articles_processed = 0
            articles_skipped = 0
                
            # Processar os últimos N artigos do feed
            for i, entry in enumerate(parsed_feed.entries):
                if articles_processed >= max_articles:
                    break
                
                # Extrair título e link para verificação de duplicatas
                title = entry.get("title", "")
                link = entry.get("link", "")
                
                # Verificar se o artigo já foi publicado no Sanity
                if title.lower() in published_titles:
                    logger.warning(f"Artigo já publicado no Sanity ignorado: {title}")
                    articles_skipped += 1
                    continue
                
                # Verificar se o artigo já foi processado (duplicata na sessão atual)
                if title.lower() in processed_titles or link in processed_urls:
                    logger.warning(f"Artigo duplicado ignorado: {title}")
                    articles_skipped += 1
                    continue
                
                # Verificar se o artigo contém alguma palavra da blacklist no título
                should_skip = False
                for keyword in blacklist_keywords:
                    if keyword.lower() in title.lower():
                        logger.warning(f"Artigo com palavra na blacklist ignorado: {title} (palavra: {keyword})")
                        articles_skipped += 1
                        should_skip = True
                        break
                
                if should_skip:
                    continue
                
                # Extrair conteúdo do artigo
                content = ""
                if "content" in entry and entry.content:
                    for content_item in entry.content:
                        if content_item.get("type") == "text/html":
                            content += content_item.get("value", "")
                elif "summary" in entry:
                    content = entry.summary
                
                # Também verificar conteúdo para palavras na blacklist
                for keyword in blacklist_keywords:
                    if keyword.lower() in content.lower():
                        logger.warning(f"Artigo com palavra na blacklist no conteúdo ignorado: {title} (palavra: {keyword})")
                        articles_skipped += 1
                        should_skip = True
                        break
                
                if should_skip:
                    continue
                
                article = {
                    "title": title,
                    "link": link,
                    "summary": entry.get("summary", ""),
                    "content": content,
                    "published": entry.get("published", ""),
                    "source": feed["name"],
                    "tags": [tag.get("term", "") for tag in entry.get("tags", [])] if hasattr(entry, "tags") else [],
                    "processed_date": datetime.now().isoformat()
                }
                
                # Salvar o artigo para tradução
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                filename = f"para_traduzir_{timestamp}_{articles_processed}.json"
                filepath = POSTS_PARA_TRADUZIR_DIR / filename
                
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(article, f, ensure_ascii=False, indent=2)
                    
                logger.info(f"Artigo salvo: {filepath}")
                
                # Adicionar aos conjuntos de artigos processados
                processed_titles.add(title.lower())
                processed_urls.add(link)
                
                results.append(filepath)
                articles_processed += 1
                
            logger.info(f"Feed {feed['name']} processado com sucesso: {articles_processed} artigos aceitos, {articles_skipped} artigos ignorados")
            
        except Exception as e:
            logger.error(f"Erro ao processar feed {feed['name']}: {str(e)}")
    
    logger.info(f"Total de artigos selecionados: {len(results)}")
    return results

# Função para remover links HTML de um texto
def remover_links_html(texto):
    """Remove todos os links HTML (<a> tags) de um texto"""
    # Padrão para capturar tags <a> completas com seu conteúdo
    return re.sub(r'<a\s+[^>]*>(.*?)</a>', r'\1', texto)

def remover_todas_tags_html(texto):
    """Remove todas as tags HTML de um texto"""
    # Primeiro remove links HTML (para preservar o texto dentro deles)
    texto = remover_links_html(texto)
    # Depois remove todas as outras tags HTML
    return re.sub(r'<[^>]*>', '', texto)

# 2. TRADUZIR: Usar nosso módulo de tradução com deep-translator
def traduzir_artigos(arquivos):
    """Traduz artigos usando a API do deep-translator"""
    logger.info("2. TRADUZINDO ARTIGOS...")
    
    # Importar nosso módulo de tradução
    from tools.translator import translate_article, clean_html
    
    resultados = []
    
    for arquivo in arquivos:
        try:
            arquivo_path = Path(arquivo)
            if not arquivo_path.exists():
                logger.warning(f"Arquivo não encontrado: {arquivo}")
                continue
                
            # Ler o conteúdo do arquivo
            with open(arquivo_path, "r", encoding="utf-8") as f:
                artigo = json.load(f)
            
            # Usar nosso módulo de tradução para traduzir o artigo completo
            logger.info(f"Iniciando tradução do artigo: {artigo['title']}")
            
            # Traduzir o artigo usando nossa função de tradução de alta qualidade
            traduzido = translate_article(artigo)
            
            # Adicionar metadados extras
            traduzido["translated_date"] = datetime.now().isoformat()
            
            # Gerar nome do arquivo traduzido
            nome_arquivo = arquivo_path.name
            nome_traduzido = f"traduzido_{nome_arquivo.replace('para_traduzir_', '')}"
            arquivo_traduzido = POSTS_TRADUZIDOS_DIR / nome_traduzido
            
            # Salvar o artigo traduzido
            with open(arquivo_traduzido, "w", encoding="utf-8") as f:
                json.dump(traduzido, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Artigo traduzido salvo: {arquivo_traduzido}")
            resultados.append(arquivo_traduzido)
            
        except Exception as e:
            logger.error(f"Erro ao traduzir artigo {arquivo}: {str(e)}")
    
    logger.info(f"Total de artigos traduzidos: {len(resultados)}")
    return resultados

# 3. FORMATAR: Preparar artigos para o Sanity CMS
def criar_slug(titulo):
    """Cria um slug a partir de um título"""
    # Normalizar para remover acentos
    slug = titulo.lower()
    # Remover caracteres especiais
    slug = unicodedata.normalize('NFKD', slug)
    slug = ''.join([c for c in slug if not unicodedata.combining(c)])
    # Substituir espaços por traços
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    return slug.strip('-')

def gerar_chave():
    """Gera uma chave aleatória para o Sanity"""
    return str(uuid.uuid4())[:8]

def texto_para_portable_text(texto):
    """Converte texto em formato Portable Text do Sanity"""
    # Remover todas as tags HTML do texto
    texto = remover_todas_tags_html(texto)
    
    # Dividir o texto em parágrafos
    paragrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
    
    # Criar blocos no formato do Sanity
    blocos = []
    for paragrafo in paragrafos:
        bloco = {
            "_type": "block",
            "_key": gerar_chave(),
            "style": "normal",
            "markDefs": [],
            "children": [
                {
                    "_type": "span",
                    "_key": gerar_chave(),
                    "text": paragrafo,
                    "marks": []
                }
            ]
        }
        blocos.append(bloco)
    
    return blocos

def formatar_artigos(arquivos):
    """Formata artigos para o formato do Sanity CMS"""
    logger.info("3. FORMATANDO ARTIGOS PARA O SANITY...")
    
    resultados = []
    
    for arquivo in arquivos:
        try:
            arquivo_path = Path(arquivo)
            if not arquivo_path.exists():
                logger.warning(f"Arquivo não encontrado: {arquivo}")
                continue
                
            # Ler o conteúdo do arquivo
            with open(arquivo_path, "r", encoding="utf-8") as f:
                artigo = json.load(f)
            
            # Criar slug a partir do título
            titulo = artigo['title']
            slug = criar_slug(titulo)
            
            # Converter conteúdo para formato Portable Text
            content_blocks = texto_para_portable_text(artigo['content'])
            
            # Limitar o resumo a 299 caracteres e remover todas as tags HTML
            resumo = artigo.get('summary', '')
            
            # Remover todas as tags HTML (incluindo <strong>, <em>, etc.)
            resumo = remover_todas_tags_html(resumo)
            
            # Limitar tamanho a 299 caracteres
            if len(resumo) > 299:
                resumo = resumo[:296] + '...'
                
            # Criar objeto formatado para o Sanity
            formatado = {
                "_type": "post",
                "title": titulo,
                "slug": {
                    "_type": "slug",
                    "current": slug
                },
                "publishedAt": datetime.now().isoformat(),
                "excerpt": resumo,
                "content": content_blocks,
                # Garantir que o título original seja traduzido, não mantido em inglês
                "originalSource": {
                    "url": artigo.get('link', ''),
                    "title": titulo,
                    "site": artigo.get('source', 'Desconhecido')
                }
            }
            
            # Gerar nome do arquivo formatado
            nome_arquivo = arquivo_path.name
            nome_formatado = f"formatado_{nome_arquivo.replace('traduzido_', '')}"
            arquivo_formatado = POSTS_FORMATADOS_DIR / nome_formatado
            
            # Salvar o artigo formatado
            with open(arquivo_formatado, "w", encoding="utf-8") as f:
                json.dump(formatado, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Artigo formatado salvo: {arquivo_formatado}")
            resultados.append(arquivo_formatado)
            
        except Exception as e:
            logger.error(f"Erro ao formatar artigo {arquivo}: {str(e)}")
    
    logger.info(f"Total de artigos formatados: {len(resultados)}")
    return resultados

# 4. PUBLICAR: Enviar artigos para o Sanity CMS
def publicar_artigos(arquivos):
    """Publica artigos no Sanity CMS"""
    logger.info("4. PUBLICANDO ARTIGOS NO SANITY...")
    
    resultados = {
        "published_files": [],
        "success_count": 0,
        "failed_count": 0,
        "failed_files": []
    }
    
    # Obter token do Sanity
    sanity_api_token = os.environ.get("SANITY_API_TOKEN")
    if not sanity_api_token:
        logger.error("Token do Sanity não encontrado no ambiente")
        return resultados
    
    # Configurações do Sanity
    project_id = os.environ.get("SANITY_PROJECT_ID", "brby2yrg")
    dataset = "production"
    api_version = "2023-05-03"
    
    # URL da API do Sanity
    url = f"https://{project_id}.api.sanity.io/v{api_version}/data/mutate/{dataset}"
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {sanity_api_token}"
    }
    
    for arquivo in arquivos:
        try:
            arquivo_path = Path(arquivo)
            if not arquivo_path.exists():
                logger.warning(f"Arquivo não encontrado: {arquivo}")
                resultados["failed_count"] += 1
                resultados["failed_files"].append({
                    "file": str(arquivo),
                    "error": "Arquivo não encontrado"
                })
                continue
                
            # Ler o conteúdo do arquivo
            with open(arquivo_path, "r", encoding="utf-8") as f:
                post_data = json.load(f)
            
            # Preparar a mutação
            mutations = {
                "mutations": [
                    {
                        "create": post_data
                    }
                ]
            }
            
            logger.info(f"Enviando post '{post_data.get('title')}' para o Sanity")
            
            # Enviar a requisição
            response = requests.post(url, headers=headers, json=mutations, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Post publicado com sucesso: {post_data.get('title')}")
                
                # Mover o arquivo para a pasta de publicados
                nome_arquivo = arquivo_path.name
                nome_publicado = f"publicado_{nome_arquivo.replace('formatado_', '')}"
                arquivo_publicado = POSTS_PUBLICADOS_DIR / nome_publicado
                
                # Copiar o arquivo
                shutil.copy2(arquivo_path, arquivo_publicado)
                logger.info(f"Arquivo movido para: {arquivo_publicado}")
                
                resultados["published_files"].append(str(arquivo_publicado))
                resultados["success_count"] += 1
            else:
                logger.error(f"Erro ao publicar post: {response.status_code} - {response.text}")
                resultados["failed_count"] += 1
                resultados["failed_files"].append({
                    "file": str(arquivo),
                    "error": f"Erro HTTP {response.status_code}: {response.text}"
                })
                
        except Exception as e:
            logger.error(f"Erro ao publicar artigo {arquivo}: {str(e)}")
            resultados["failed_count"] += 1
            resultados["failed_files"].append({
                "file": str(arquivo),
                "error": str(e)
            })
    
    logger.info(f"Total de artigos publicados com sucesso: {resultados['success_count']}")
    logger.info(f"Total de falhas na publicação: {resultados['failed_count']}")
    
    return resultados

# 5. SINCRONIZAR: Enviar artigos publicados ao Algolia
def sincronizar_com_algolia(arquivos_publicados):
    """Sincroniza artigos publicados com o Algolia"""
    logger.info("5. SINCRONIZANDO COM ALGOLIA...")
    
    # Verificar credenciais do Algolia
    app_id = os.environ.get('ALGOLIA_APP_ID', '42TZWHW8UP')
    api_key = os.environ.get('ALGOLIA_ADMIN_API_KEY')
    index_name = os.environ.get('ALGOLIA_INDEX_NAME', 'development_mcpx_content')
    
    if not api_key:
        logger.warning("ALGOLIA_ADMIN_API_KEY não definida, pulando sincronização")
        return {
            "success_count": 0,
            "failed_count": len(arquivos_publicados),
            "error": "ALGOLIA_ADMIN_API_KEY não definida"
        }
    
    try:
        from algoliasearch.search_client import SearchClient
    except ImportError:
        logger.error("Biblioteca algoliasearch não instalada")
        return {
            "success_count": 0,
            "failed_count": len(arquivos_publicados),
            "error": "Biblioteca algoliasearch não instalada"
        }
    
    resultados = {
        "success_count": 0,
        "failed_count": 0,
        "errors": []
    }
    
    # Conectar ao Algolia
    client = SearchClient.create(app_id, api_key)
    index = client.init_index(index_name)
    
    # Buscar detalhes dos artigos publicados
    sanity_token = os.environ.get("SANITY_API_TOKEN")
    if not sanity_token:
        logger.error("Token do Sanity não encontrado para buscar detalhes dos posts")
        return resultados
    
    # Configurações do Sanity
    project_id = os.environ.get("SANITY_PROJECT_ID", "brby2yrg")
    dataset = "production"
    api_version = "2023-05-03"
    
    for arquivo in arquivos_publicados:
        try:
            # Ler o arquivo publicado para obter o título e slug
            with open(arquivo, "r", encoding="utf-8") as f:
                post_data = json.load(f)
            
            title = post_data.get('title')
            slug = post_data.get('slug', {}).get('current') if isinstance(post_data.get('slug'), dict) else post_data.get('slug')
            
            if not title:
                logger.warning(f"Arquivo sem título: {arquivo}")
                continue
            
            # Buscar o post no Sanity para obter o _id e outros detalhes
            query = f'*[_type == "post" && title == "{title}"][0]{{ _id, title, slug {{ current }}, publishedAt, excerpt }}'
            encoded_query = quote(query)
            
            url = f"https://{project_id}.api.sanity.io/v{api_version}/data/query/{dataset}?query={encoded_query}"
            headers = {"Authorization": f"Bearer {sanity_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json().get("result")
            if not result:
                logger.warning(f"Post não encontrado no Sanity: {title}")
                resultados["failed_count"] += 1
                continue
            
            # Preparar documento para Algolia
            algolia_doc = {
                "objectID": result.get('_id'),
                "title": result.get('title'),
                "slug": result.get('slug', {}).get('current') if isinstance(result.get('slug'), dict) else result.get('slug'),
                "publishedAt": result.get('publishedAt'),
                "excerpt": result.get('excerpt', ''),
                "originalSource": post_data.get('originalSource', {})
            }
            
            # Adicionar timestamp para ordenação
            if algolia_doc['publishedAt']:
                try:
                    dt = datetime.fromisoformat(algolia_doc['publishedAt'].replace('Z', '+00:00'))
                    algolia_doc['publishedAtTimestamp'] = int(dt.timestamp())
                except Exception:
                    pass
            
            # Indexar no Algolia
            index.save_object(algolia_doc)
            logger.info(f"Artigo sincronizado com Algolia: {title}")
            resultados["success_count"] += 1
            
        except Exception as e:
            logger.error(f"Erro ao sincronizar {arquivo}: {str(e)}")
            resultados["failed_count"] += 1
            resultados["errors"].append(str(e))
    
    logger.info(f"Sincronização com Algolia concluída: {resultados['success_count']} sucesso, {resultados['failed_count']} falhas")
    return resultados

# Execução principal
def main():
    """Função principal para execução do pipeline completo"""
    parser = argparse.ArgumentParser(description="Pipeline de blog para o Sanity CMS")
    parser.add_argument("--max-articles", type=int, default=3, help="Número máximo de artigos por feed (padrão: 3)")
    parser.add_argument("--skip-steps", type=str, help="Etapas a pular (separadas por vírgula)")
    parser.add_argument("--only-steps", type=str, help="Apenas executar estas etapas (separadas por vírgula)")
    parser.add_argument("--input-files", type=str, help="Arquivos específicos para processar (separados por vírgula)")
    parser.add_argument("--delay", type=int, default=2, help="Atraso entre etapas em segundos (padrão: 2)")
    
    args = parser.parse_args()
    
    logger.info("=== INICIANDO PIPELINE DE BLOG ===")
    
    # Determinar quais etapas executar
    skip_steps = args.skip_steps.split(",") if args.skip_steps else []
    only_steps = args.only_steps.split(",") if args.only_steps else []
    
    # Variáveis para armazenar os resultados de cada etapa
    arquivos_selecionados = []
    arquivos_traduzidos = []
    arquivos_formatados = []
    resultados_publicacao = None
    
    # Verificar se foram fornecidos arquivos de entrada
    if args.input_files:
        arquivos_selecionados = args.input_files.split(",")
        logger.info(f"Usando arquivos de entrada fornecidos: {len(arquivos_selecionados)}")
    
    # 1. Monitorar feeds
    if (not only_steps or "monitorar" in only_steps) and "monitorar" not in skip_steps and not args.input_files:
        arquivos_selecionados = monitorar_feeds(args.max_articles)
        
        # Pausa para verificar os arquivos
        logger.info(f"Aguardando {args.delay} segundos...")
        time.sleep(args.delay)
    
    # 2. Traduzir artigos
    if (not only_steps or "traduzir" in only_steps) and "traduzir" not in skip_steps and arquivos_selecionados:
        arquivos_traduzidos = traduzir_artigos(arquivos_selecionados)
        
        # Pausa para verificar os arquivos
        logger.info(f"Aguardando {args.delay} segundos...")
        time.sleep(args.delay)
    
    # 3. Formatar artigos
    if (not only_steps or "formatar" in only_steps) and "formatar" not in skip_steps and (arquivos_traduzidos or args.input_files):
        # Se não temos arquivos traduzidos mas temos input_files, assume que são arquivos traduzidos
        arquivos_para_formatar = arquivos_traduzidos if arquivos_traduzidos else arquivos_selecionados
        arquivos_formatados = formatar_artigos(arquivos_para_formatar)
        
        # Pausa para verificar os arquivos
        logger.info(f"Aguardando {args.delay} segundos...")
        time.sleep(args.delay)
    
    # 4. Publicar artigos
    if (not only_steps or "publicar" in only_steps) and "publicar" not in skip_steps and (arquivos_formatados or args.input_files):
        # Se não temos arquivos formatados mas temos input_files, assume que são arquivos formatados
        arquivos_para_publicar = arquivos_formatados if arquivos_formatados else arquivos_selecionados
        resultados_publicacao = publicar_artigos(arquivos_para_publicar)
    
    # 5. Sincronizar com Algolia (apenas se teve publicação bem-sucedida)
    resultados_algolia = None
    if resultados_publicacao and resultados_publicacao.get('published_files'):
        resultados_algolia = sincronizar_com_algolia(resultados_publicacao['published_files'])
    
    logger.info("=== PIPELINE DE BLOG CONCLUÍDO ===")
    
    # Mostrar estatísticas finais
    logger.info(f"Artigos selecionados: {len(arquivos_selecionados)}")
    logger.info(f"Artigos traduzidos: {len(arquivos_traduzidos)}")
    logger.info(f"Artigos formatados: {len(arquivos_formatados)}")
    if resultados_publicacao:
        logger.info(f"Artigos publicados: {resultados_publicacao['success_count']}")
        logger.info(f"Falhas na publicação: {resultados_publicacao['failed_count']}")
    if resultados_algolia:
        logger.info(f"Artigos sincronizados com Algolia: {resultados_algolia['success_count']}")
        logger.info(f"Falhas na sincronização com Algolia: {resultados_algolia['failed_count']}")

if __name__ == "__main__":
    main()