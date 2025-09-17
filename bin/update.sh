#!/usr/bin/env bash

ROOT_DIR=$(cd $(dirname $0)/.. && pwd)
BIN_DIR="${ROOT_DIR}/bin"
ETC_DIR="${ROOT_DIR}/etc"
LIB_DIR="${ROOT_DIR}/lib"

export PYTHONPATH="${ETC_DIR}:${LIB_DIR}"
exec python3 "${LIB_DIR}/update.py" \
    --root="${ROOT_DIR}" \
    "$@"
