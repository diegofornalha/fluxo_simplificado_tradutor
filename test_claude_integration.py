#!/usr/bin/env python3
"""
Script de teste para verificar a integração do Claude Code com o fluxo simplificado
"""

import os
import json
import logging
from pathlib import Path
import sys
import time

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("teste")

# Definir diretórios
SCRIPT_DIR = Path(__file__).parent
TEMP_DIR = SCRIPT_DIR / "temp_test"
TEMP_DIR.mkdir(exist_ok=True)

def criar_artigo_teste():
    """Cria um artigo de teste para tradução"""
    artigo = {
        "title": "The Future of AI in Software Development",
        "summary": "Artificial Intelligence is transforming how software is created, with tools like GitHub Copilot and Claude Code leading the way to more efficient programming workflows.",
        "content": "<p>Software development is undergoing a significant transformation thanks to advances in artificial intelligence. The emergence of AI coding assistants like GitHub Copilot, Amazon CodeWhisperer, and Claude Code are changing how developers approach their daily tasks.</p>\n\n<p>These AI tools can:</p>\n\n<ul>\n<li>Generate code snippets based on natural language descriptions</li>\n<li>Automatically complete functions and methods</li>\n<li>Suggest fixes for common bugs and issues</li>\n<li>Help with documentation and code comments</li>\n</ul>\n\n<p>According to recent surveys, developers using these tools report productivity increases of 20-30% on average. The quality of AI-generated code continues to improve as models are trained on larger codebases and more diverse programming languages.</p>",
        "source": "TechBlog",
        "link": "https://example.com/ai-software-development",
        "tags": ["AI", "Software Development", "Programming", "Technology Trends"]
    }
    
    # Salvar no arquivo temporário
    artigo_path = TEMP_DIR / "artigo_teste.json"
    with open(artigo_path, "w", encoding="utf-8") as f:
        json.dump(artigo, f, ensure_ascii=False, indent=2)
        
    logger.info(f"Artigo de teste criado: {artigo_path}")
    return artigo_path

def test_claude_disponivel():
    """Verifica se o Claude está disponível"""
    logger.info("\n🧪 Testando disponibilidade do Claude Code...")
    
    try:
        from claude_integration import verify_claude_available
        
        if verify_claude_available():
            logger.info("✅ Claude Code disponível!")
            return True
        else:
            logger.error("❌ Claude Code não disponível")
            return False
    except ImportError:
        logger.error("❌ Módulo de integração não encontrado")
        return False

def test_traducao():
    """Testa a tradução de um artigo com Claude"""
    logger.info("\n🧪 Testando tradução com Claude Code...")
    
    try:
        from claude_integration import translate_with_claude
        
        # Carregar artigo de teste
        artigo_path = criar_artigo_teste()
        with open(artigo_path, "r", encoding="utf-8") as f:
            artigo = json.load(f)
            
        # Traduzir artigo
        start_time = time.time()
        artigo_traduzido = translate_with_claude(artigo)
        duration = time.time() - start_time
        
        # Verificar se a tradução foi feita
        if artigo_traduzido.get("title") != artigo.get("title"):
            logger.info(f"✅ Tradução realizada em {duration:.2f} segundos")
            
            # Salvar tradução
            traduzido_path = TEMP_DIR / "artigo_traduzido.json"
            with open(traduzido_path, "w", encoding="utf-8") as f:
                json.dump(artigo_traduzido, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Título traduzido: {artigo_traduzido.get('title')}")
            logger.info(f"Artigo traduzido salvo: {traduzido_path}")
            return True, artigo_traduzido
        else:
            logger.error("❌ Tradução não foi realizada")
            return False, None
    except Exception as e:
        logger.error(f"❌ Erro ao testar tradução: {str(e)}")
        return False, None

def test_formatacao(artigo_traduzido=None):
    """Testa a formatação de um artigo para o Sanity"""
    logger.info("\n🧪 Testando formatação para Sanity com Claude Code...")
    
    if not artigo_traduzido:
        logger.warning("Nenhum artigo traduzido fornecido. Usando o arquivo de teste se disponível.")
        traduzido_path = TEMP_DIR / "artigo_traduzido.json"
        if traduzido_path.exists():
            with open(traduzido_path, "r", encoding="utf-8") as f:
                artigo_traduzido = json.load(f)
        else:
            _, artigo_traduzido = test_traducao()
            if not artigo_traduzido:
                logger.error("❌ Não foi possível obter um artigo traduzido para formatação")
                return False
    
    try:
        from claude_integration import format_article_with_claude
        
        # Formatar artigo
        start_time = time.time()
        artigo_formatado = format_article_with_claude(artigo_traduzido)
        duration = time.time() - start_time
        
        # Verificar formatação
        if artigo_formatado.get("_type") == "post" and artigo_formatado.get("content"):
            logger.info(f"✅ Formatação realizada em {duration:.2f} segundos")
            
            # Salvar formatação
            formatado_path = TEMP_DIR / "artigo_formatado.json"
            with open(formatado_path, "w", encoding="utf-8") as f:
                json.dump(artigo_formatado, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Slug gerado: {artigo_formatado.get('slug', {}).get('current')}")
            logger.info(f"Blocos de conteúdo: {len(artigo_formatado.get('content', []))}")
            logger.info(f"Artigo formatado salvo: {formatado_path}")
            return True
        else:
            logger.error("❌ Formatação não foi realizada corretamente")
            logger.error(f"Tipo do documento: {artigo_formatado.get('_type')}")
            return False
    except Exception as e:
        logger.error(f"❌ Erro ao testar formatação: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Teste de integração Claude Code no fluxo_simplificado...\n")
    
    # Executar testes
    claude_disponivel = test_claude_disponivel()
    
    if claude_disponivel:
        success_traducao, artigo_traduzido = test_traducao()
        
        if success_traducao:
            success_formatacao = test_formatacao(artigo_traduzido)
        else:
            logger.warning("Pulando teste de formatação devido a falha na tradução")
            success_formatacao = False
    else:
        logger.error("Claude Code não disponível. Testes abortados.")
        sys.exit(1)
    
    # Resumo
    logger.info("\n" + "="*50)
    logger.info("📊 RESUMO DOS TESTES:")
    
    if claude_disponivel:
        logger.info("✅ Claude Code disponível")
    else:
        logger.info("❌ Claude Code não disponível")
        
    if success_traducao:
        logger.info("✅ Tradução com Claude funcionando")
    else:
        logger.info("❌ Tradução com Claude falhou")
        
    if success_formatacao:
        logger.info("✅ Formatação para Sanity funcionando")
    else:
        logger.info("❌ Formatação para Sanity falhou")
    
    # Status geral
    if claude_disponivel and success_traducao and success_formatacao:
        logger.info("\n🎉 TODOS OS TESTES PASSARAM! A integração com Claude está funcionando.")
        logger.info("\n✨ CONCLUSÃO: O fluxo_simplificado pode usar o Claude Code com sucesso!")
        sys.exit(0)
    else:
        logger.error("\n❌ Alguns testes falharam. Verifique os problemas acima.")
        sys.exit(1) 