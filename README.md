# Pie OS 🍰

**Console System para PieBox** — Interface estilo Xbox 360, baseado em Arch Linux.

## Requisitos

| Componente | Especificação |
|------------|---------------|
| CPU | Intel Core i3 (Sandy Bridge+) |
| GPU | Intel HD Graphics 3000 |
| RAM | 2GB+ |
| Armazenamento | 16GB+ (SSD recomendado) |
| Controles | USB ou Wireless (Xbox, PS, genéricos) |
| WiFi | Qualquer adaptador compatível com Linux |

## Funcionalidades

- 🎮 Interface Xbox 360 Blades (navegação por guias)
- 📦 Execução direta de **.AppImage**
- 🎮 Execução de **.xex** via Xenia Canary
- 🎮 Suporte universal a gamepads (USB/Wireless)
- 📶 WiFi integrado
- ⚡ Otimizado para Intel HD Graphics 3000
- 🟢 Tema claro/verde (mínimo de azul)
- 🚀 Boot animation personalizada (Plymouth)

## Build

### Pré-requisitos (Linux)

```bash
sudo pacman -S archiso git base-devel
```

### Gerar ISO

```bash
git clone [seu-repo] pieos
cd pieos
sudo ./build.sh build
```

A ISO será gerada em `out/`.

### Instalar em USB/Disco

```bash
sudo ./build.sh install /dev/sdX   # cuidado! apaga tudo em /dev/sdX
```

Ou use **Rufus** (modo DD) ou **balenaEtcher** no Windows.

## Estrutura

```
pieos/
├── build.sh              # Script de build
├── archlive/             # Perfil ArchISO
│   ├── profiledef.sh
│   └── pacman.conf
├── airootfs/             # Overlay do sistema de arquivos
│   ├── etc/
│   │   ├── systemd/system/pieos.target
│   │   └── udev/rules.d/99-joystick.rules
│   └── usr/
│       ├── bin/pieos-launcher
│       ├── bin/xenia-run
│       └── share/plymouth/themes/pieos/
├── ui/pieos-shell/       # Interface gráfica (PyQt5)
│   ├── main.py
│   └── styles/xbox360.qss
└── configs/
```

## Atalhos

| Tecla | Ação |
|-------|------|
| F1 | Guia Início |
| F2 | Guia Jogos |
| F3 | Guia Configurações |
| ← → | Navegar guias |
| Esc | Voltar ao início |
| F12 | Desligar console |

**Gamepad:** A=OK  B=Voltar  LB/RB=Trocar guia  Guide=Início

## Personalização

- Tema padrão: verde claro (`#A8D854`)
- Boot animation: edite `airootfs/usr/share/plymouth/themes/pieos/`
- Adicione seu logo em `pieos.plymouth` e coloque `logo.png` no mesmo diretório

---

**PieBox Systems** — 2026
