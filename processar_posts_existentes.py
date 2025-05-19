import os
import json
import logging
from pathlib import Path
import sys
from datetime import datetime
import argparse

# Configurar o caminho do projeto
sys.path.insert(0, str(Path(__file__).parent))

from traduzir_artigo import traduzir_artigo
from claude_connector import formatar_para_sanity

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("processar_posts")

# Diretórios
SCRIPT_DIR = Path(__file__).parent
POSTS_PARA_TRADUZIR_DIR = SCRIPT_DIR / "posts_para_traduzir"
POSTS_TRADUZIDOS_DIR = SCRIPT_DIR / "posts_traduzidos"
POSTS_FORMATADOS_DIR = SCRIPT_DIR / "posts_formatados"

# Criar diretórios se não existirem
POSTS_TRADUZIDOS_DIR.mkdir(exist_ok=True)
POSTS_FORMATADOS_DIR.mkdir(exist_ok=True)

def listar_posts_para_traduzir():
    """Lista todos os arquivos JSON na pasta posts_para_traduzir"""
    arquivos = []
    
    if not POSTS_PARA_TRADUZIR_DIR.exists():
        logger.error(f"Diretório não existe: {POSTS_PARA_TRADUZIR_DIR}")
        return arquivos
    
    for arquivo in POSTS_PARA_TRADUZIR_DIR.glob("*.json"):
        arquivos.append(arquivo)
    
    return sorted(arquivos)

def processar_artigo(arquivo_path, formatar_sanity=True, forcar=True):
    """Processa um único artigo: traduz e opcionalmente formata para Sanity
    
    Args:
        arquivo_path: Caminho para o arquivo
        formatar_sanity: Se True, formata para Sanity após traduzir
        forcar: Se True, força a tradução mesmo se o arquivo já existir
    """
    try:
        logger.info(f"Processando: {arquivo_path.name}")
        
        # Traduzir o artigo
        arquivo_traduzido = traduzir_artigo(arquivo_path, forcar=True)
        logger.info(f"✅ Traduzido: {arquivo_traduzido}")
        
        if formatar_sanity and arquivo_traduzido:
            # Carregar o artigo traduzido
            with open(arquivo_traduzido, "r", encoding="utf-8") as f:
                artigo = json.load(f)
            
            # Formatar para Sanity
            documento_formatado = formatar_para_sanity(
                titulo=artigo.get("title", ""),
                conteudo=artigo.get("content", artigo.get("summary", "")),
                resumo=artigo.get("summary", ""),
                fonte=artigo.get("source", ""),
                link=artigo.get("link", "")
            )
            
            # Salvar documento formatado
            nome_formatado = f"sanity_{arquivo_traduzido.stem}.json"
            arquivo_formatado = POSTS_FORMATADOS_DIR / nome_formatado
            
            with open(arquivo_formatado, "w", encoding="utf-8") as f:
                json.dump(documento_formatado, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ Formatado para Sanity: {arquivo_formatado}")
            return arquivo_traduzido, arquivo_formatado
        
        return arquivo_traduzido, None
        
    except KeyError as e:
        # Vamos verificar se é um problema de campo ausente
        logger.warning(f"Campo ausente no arquivo {arquivo_path}: {str(e)}")
        
        # Tentar ler o arquivo novamente para adaptar
        try:
            with open(arquivo_path, "r", encoding="utf-8") as f:
                artigo = json.load(f)
            
            # Verificar os campos e adaptar se necessário
            if "excerpt" not in artigo and "summary" in artigo:
                logger.info(f"Adaptando formato: usando 'summary' como 'excerpt'")
                # Modificar o arquivo original para adicionar excerpt
                artigo["excerpt"] = artigo["summary"]
                
                # Salvar o arquivo modificado
                with open(arquivo_path, "w", encoding="utf-8") as f:
                    json.dump(artigo, f, ensure_ascii=False, indent=2)
                
                # Tentar traduzir novamente
                return processar_artigo(arquivo_path, formatar_sanity)
            else:
                logger.error(f"Não foi possível adaptar o formato do arquivo")
                return None, None
                
        except Exception as e2:
            logger.error(f"❌ Erro ao tentar adaptar {arquivo_path}: {str(e2)}")
            return None, None
            
    except Exception as e:
        logger.error(f"❌ Erro ao processar {arquivo_path}: {str(e)}")
        return None, None

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Processa artigos para tradução")
    parser.add_argument("--limit", type=int, help="Número máximo de artigos para processar")
    parser.add_argument("--no-sanity", action="store_true", help="Pular formatação para Sanity")
    parser.add_argument("--force", action="store_true", help="Forçar reprocessamento de arquivos existentes")
    args = parser.parse_args()
    
    logger.info("🚀 Iniciando processamento de artigos...")
    
    # Listar arquivos
    arquivos = listar_posts_para_traduzir()
    
    if not arquivos:
        logger.warning("Nenhum arquivo encontrado em posts_para_traduzir")
        return
    
    logger.info(f"📁 {len(arquivos)} arquivos encontrados")
    
    # Aplicar limite se especificado
    if args.limit:
        arquivos = arquivos[:args.limit]
        logger.info(f"⚡ Limitado a {args.limit} arquivos")
    
    # Processar arquivos
    resultados = {
        "sucesso": [],
        "erro": []
    }
    
    for i, arquivo in enumerate(arquivos, 1):
        logger.info(f"\n[{i}/{len(arquivos)}] Processando...")
        
        traduzido, formatado = processar_artigo(
            arquivo, 
            formatar_sanity=not args.no_sanity,
            forcar=args.force
        )
        
        if traduzido:
            resultados["sucesso"].append({
                "original": arquivo,
                "traduzido": traduzido,
                "formatado": formatado
            })
        else:
            resultados["erro"].append(arquivo)
    
    # Resumo final
    logger.info("\n" + "="*50)
    logger.info("📊 RESUMO DO PROCESSAMENTO:")
    logger.info(f"✅ Sucesso: {len(resultados['sucesso'])} arquivos")
    logger.info(f"❌ Erro: {len(resultados['erro'])} arquivos")
    
    if resultados["erro"]:
        logger.info("\nArquivos com erro:")
        for arquivo in resultados["erro"]:
            logger.info(f"  - {arquivo.name}")
    
    # Salvar relatório
    relatorio_path = SCRIPT_DIR / f"relatorio_processamento_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(relatorio_path, "w", encoding="utf-8") as f:
        json.dump({
            "data": datetime.now().isoformat(),
            "total_arquivos": len(arquivos),
            "sucesso": len(resultados["sucesso"]),
            "erro": len(resultados["erro"]),
            "detalhes": resultados
        }, f, ensure_ascii=False, indent=2, default=str)
    
    logger.info(f"\n📄 Relatório salvo em: {relatorio_path}")
    logger.info("\n✨ Processamento concluído!")

if __name__ == "__main__":
    main()