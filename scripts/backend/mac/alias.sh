#!/bin/bash
echo "=============================================="
echo "Configurando Alias para la Consola (Bash/Zsh)..."
echo "=============================================="

# Obtener el directorio absoluto del script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Definir los alias
alias CA_install="bash $DIR/venv.sh"
alias CA_run="bash $DIR/run.sh"
alias CA_export="bash $DIR/export.sh"

echo "Alias creados para esta sesión de terminal:"
echo "  - CA_install : Ejecuta scripts/backend/mac/venv.sh"
echo "  - CA_run     : Ejecuta scripts/backend/mac/run.sh"
echo "  - CA_export  : Ejecuta scripts/backend/mac/export.sh"
echo ""
echo "NOTA: Para hacer uso de estos alias, debes 'sourcear' este script:"
echo "  source scripts/backend/mac/alias.sh"
echo ""
echo "Para hacerlos permanentes, puedes agregarlos a tu ~/.zshrc o ~/.bash_profile:"
echo "  alias CA_install=\"bash $DIR/venv.sh\""
echo "  alias CA_run=\"bash $DIR/run.sh\""
echo "  alias CA_export=\"bash $DIR/export.sh\""
echo "=============================================="
