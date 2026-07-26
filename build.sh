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
    local deps=("mkarchiso" "xorriso" "mksquashfs")
    for dep in "${deps[@]}"; do
        if ! command -v "${dep}" &>/dev/null && ! command -v "/usr/bin/${dep}" &>/dev/null; then
            err "${dep} não encontrado. Instale archiso e grub: sudo pacman -S archiso grub"
        fi
    done
    log "Dependências OK"
}

setup_airootfs() {
    log "Configurando sistema de arquivos raiz..."

    rm -rf "${ARCHLIVE}/airootfs"
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
    set +e
    mkarchiso -v -w "${WORK_DIR}" -o "${OUT_DIR}" "${profile_dir}" 2>&1
    local rc=$?
    set -e
    if [ $rc -eq 0 ]; then
        local iso_file=$(ls "${OUT_DIR}"/*.iso 2>/dev/null | head -1)
        log "ISO gerada com sucesso: ${iso_file}"
        log "Tamanho: $(du -h "${iso_file}" | cut -f1)"
        log "Boot mode: bios.syslinux"
        log ""
        log "Para gravar em USB, use balenaEtcher ou:"
        log "  sudo dd if=${iso_file} of=/dev/sdX bs=4M status=progress"
    else
        log "Debug: listando diretórios de trabalho..."
        find "${WORK_DIR}" -type d -maxdepth 4 2>/dev/null | head -30
        echo "---"
        ls -la "${WORK_DIR}/x86_64/" 2>/dev/null || echo "x86_64 dir nao existe"
        if [ -d "${WORK_DIR}/x86_64/boot/grub" ]; then
            echo "GRUB CONFIG:"
            cat "${WORK_DIR}/x86_64/boot/grub/grub.cfg" 2>/dev/null || echo "sem grub.cfg"
        fi
        err "Falha no mkarchiso (veja logs acima)"
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
