#!/bin/bash
# Configurar o ambiente para os testes do fluxo simplificado

# Caminho absoluto para o diretório raiz do projeto
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Diretório do projeto: $PROJECT_ROOT"
echo "Configurando PYTHONPATH..."

# Exportar PYTHONPATH para incluir o diretório raiz
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Verificar se o Claude está disponível
which claude
if [ $? -eq 0 ]; then
    echo "✅ Claude CLI instalado: $(claude --version)"
else
    echo "❌ Claude CLI não encontrado! Certifique-se de que está instalado."
    exit 1
fi

# Criar pastas necessárias se não existirem
mkdir -p "$SCRIPT_DIR/posts_para_traduzir"
mkdir -p "$SCRIPT_DIR/posts_traduzidos"
mkdir -p "$SCRIPT_DIR/posts_formatados"
mkdir -p "$SCRIPT_DIR/posts_publicados"
mkdir -p "$SCRIPT_DIR/temp_test"

echo "Diretórios de trabalho criados."

# Executar o teste de integração
echo "Executando teste de integração..."
python "$SCRIPT_DIR/test_claude_integration.py"
TEST_RESULT=$?

if [ $TEST_RESULT -eq 0 ]; then
    echo "✅ Teste de integração bem-sucedido!"
    
    # Executar pipeline completo com um artigo de exemplo
    echo "Deseja executar o pipeline completo? (s/n)"
    read resposta
    
    if [ "$resposta" = "s" ]; then
        echo "Executando pipeline completo..."
        python "$SCRIPT_DIR/run_pipeline.py" --max-articles 1
    fi
else
    echo "❌ Teste de integração falhou!"
fi

exit $TEST_RESULT 