# Fluxo Simplificado com Claude Code

Este módulo implementa um fluxo de processamento e tradução de artigos utilizando o Claude Code como motor de tradução e formatação, sem depender de APIs pagas de terceiros.

## 📋 Estrutura

```
fluxo_simplificado/
├── claude_connector.py      # Conector principal para o Claude Code
├── traduzir_artigo.py       # Script de demonstração
├── run_tests.sh             # Script para executar testes
├── posts_para_traduzir/     # Artigos originais em inglês
├── posts_traduzidos/        # Artigos traduzidos para português
├── posts_formatados/        # Artigos formatados para o Sanity
└── temp_test/               # Diretório para testes temporários
```

## 🚀 Funcionalidades

- **Tradução de artigos**: Inglês → Português brasileiro com Claude Code
- **Formatação para Sanity**: Converte artigos para o formato Portable Text do Sanity CMS
- **Geração de resumos**: Cria resumos concisos de artigos
- **Validação de saída**: Verifica se os resultados são válidos e completos

## 🔧 Requisitos

- Python 3.9+
- Claude CLI (https://www.anthropic.com/claude-code-cli)
- Acesso à internet e à API Claude

## 📦 Instalação

1. Certifique-se de ter o Claude CLI instalado:
```bash
curl -1sLf https://cli.claude.ai/install.sh | sh
```

2. Verifique a instalação do Claude:
```bash
claude --version
```

## 🧪 Testes

Execute os testes de integração com o Claude:

```bash
./run_tests.sh
```

Ou teste cada componente individualmente:

```bash
# Testar apenas o conector
./claude_connector.py

# Executar demonstração completa
./traduzir_artigo.py
```

## 🌟 Exemplo de Uso

```python
from claude_connector import traduzir, resumir, formatar_para_sanity

# Traduzir texto
texto_en = "Artificial Intelligence is transforming the world."
texto_pt = traduzir(texto_en)

# Criar resumo
resumo = resumir(texto_longo, max_palavras=50)

# Formatar para Sanity
documento = formatar_para_sanity(
    titulo="Título do artigo", 
    conteudo="Conteúdo completo", 
    resumo="Resumo breve",
    fonte="Nome da fonte",
    link="https://exemplo.com/artigo"
)
```

## 📂 Fluxo de Trabalho

1. Os artigos em inglês são colocados em `posts_para_traduzir/`
2. O script processa e traduz usando o Claude Code
3. Os artigos traduzidos são salvos em `posts_traduzidos/`
4. Os artigos formatados para o Sanity são salvos em `posts_formatados/`
5. Estes podem ser publicados diretamente no Sanity CMS

## 🔄 Integração com o Fluxo Completo

Este módulo pode funcionar de forma independente ou integrado ao fluxo completo do CrewAI. Para integração, consulte a documentação principal do projeto.

## 📊 Limitações

- Dependente do Claude CLI, que pode ter limites de uso ou cotas
- Tradução sequencial (não paralela) para evitar sobrecarga da API
- Formatação limitada às capacidades atuais do Claude

## 🔮 Futuras Melhorias

- Implementar processamento em lote (batch)
- Adicionar suporte a mais idiomas
- Integrar verificação automática de qualidade da tradução
- Adicionar suporte a conteúdo multimídia 