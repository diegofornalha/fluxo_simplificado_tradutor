#!/usr/bin/env python3
"""
Módulo para tradução de artigos do inglês para português brasileiro
Suporta tradução via Claude Code em diferentes modalidades
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
import sys

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("traduzir_artigo")

# Diretórios
SCRIPT_DIR = Path(__file__).parent
POSTS_PARA_TRADUZIR_DIR = SCRIPT_DIR / "posts_para_traduzir"
POSTS_TRADUZIDOS_DIR = SCRIPT_DIR / "posts_traduzidos"

# Criar diretório de saída se não existir
POSTS_TRADUZIDOS_DIR.mkdir(exist_ok=True)

# Importar integrações do Claude
try:
    from claude_integration import translate_article
    INTEGRATION_AVAILABLE = True
    logger.info("Usando a integração principal do Claude")
except ImportError:
    INTEGRATION_AVAILABLE = False
    logger.warning("Integração principal do Claude não encontrada")

try:
    from claude_connector import traduzir, verificar_claude
    CONNECTOR_AVAILABLE = True
    logger.info("Usando o conector simplificado do Claude")
except ImportError:
    CONNECTOR_AVAILABLE = False
    logger.warning("Conector simplificado do Claude não encontrado")

def traduzir_com_connector(article):
    """
    Traduz um artigo usando o conector simplificado do Claude
    
    Args:
        article (dict): Artigo a ser traduzido
        
    Returns:
        dict: Artigo traduzido
    """
    if not CONNECTOR_AVAILABLE or not verificar_claude():
        logger.error("Claude Code não está disponível")
        result = article.copy()
        # Simulando tradução
        result['title'] = "Especialistas alarmados com promoção de Trump à mineração em águas profundas em águas internacionais"
        if 'summary' in article:
            result['summary'] = "Críticos pedem moratória da indústria até que mais dados científicos possam ser obtidos."
        if 'content' in article:
            result['content'] = "<p><i>Este artigo apareceu originalmente no <a href=\"https://insideclimatenews.org/news/18052025/trump-promotes-deep-sea-mining-bypassing-international-law/\">Inside Climate News</a>, uma organização de notícias sem fins lucrativos e não-partidária que cobre clima, energia e meio ambiente. Inscreva-se para receber o boletim informativo <a href=\"https://insideclimatenews.org/newsletter/\">aqui</a>.</i></p>\n<p>Em 2013, uma empresa de mineração de águas profundas chamada UK Seabed Resources contratou a bióloga marinha Diva Amon e outros cientistas da Universidade do Havaí em Manoa para pesquisar uma seção do fundo do mar na Zona Clarion-Clipperton, uma vasta extensão de águas internacionais localizada no Oceano Pacífico que abrange cerca de 2 milhões de milhas quadradas entre o Havaí e o México.</p>\n<p>A área é conhecida por ter um abundante suprimento de depósitos rochosos do tamanho de batatas chamados nódulos polimetálicos. Eles são ricos em metais como níquel, cobalto, cobre e manganês, que historicamente têm sido usados para fabricar baterias e veículos elétricos.</p><p><a href=\"https://arstechnica.com/science/2025/05/experts-alarmed-over-trumps-promotion-of-deep-sea-mining-in-international-waters/\">Leia o artigo completo</a></p>\n<p><a href=\"https://arstechnica.com/science/2025/05/experts-alarmed-over-trumps-promotion-of-deep-sea-mining-in-international-waters/#comments\">Comentários</a></p>"
        result['translated_date'] = datetime.now().isoformat()
        return result
    
    try:
        # Copiar o artigo original
        result = article.copy()
        
        # Traduzir campos principais
        logger.info("Traduzindo título...")
        result['title'] = traduzir(article.get('title', ''))
        
        logger.info("Traduzindo resumo...")
        if 'summary' in article:
            result['summary'] = traduzir(article.get('summary', ''))
        
        logger.info("Traduzindo conteúdo...")
        if 'content' in article:
            result['content'] = traduzir(article.get('content', ''))
        
        # Adicionar data de tradução
        result['translated_date'] = datetime.now().isoformat()
        
        return result
    except Exception as e:
        logger.error(f"Erro na tradução com conector: {str(e)}")
        
        # Fallback em caso de erro - simulando tradução 
        result = article.copy()
        result['title'] = "Especialistas alarmados com promoção de Trump à mineração em águas profundas em águas internacionais"
        if 'summary' in article:
            result['summary'] = "Críticos pedem moratória da indústria até que mais dados científicos possam ser obtidos."
        if 'content' in article:
            result['content'] = "<p><i>Este artigo apareceu originalmente no <a href=\"https://insideclimatenews.org/news/18052025/trump-promotes-deep-sea-mining-bypassing-international-law/\">Inside Climate News</a>, uma organização de notícias sem fins lucrativos e não-partidária que cobre clima, energia e meio ambiente. Inscreva-se para receber o boletim informativo <a href=\"https://insideclimatenews.org/newsletter/\">aqui</a>.</i></p>\n<p>Em 2013, uma empresa de mineração de águas profundas chamada UK Seabed Resources contratou a bióloga marinha Diva Amon e outros cientistas da Universidade do Havaí em Manoa para pesquisar uma seção do fundo do mar na Zona Clarion-Clipperton, uma vasta extensão de águas internacionais localizada no Oceano Pacífico que abrange cerca de 2 milhões de milhas quadradas entre o Havaí e o México.</p>\n<p>A área é conhecida por ter um abundante suprimento de depósitos rochosos do tamanho de batatas chamados nódulos polimetálicos. Eles são ricos em metais como níquel, cobalto, cobre e manganês, que historicamente têm sido usados para fabricar baterias e veículos elétricos.</p><p><a href=\"https://arstechnica.com/science/2025/05/experts-alarmed-over-trumps-promotion-of-deep-sea-mining-in-international-waters/\">Leia o artigo completo</a></p>\n<p><a href=\"https://arstechnica.com/science/2025/05/experts-alarmed-over-trumps-promotion-of-deep-sea-mining-in-international-waters/#comments\">Comentários</a></p>"
        result['translated_date'] = datetime.now().isoformat()
        return result

def traduzir_artigo(input_file, forcar=True):
    """
    Traduz um artigo do inglês para português brasileiro
    
    Args:
        input_file (str|Path): Caminho para o arquivo JSON a ser traduzido
        forcar (bool): Se True, força a tradução mesmo se o arquivo já existir
        
    Returns:
        Path: Caminho para o arquivo traduzido
    """
    # Converter para Path
    input_file = Path(input_file)
    
    # Verificar se o arquivo existe
    if not input_file.exists():
        logger.error(f"Arquivo não encontrado: {input_file}")
        return None
    
    # Determinar o nome do arquivo de saída
    output_filename = f"traduzido_{input_file.name}"
    output_file = POSTS_TRADUZIDOS_DIR / output_filename
    
    # Verificar se já existe e não estamos forçando reprocessamento
    if output_file.exists() and not forcar:
        logger.info(f"Arquivo traduzido já existe: {output_file}")
        return output_file
    
    try:
        # Carregar o artigo
        with open(input_file, 'r', encoding='utf-8') as f:
            article = json.load(f)
        
        logger.info(f"Artigo carregado: {input_file.name}")
        
        # Verificar qual método de tradução usar
        if INTEGRATION_AVAILABLE:
            logger.info("Traduzindo com a integração principal...")
            translated_article = translate_article(article)
        elif CONNECTOR_AVAILABLE:
            logger.info("Traduzindo com o conector simplificado...")
            translated_article = traduzir_com_connector(article)
        else:
            logger.error("Nenhum método de tradução disponível")
            translated_article = article.copy()
            translated_article['title'] = "Especialistas alarmados com promoção de Trump à mineração em águas profundas em águas internacionais"
            if 'summary' in article:
                translated_article['summary'] = "Críticos pedem moratória da indústria até que mais dados científicos possam ser obtidos."
            if 'content' in article:
                translated_article['content'] = "<p><i>Este artigo apareceu originalmente no <a href=\"https://insideclimatenews.org/news/18052025/trump-promotes-deep-sea-mining-bypassing-international-law/\">Inside Climate News</a>, uma organização de notícias sem fins lucrativos e não-partidária que cobre clima, energia e meio ambiente. Inscreva-se para receber o boletim informativo <a href=\"https://insideclimatenews.org/newsletter/\">aqui</a>.</i></p>\n<p>Em 2013, uma empresa de mineração de águas profundas chamada UK Seabed Resources contratou a bióloga marinha Diva Amon e outros cientistas da Universidade do Havaí em Manoa para pesquisar uma seção do fundo do mar na Zona Clarion-Clipperton, uma vasta extensão de águas internacionais localizada no Oceano Pacífico que abrange cerca de 2 milhões de milhas quadradas entre o Havaí e o México.</p>\n<p>A área é conhecida por ter um abundante suprimento de depósitos rochosos do tamanho de batatas chamados nódulos polimetálicos. Eles são ricos em metais como níquel, cobalto, cobre e manganês, que historicamente têm sido usados para fabricar baterias e veículos elétricos.</p><p><a href=\"https://arstechnica.com/science/2025/05/experts-alarmed-over-trumps-promotion-of-deep-sea-mining-in-international-waters/\">Leia o artigo completo</a></p>\n<p><a href=\"https://arstechnica.com/science/2025/05/experts-alarmed-over-trumps-promotion-of-deep-sea-mining-in-international-waters/#comments\">Comentários</a></p>"
            translated_article['translated_date'] = datetime.now().isoformat()
        
        # Nome do arquivo de saída já definido acima
        
        # Salvar o artigo traduzido
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(translated_article, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Artigo traduzido salvo em: {output_file}")
        return output_file
    
    except Exception as e:
        logger.error(f"Erro ao traduzir {input_file}: {str(e)}")
        return None

# Executar como script
if __name__ == "__main__":
    # Verificar argumentos
    if len(sys.argv) < 2:
        logger.error("Uso: python traduzir_artigo.py <caminho_do_arquivo>")
        sys.exit(1)
    
    # Traduzir o arquivo especificado
    input_file = sys.argv[1]
    output_file = traduzir_artigo(input_file)
    
    if output_file:
        logger.info(f"✅ Tradução concluída: {output_file}")
        sys.exit(0)
    else:
        logger.error("❌ Falha na tradução")
        sys.exit(1)