#!/usr/bin/env python3
"""
Script de demonstração - Tradução e formatação de artigo com Claude
Mostra como usar o Claude Code dentro do fluxo simplificado
"""

import json
import os
import logging
from pathlib import Path
import datetime
import uuid
from claude_connector import traduzir, resumir, formatar_para_sanity

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("traduzir_artigo")

# Configurar diretórios
SCRIPT_DIR = Path(__file__).parent
POSTS_DIR = SCRIPT_DIR / "posts_para_traduzir"
POSTS_TRADUZIDOS_DIR = SCRIPT_DIR / "posts_traduzidos"
POSTS_FORMATADOS_DIR = SCRIPT_DIR / "posts_formatados"

# Criar diretórios se não existirem
POSTS_DIR.mkdir(exist_ok=True)
POSTS_TRADUZIDOS_DIR.mkdir(exist_ok=True)
POSTS_FORMATADOS_DIR.mkdir(exist_ok=True)

def criar_artigo_demo():
    """Cria um artigo de demonstração em inglês"""
    artigo = {
        "title": "The Future of AI in Software Development",
        "excerpt": "Artificial Intelligence is transforming how software is created, with tools like GitHub Copilot and Claude changing developer workflows.",
        "content": [
            "Artificial Intelligence is revolutionizing software development in unprecedented ways. AI coding assistants are becoming increasingly sophisticated, helping developers write better code faster.",
            "Tools like GitHub Copilot, powered by OpenAI's technology, can suggest entire functions and blocks of code based on comments or function signatures. Similarly, Claude and other AI assistants can help with code review, debugging, and even architectural decisions.",
            "According to recent surveys, developers using AI tools report up to 40% increase in productivity. These tools are particularly effective for repetitive tasks, boilerplate code, and standard implementations.",
            "However, concerns remain about code quality, security vulnerabilities, and the potential loss of programming skills. Critics argue that over-reliance on AI might lead to developers who don't fully understand the code they're implementing.",
            "The future likely involves collaborative workflows where AI handles routine coding tasks while humans focus on higher-level design, creativity, and quality assurance. This partnership between human creativity and AI efficiency could reshape software development in the decades to come."
        ],
        "source": "TechTrends Magazine",
        "source_url": "https://example.com/future-ai-software-development",
        "published_date": datetime.datetime.now().isoformat()
    }
    
    # Salvar o artigo como JSON
    artigo_path = POSTS_DIR / "artigo_demo.json"
    with open(artigo_path, "w", encoding="utf-8") as f:
        json.dump(artigo, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Artigo de demonstração criado em: {artigo_path}")
    return artigo_path

def traduzir_artigo(artigo_path):
    """Traduz um artigo do inglês para o português"""
    # Carregar o artigo
    with open(artigo_path, "r", encoding="utf-8") as f:
        artigo = json.load(f)
    
    logger.info(f"Traduzindo artigo: {artigo['title']}")
    
    # Traduzir título
    titulo_traduzido = traduzir(artigo["title"])
    logger.info(f"Título traduzido: {titulo_traduzido}")
    
    # Traduzir resumo
    resumo_traduzido = traduzir(artigo["excerpt"])
    logger.info(f"Resumo traduzido: {resumo_traduzido}")
    
    # Traduzir conteúdo (cada parágrafo)
    logger.info("Traduzindo parágrafos...")
    paragrafos_traduzidos = []
    
    for i, paragrafo in enumerate(artigo["content"]):
        logger.info(f"Traduzindo parágrafo {i+1}/{len(artigo['content'])}")
        paragrafo_traduzido = traduzir(paragrafo)
        paragrafos_traduzidos.append(paragrafo_traduzido)
    
    # Criar artigo traduzido
    artigo_traduzido = {
        "title": titulo_traduzido,
        "excerpt": resumo_traduzido,
        "content": paragrafos_traduzidos,
        "source": artigo["source"],
        "source_url": artigo["source_url"],
        "translated_date": datetime.datetime.now().isoformat(),
        "original_title": artigo["title"],
        "original_language": "en"
    }
    
    # Salvar o artigo traduzido
    nome_arquivo = f"traduzido_{Path(artigo_path).stem}.json"
    artigo_traduzido_path = POSTS_TRADUZIDOS_DIR / nome_arquivo
    
    with open(artigo_traduzido_path, "w", encoding="utf-8") as f:
        json.dump(artigo_traduzido, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Artigo traduzido salvo em: {artigo_traduzido_path}")
    return artigo_traduzido_path

def formatar_artigo_sanity(artigo_traduzido_path):
    """Formata um artigo traduzido para o formato Sanity CMS"""
    # Carregar o artigo traduzido
    with open(artigo_traduzido_path, "r", encoding="utf-8") as f:
        artigo = json.load(f)
    
    logger.info(f"Formatando artigo para Sanity: {artigo['title']}")
    
    # Unir parágrafos para enviar ao Claude
    conteudo_completo = "\n\n".join(artigo["content"])
    
    # Formatar para Sanity
    documento_sanity = formatar_para_sanity(
        titulo=artigo["title"],
        conteudo=conteudo_completo,
        resumo=artigo["excerpt"],
        fonte=artigo["source"],
        link=artigo["source_url"]
    )
    
    if not documento_sanity:
        logger.error("Erro ao formatar para Sanity!")
        return None
    
    # Adicionar campos adicionais
    documento_sanity["_id"] = f"post_{uuid.uuid4().hex}"
    documento_sanity["_createdAt"] = datetime.datetime.now().isoformat()
    
    # Salvar o documento formatado
    nome_arquivo = f"sanity_{Path(artigo_traduzido_path).stem}.json"
    documento_path = POSTS_FORMATADOS_DIR / nome_arquivo
    
    with open(documento_path, "w", encoding="utf-8") as f:
        json.dump(documento_sanity, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Documento Sanity salvo em: {documento_path}")
    return documento_path

def main():
    """Função principal do script"""
    logger.info("Iniciando demonstração de tradução e formatação com Claude")
    
    # Criar artigo de demonstração
    artigo_path = criar_artigo_demo()
    
    # Traduzir o artigo
    artigo_traduzido_path = traduzir_artigo(artigo_path)
    
    # Formatar para Sanity
    documento_path = formatar_artigo_sanity(artigo_traduzido_path)
    
    if documento_path:
        logger.info("\n✅ DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        logger.info("O Claude Code está corretamente integrado ao fluxo simplificado.")
        logger.info("Os arquivos gerados estão disponíveis em:")
        logger.info(f"- Original: {artigo_path}")
        logger.info(f"- Traduzido: {artigo_traduzido_path}")
        logger.info(f"- Formatado: {documento_path}")
    else:
        logger.error("\n❌ DEMONSTRAÇÃO FALHOU!")
        logger.error("Verifique os erros acima.")

if __name__ == "__main__":
    main() 