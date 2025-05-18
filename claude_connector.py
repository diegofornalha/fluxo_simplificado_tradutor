#!/usr/bin/env python3
"""
Conector simplificado para o Claude Code
Facilita a integração do Claude no fluxo simplificado
"""

import os
import subprocess
import json
import re
import logging
from pathlib import Path
import time

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("claude_connector")

class ClaudeConnector:
    """Conector simplificado para o Claude Code CLI"""
    
    def __init__(self, claude_path="claude", timeout=60):
        self.claude_path = claude_path
        self.timeout = timeout
        self.verify_claude()
    
    def verify_claude(self):
        """Verifica se o Claude CLI está disponível"""
        try:
            result = subprocess.run(
                [self.claude_path, "--version"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            
            if result.returncode == 0:
                logger.info(f"Claude CLI disponível: {result.stdout.strip()}")
                return True
            else:
                logger.error(f"Claude CLI não está acessível: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Erro ao verificar Claude CLI: {str(e)}")
            return False
    
    def send_prompt(self, prompt, retries=2, retry_delay=3):
        """Envia um prompt para o Claude e retorna a resposta"""
        for attempt in range(retries + 1):
            try:
                # Escapar aspas duplas
                escaped_prompt = prompt.replace('"', '\\"')
                
                # Construir o comando
                cmd = f'{self.claude_path} -p "{escaped_prompt}"'
                
                # Executar o comando
                result = subprocess.run(
                    cmd,
                    shell=True,
                    text=True,
                    capture_output=True,
                    timeout=self.timeout
                )
                
                # Verificar se houve erro na execução
                if result.returncode != 0:
                    logger.error(f"Erro na execução do Claude: {result.stderr}")
                    if attempt < retries:
                        logger.info(f"Tentando novamente em {retry_delay} segundos...")
                        time.sleep(retry_delay)
                        continue
                    return f"ERRO: {result.stderr}"
                
                # Processar e retornar a resposta
                return result.stdout.strip()
                
            except subprocess.TimeoutExpired:
                logger.error(f"Timeout ao aguardar resposta do Claude (limite: {self.timeout}s)")
                if attempt < retries:
                    logger.info(f"Tentando novamente em {retry_delay} segundos...")
                    time.sleep(retry_delay)
                    continue
                return "ERRO: A resposta demorou muito tempo."
                
            except Exception as e:
                logger.error(f"Erro inesperado: {str(e)}")
                if attempt < retries:
                    logger.info(f"Tentando novamente em {retry_delay} segundos...")
                    time.sleep(retry_delay)
                    continue
                return f"ERRO: {str(e)}"
    
    def extract_json(self, text):
        """Extrai um objeto JSON de uma resposta"""
        json_match = re.search(r'({[\s\S]*?})(?:\s*\n|$)', text)
        if not json_match:
            json_match = re.search(r'(\[[\s\S]*?\])(?:\s*\n|$)', text)
            
        if json_match:
            try:
                json_text = json_match.group(1)
                return json.loads(json_text)
            except json.JSONDecodeError:
                logger.error("Falha ao decodificar JSON da resposta")
                return None
        return None
    
    def traduzir(self, texto):
        """Traduz um texto do inglês para o português brasileiro"""
        prompt = f"""
        Traduza o seguinte texto do inglês para o português brasileiro:
        
        "{texto}"
        
        Traduza de forma natural, mantendo o significado original.
        Responda apenas com o texto traduzido, sem explicações.
        """
        
        return self.send_prompt(prompt)
    
    def resumir(self, texto, max_palavras=100):
        """Resume um texto, mantendo as informações principais"""
        prompt = f"""
        Resuma o seguinte texto em não mais que {max_palavras} palavras.
        Mantenha as informações mais importantes e o tom original:
        
        "{texto}"
        
        Responda apenas com o resumo, sem explicações.
        """
        
        return self.send_prompt(prompt)
    
    def formatar_json(self, dados, schema_exemplo):
        """Formata dados em um JSON seguindo um schema específico"""
        prompt = f"""
        Converta os seguintes dados para o formato JSON especificado no exemplo.
        
        DADOS:
        {dados}
        
        FORMATO ESPERADO:
        {schema_exemplo}
        
        Responda apenas com o JSON formatado, sem explicações.
        """
        
        resposta = self.send_prompt(prompt)
        return self.extract_json(resposta)
    
    def formatar_para_sanity(self, titulo, conteudo, resumo="", fonte="", link=""):
        """Formata um artigo para o schema do Sanity CMS"""
        prompt = f"""
        Converta o seguinte artigo para o formato Portable Text do Sanity CMS:
        
        TÍTULO: {titulo}
        
        RESUMO: {resumo}
        
        CONTEÚDO: {conteudo}
        
        FONTE: {fonte}
        
        LINK: {link}
        
        O formato deve seguir exatamente este schema:
        ```json
        {{
          "_type": "post",
          "title": "Título do artigo",
          "slug": {{
            "_type": "slug",
            "current": "titulo-do-artigo" // slug em minúsculas, sem acentos, espaços como traços
          }},
          "publishedAt": "2023-05-18T12:34:56Z", // data atual ISO
          "excerpt": "Resumo breve do post (máximo 299 caracteres)",
          "content": [
            {{
              "_type": "block",
              "_key": "randomKey1", // gere chaves aleatórias
              "style": "normal",
              "markDefs": [],
              "children": [
                {{
                  "_type": "span",
                  "_key": "randomKey2", // gere chaves aleatórias
                  "text": "Texto do parágrafo",
                  "marks": []
                }}
              ]
            }},
            // Cada parágrafo deve ser um bloco separado
          ],
          "originalSource": {{
            "url": "https://site-original.com/artigo",
            "title": "Título Original",
            "site": "Nome do Site"
          }}
        }}
        ```
        
        IMPORTANTE:
        1. Gere um slug removendo acentos, convertendo para minúsculas, e substituindo espaços por traços
        2. Divida o conteúdo em blocos separados para cada parágrafo
        3. Gere chaves aleatórias (_key) para cada bloco e span
        4. O resumo deve ter no máximo 299 caracteres
        
        Responda apenas com o JSON formatado, sem explicações.
        """
        
        resposta = self.send_prompt(prompt)
        return self.extract_json(resposta)

# Instância global para uso fácil
claude = ClaudeConnector()

# Funções auxiliares para uso direto
def traduzir(texto):
    """Traduz um texto para português brasileiro"""
    return claude.traduzir(texto)

def resumir(texto, max_palavras=100):
    """Resume um texto"""
    return claude.resumir(texto, max_palavras)

def formatar_para_sanity(titulo, conteudo, resumo="", fonte="", link=""):
    """Formata artigo para Sanity"""
    return claude.formatar_para_sanity(titulo, conteudo, resumo, fonte, link)

# Exemplo de uso
if __name__ == "__main__":
    # Testar se está funcionando
    logger.info("Testando o conector Claude...")
    
    # Texto de exemplo
    texto = "The Future of AI is bright. Artificial Intelligence will change how we live and work."
    
    # Traduzir
    traducao = traduzir(texto)
    logger.info(f"Tradução: {traducao}")
    
    # Resumir
    resumo = resumir(texto, 10)
    logger.info(f"Resumo: {resumo}")
    
    logger.info("Testes concluídos!") 