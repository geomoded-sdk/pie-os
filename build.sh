#!/usr/bin/env bash
#=============================================================================
# Pie OS Build Script
# Cria a ISO personalizada do Pie OS para o console PieBox
# Baseado em Arch Linux com interface estilo Xbox 360
#=============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="${SCRIPT_DIR}/work"
OUT_DIR="${SCRIPT_DIR}/out"
AIROOTFS="${SCRIPT_DIR}/airootfs"
ARCHLIVE="${SCRIPT_DIR}/archlive"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[PIEOS]${NC} $1"; }
warn() { echo -e "${YELLOW}[AVISO]${NC} $1"; }
err()  { echo -e "${RED}[ERRO]${NC} $1"; exit 1; }

clean() {
    log "Limpando diretórios de trabalho..."
    rm -rf "${WORK_DIR}" "${OUT_DIR}"
}

check_deps() {
    local deps=("mkarchiso" "pacman" "xorriso" "mksquashfs")
    for dep in "${deps[@]}"; do
        if ! command -v "${dep}" &>/dev/null && ! command -v "/usr/bin/${dep}" &>/dev/null; then
            err "${dep} não encontrado. Instale archiso: sudo pacman -S archiso"
        fi
    done
    log "Dependências OK"
}

setup_airootfs() {
    log "Configurando sistema de arquivos raiz..."

    mkdir -p "${ARCHLIVE}/airootfs"
    cp -a "${AIROOTFS}/." "${ARCHLIVE}/airootfs/"

    # Instalar pacotes essenciais
    log "Pacotes base do Pie OS configurados"
}

build_iso() {
    log "Iniciando build da ISO..."

    local profile_dir="${ARCHLIVE}"
    if [ ! -f "${profile_dir}/profiledef.sh" ]; then
        err "profiledef.sh não encontrado em ${profile_dir}"
    fi

    mkdir -p "${OUT_DIR}"

    log "Executando mkarchiso..."
    mkarchiso -v -w "${WORK_DIR}" -o "${OUT_DIR}" "${profile_dir}"

    if [ $? -eq 0 ]; then
        log "ISO gerada com sucesso em: ${OUT_DIR}"
        ls -lh "${OUT_DIR}"/*.iso
    else
        err "Falha ao gerar ISO. Verifique os logs."
    fi
}

post_build() {
    local iso_file=$(ls "${OUT_DIR}"/*.iso 2>/dev/null | head -1)
    if [ -n "${iso_file}" ]; then
        log "ISO: ${iso_file}"
        log "Tamanho: $(du -h "${iso_file}" | cut -f1)"
        log ""
        log "Para gravar em USB (Linux):"
        log "  sudo dd if=${iso_file} of=/dev/sdX bs=4M status=progress"
        log ""
        log "Para gravar em USB (Windows):"
        log "  Use Rufus (modo DD) ou balenaEtcher"
    fi
}

install_to_disk() {
    local disk="$1"
    if [ -z "${disk}" ]; then
        err "Especifique o disco: sudo ./build.sh install /dev/sdX"
    fi
    log "Instalando Pie OS em ${disk}..."
    warn "ISSO VAI APAGAR TODOS OS DADOS EM ${disk}!"
    read -rp "Tem certeza? (yes/N): " confirm
    if [ "${confirm}" != "yes" ]; then
        log "Instalação cancelada."
        exit 0
    fi

    local iso_file=$(ls "${OUT_DIR}"/*.iso 2>/dev/null | head -1)
    if [ -z "${iso_file}" ]; then
        log "ISO não encontrada. Execute primeiro: sudo ./build.sh build"
        exit 1
    fi

    log "Gravando ISO em ${disk}..."
    sudo dd if="${iso_file}" of="${disk}" bs=4M status=progress
    sync
    log "Instalação concluída! Conecte o disco no PieBox e ligue."
}

case "${1:-build}" in
    clean)
        clean
        ;;
    build)
        check_deps
        clean
        setup_airootfs
        build_iso
        post_build
        ;;
    install)
        install_to_disk "${2:-}"
        ;;
    *)
        echo "Uso: ${0} {build|clean|install /dev/sdX}"
        echo ""
        echo "  build        - Gera a ISO do Pie OS"
        echo "  clean        - Limpa arquivos temporários"
        echo "  install /dev/sdX - Grava ISO em disco/USB"
        exit 1
        ;;
esac
