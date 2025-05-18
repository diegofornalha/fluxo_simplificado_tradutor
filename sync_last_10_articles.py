#!/usr/bin/env python3
"""
Script para sincronizar apenas os últimos 10 artigos publicados com o Algolia
"""

import os
import json
import logging
import sys
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sync_last_10")

# Importar a função de sincronização
sys.path.append(str(Path(__file__).parent))
from run_pipeline import sincronizar_com_algolia

def main():
    """Sincroniza os últimos 10 artigos publicados"""
    # Definir diretório de artigos publicados
    POSTS_PUBLICADOS_DIR = Path(__file__).parent / "posts_publicados"
    
    # Listar arquivos publicados
    arquivos_publicados = list(POSTS_PUBLICADOS_DIR.glob("publicado_*.json"))
    
    # Ordenar por data de modificação (mais recentes primeiro)
    arquivos_publicados.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    # Pegar apenas os últimos 10
    ultimos_10 = arquivos_publicados[:10]
    
    if not ultimos_10:
        logger.info("Nenhum arquivo publicado encontrado")
        return
    
    logger.info(f"Encontrados {len(ultimos_10)} artigos publicados para sincronizar")
    
    # Sincronizar com Algolia
    resultados = sincronizar_com_algolia(ultimos_10)
    
    # Mostrar resultados
    logger.info("=== SINCRONIZAÇÃO CONCLUÍDA ===")
    logger.info(f"Artigos sincronizados com sucesso: {resultados['success_count']}")
    logger.info(f"Falhas na sincronização: {resultados['failed_count']}")
    
    if resultados.get('errors'):
        logger.error("Erros encontrados:")
        for error in resultados['errors']:
            logger.error(f"  - {error}")

if __name__ == "__main__":
    main()