#!/usr/bin/env bash

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd -P)
PYTHON_CMD=${PYTHON_CMD:-"python3"}

cd "${SCRIPT_DIR}" || exit
${PYTHON_CMD} -c 'import sys; assert sys.version_info[0:2] >= (3,12)' || exit

${PYTHON_CMD} -m black src/
${PYTHON_CMD} -m pylint --disable=C,R,fixme src/
${PYTHON_CMD} -m mypy --enable-incomplete-feature=NewGenericSyntax src/
