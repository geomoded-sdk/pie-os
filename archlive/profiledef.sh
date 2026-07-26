#!/usr/bin/env bash
# Pie OS - Profile definition for mkarchiso

set -euo pipefail

iso_name="pieos"
iso_label="PIEOS"
iso_publisher="PieBox Systems"
iso_application="Pie OS - Console Operating System"
iso_version="1.0.0"
install_dir="arch"
buildmodes=('iso')
bootmodes=('bios.grub')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'xz' '-Xbcj' 'x86' '-b' '1M')
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/etc/gshadow"]="0:0:400"
  ["/root"]="0:0:750"
  ["/usr/bin/pieos-launcher"]="0:0:755"
  ["/usr/bin/xenia-run"]="0:0:755"
)
