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
    local deps=("mkarchiso" "pacman" "xorriso" "mksquashfs" "grub-mkrescue")
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
        log "ISO gerada com sucesso em: ${OUT_DIR}"
        ls -lh "${OUT_DIR}"/*.iso
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

create_hybrid_grub_iso() {
    local bios_iso="$1"
    local work_dir="${WORK_DIR}/hybrid"
    local hybrid_iso="${OUT_DIR}/pieos-hybrid.iso"

    log "Criando ISO híbrida BIOS+UEFI com GRUB..."
    log "Fonte: ${bios_iso}"

    rm -rf "${work_dir}"
    mkdir -p "${work_dir}/iso"

    # Extrair o volume ID da ISO original
    local iso_label
    iso_label=$(xorriso -indev "${bios_iso}" -report_el_torito 2>/dev/null | grep "Volume Id" | awk -F': ' '{print $2}' | tr -d "'")
    if [ -z "${iso_label}" ]; then
        iso_label="PIEOS"
        warn "Não foi possível extrair volume ID, usando: ${iso_label}"
    fi
    log "Volume ID: ${iso_label}"

    # Extrair conteúdo da ISO BIOS
    log "Extraindo conteúdo da ISO..."
    xorriso -osirrox on -indev "${bios_iso}" -extract / "${work_dir}/iso/" 2>&1
    log "Conteúdo extraído para ${work_dir}/iso"

    # Garantir diretório do GRUB
    mkdir -p "${work_dir}/iso/boot/grub"

    # Copiar nossa config GRUB customizada
    if [ -f "${SCRIPT_DIR}/archlive/grub/grub.cfg" ]; then
        cp "${SCRIPT_DIR}/archlive/grub/grub.cfg" "${work_dir}/iso/boot/grub/"
        log "GRUB config copiada para /boot/grub/grub.cfg"
    else
        warn "grub.cfg não encontrado em archlive/grub/"

        # Gerar config GRUB padrão para archiso
        cat > "${work_dir}/iso/boot/grub/grub.cfg" << 'GRUBEOF'
set default="pieos"
set timeout=10
set gfxpayload=keep

insmod all_video
insmod usb
insmod usb_keyboard
insmod part_gpt
insmod part_msdos
insmod ext2
insmod fat
insmod iso9660
insmod loopback
insmod search
insmod search_fs_label

search --no-floppy --set=root --label PIEOS

menuentry "Pie OS" {
    linux /arch/boot/x86_64/vmlinuz-linux archisobasedir=arch archisolabel=PIEOS loglevel=3 i915.modeset=1
    initrd /arch/boot/x86_64/intel-ucode.img /arch/boot/x86_64/initramfs-linux.img
}

menuentry "Pie OS (modo seguro)" {
    linux /arch/boot/x86_64/vmlinuz-linux archisobasedir=arch archisolabel=PIEOS loglevel=3 nomodeset
    initrd /arch/boot/x86_64/intel-ucode.img /arch/boot/x86_64/initramfs-linux.img
}

menuentry "Desligar" { halt }
menuentry "Reiniciar" { reboot }
GRUBEOF
        log "Config GRUB gerada automaticamente"
    fi

    # Criar ISO híbrida com GRUB (BIOS+UEFI)
    log "Criando ISO híbrida com grub-mkrescue..."
    grub-mkrescue -o "${hybrid_iso}" "${work_dir}/iso/" \
        -- -volid "${iso_label}" \
           -publisher "PieBox Systems" \
           -appid "Pie OS - Console System" \
           -volset "Pie OS" 2>&1

    if [ ! -f "${hybrid_iso}" ]; then
        err "Falha ao criar ISO híbrida com grub-mkrescue"
    fi

    log "ISO híbrida criada: ${hybrid_iso}"
    ls -lh "${hybrid_iso}"

    # Substituir ISO original pela híbrida
    rm -f "${bios_iso}"
    mv "${hybrid_iso}" "${bios_iso}"
    log "ISO híbrida (BIOS+UEFI/GRUB) salva como: ${bios_iso}"
}

post_build() {
    local iso_file=$(ls "${OUT_DIR}"/*.iso 2>/dev/null | head -1)
    if [ -n "${iso_file}" ]; then
        log "ISO original (BIOS/syslinux): ${iso_file}"
        log "Tamanho: $(du -h "${iso_file}" | cut -f1)"

        # Criar ISO híbrida com GRUB
        create_hybrid_grub_iso "${iso_file}"

        log ""
        log "ISO final com GRUB (BIOS+UEFI):"
        log "  ${iso_file}"
        log "  Tamanho: $(du -h "${iso_file}" | cut -f1)"
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
