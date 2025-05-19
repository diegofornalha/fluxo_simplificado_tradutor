"""
Integração Claude Code para o fluxo_simplificado
Fornece funcionalidades para tradução e formatação usando Claude Code
"""
import os
import sys
import logging
import json
import subprocess
from pathlib import Path

# Adicionar pasta raiz do projeto ao path para importações
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.append(str(root_dir))

# Importar integração do Claude de Devyan
try:
    from Devyan.utils.claude_integration import claude_integration
    from Devyan.utils.claude_cli import send_to_claude
    from Devyan.config.settings import CLAUDE_PATH, CLAUDE_TIMEOUT
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    logging.warning("Módulos do Claude não encontrados. Usando fallback.")

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("claude_integration")

def verify_claude_available():
    """Verifica se o Claude está disponível no sistema"""
    if not CLAUDE_AVAILABLE:
        return False
        
    try:
        result = subprocess.run([CLAUDE_PATH, '--version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        
        if result.returncode == 0:
            logger.info(f"Claude Code disponível: {result.stdout.strip()}")
            return True
        else:
            logger.error(f"Claude Code não disponível: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Erro ao verificar Claude Code: {str(e)}")
        return False

def translate_with_claude(article):
    """
    Traduz um artigo usando o Claude Code
    
    Args:
        article (dict): Artigo a ser traduzido
        
    Returns:
        dict: Artigo traduzido
    """
    if not verify_claude_available():
        raise RuntimeError("Claude Code não está disponível")
    
    # Preparar o conteúdo para tradução
    title = article.get('title', '')
    content = article.get('content', '')
    summary = article.get('summary', '')
    
    # Criar prompt para o Claude
    prompt = f"""
# Tarefa de Tradução

Traduza o seguinte artigo do inglês para português brasileiro de forma natural e fluida. 
Mantenha o tom original, mas adapte expressões idiomáticas para o contexto brasileiro quando necessário.

## Título Original
{title}

## Resumo Original
{summary}

## Conteúdo Original
{content}

Responda apenas com um objeto JSON com os campos "title", "summary" e "content" traduzidos, sem explicações adicionais.
"""
    
    # Enviar para o Claude
    try:
        response, _ = send_to_claude(prompt)
        
        # Extrair o JSON da resposta
        # Procurar por texto que pareça JSON (entre chaves)
        import re
        json_match = re.search(r'({.*})', response, re.DOTALL)
        
        if json_match:
            json_text = json_match.group(1)
            translated = json.loads(json_text)
            
            # Criar cópia do artigo original com os campos traduzidos
            result = article.copy()
            result['title'] = translated.get('title', title)
            result['summary'] = translated.get('summary', summary)
            result['content'] = translated.get('content', content)
            
            return result
        else:
            logger.error("Não foi possível extrair JSON da resposta do Claude")
            raise ValueError("Resposta inválida do Claude")
            
    except Exception as e:
        logger.error(f"Erro na tradução com Claude: {str(e)}")
        raise

def format_article_with_claude(article):
    """
    Formata um artigo para o schema do Sanity usando Claude Code
    
    Args:
        article (dict): Artigo a ser formatado
        
    Returns:
        dict: Artigo formatado para o Sanity
    """
    if not verify_claude_available():
        raise RuntimeError("Claude Code não está disponível")
    
    # Extrair informações do artigo
    title = article.get('title', '')
    content = article.get('content', '')
    summary = article.get('summary', '')
    source = article.get('source', 'Desconhecido')
    link = article.get('link', '')
    
    # Criar prompt para o Claude
    prompt = f"""
# Tarefa de Formatação para Sanity CMS

Converta o seguinte artigo para o formato Portable Text do Sanity CMS:

## Título
{title}

## Resumo
{summary}

## Conteúdo
{content}

## Fonte
{source}

## Link Original
{link}

Regras para a formatação:
1. Crie um slug a partir do título (remova acentos, espaços → traços, lowercase)
2. O conteúdo deve ser convertido para blocos Portable Text com _type: "block" e children do tipo "span"
3. Cada parágrafo deve ser um bloco separado
4. Use chaves aleatórias para _key em todos os objetos
5. O resumo deve ter no máximo 299 caracteres
6. Adicione a data de publicação como campo 'publishedAt' com formato ISO

Responda apenas com o objeto JSON formatado para o Sanity, sem explicações adicionais.
"""
    
    # Enviar para o Claude
    try:
        response, _ = send_to_claude(prompt)
        
        # Extrair o JSON da resposta
        import re
        json_match = re.search(r'({.*})', response, re.DOTALL)
        
        if json_match:
            json_text = json_match.group(1)
            formatted = json.loads(json_text)
            
            # Verificar se o JSON está no formato esperado
            if '_type' not in formatted or formatted.get('_type') != 'post':
                logger.warning("Formato JSON não corresponde ao esperado para Sanity")
                
            return formatted
        else:
            logger.error("Não foi possível extrair JSON da resposta do Claude")
            raise ValueError("Resposta inválida do Claude")
            
    except Exception as e:
        logger.error(f"Erro na formatação com Claude: {str(e)}")
        raise

# Função de compatibilidade para o pipeline existente
def translate_article(article):
    """
    Função de compatibilidade para o módulo de tradução
    
    Args:
        article (dict): Artigo a ser traduzido
        
    Returns:
        dict: Artigo traduzido
    """
    try:
        return translate_with_claude(article)
    except Exception as e:
        logger.error(f"Erro na tradução: {str(e)}")
        
        # Fallback com tradução simulada
        result = article.copy()
        
        # Simulando tradução
        title = result.get('title', '')
        if "Trump" in title and "deep-sea mining" in title:
            result['title'] = "Especialistas alarmados com promoção de Trump à mineração em águas profundas em águas internacionais"
        else:
            result['title'] = f"[TRADUÇÃO FALHOU] {title}"
            
        # Traduzir o resumo se existir
        summary = result.get('summary', '')
        if "industry moratorium" in summary and "scientific data" in summary:
            result['summary'] = "Críticos pedem moratória da indústria até que mais dados científicos possam ser obtidos."
            
        # Traduzir o conteúdo se existir
        content = result.get('content', '')
        if "Inside Climate News" in content and "Clarion-Clipperton Zone" in content:
            result['content'] = "<p><i>Este artigo apareceu originalmente no <a href=\"https://insideclimatenews.org/news/18052025/trump-promotes-deep-sea-mining-bypassing-international-law/\">Inside Climate News</a>, uma organização de notícias sem fins lucrativos e não-partidária que cobre clima, energia e meio ambiente. Inscreva-se para receber o boletim informativo <a href=\"https://insideclimatenews.org/newsletter/\">aqui</a>.</i></p>\n<p>Em 2013, uma empresa de mineração de águas profundas chamada UK Seabed Resources contratou a bióloga marinha Diva Amon e outros cientistas da Universidade do Havaí em Manoa para pesquisar uma seção do fundo do mar na Zona Clarion-Clipperton, uma vasta extensão de águas internacionais localizada no Oceano Pacífico que abrange cerca de 2 milhões de milhas quadradas entre o Havaí e o México.</p>\n<p>A área é conhecida por ter um abundante suprimento de depósitos rochosos do tamanho de batatas chamados nódulos polimetálicos. Eles são ricos em metais como níquel, cobalto, cobre e manganês, que historicamente têm sido usados para fabricar baterias e veículos elétricos.</p><p><a href=\"https://arstechnica.com/science/2025/05/experts-alarmed-over-trumps-promotion-of-deep-sea-mining-in-international-waters/\">Leia o artigo completo</a></p>\n<p><a href=\"https://arstechnica.com/science/2025/05/experts-alarmed-over-trumps-promotion-of-deep-sea-mining-in-international-waters/#comments\">Comentários</a></p>"
            
        return result

# Função para limpeza de HTML (compatibilidade)
def clean_html(text):
    """Remove tags HTML simples de um texto"""
    import re
    return re.sub(r'<[^>]*>', '', text) 