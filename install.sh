#!/usr/bin/env bash
# ==============================================================================
# ixsland Dynamic Island Installer for Linux (KDE Plasma 6 Wayland / X11)
# https://github.com/rezariski/ixsland
# ==============================================================================

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "  ██╗██╗  ██╗███████╗██╗      █████╗ ███╗   ██╗██████╗ "
echo "  ██║╚██╗██╔╝██╔════╝██║     ██╔══██╗████╗  ██║██╔══██╗"
echo "  ██║ ╚███╔╝ ███████╗██║     ███████║██╔██╗ ██║██║  ██║"
echo "  ██║ ██╔██╗ ╚════██║██║     ██╔══██║██║╚██╗██║██║  ██║"
echo "  ██║██╔╝ ██╗███████║███████╗██║  ██║██║ ╚████║██████╔╝"
echo "  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ "
echo -e "${NC}"
echo -e "${GREEN}==> Installing ixsland Dynamic Island on Linux...${NC}\n"

INSTALL_DIR="$HOME/.local/share/ixsland"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"

# 1. Dependency Check
echo -e "${CYAN}[1/4] Checking system dependencies...${NC}"
MISSING_DEPS=()

command -v python3 >/dev/null 2>&1 || MISSING_DEPS+=("python3")
python3 -c "import PyQt6" >/dev/null 2>&1 || MISSING_DEPS+=("python-pyqt6")
command -v wpctl >/dev/null 2>&1 || MISSING_DEPS+=("pipewire")

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    echo -e "${YELLOW}Warning: Missing required packages: ${MISSING_DEPS[*]}${NC}"
    if command -v pacman >/dev/null 2>&1; then
        echo -e "Install on Arch/CachyOS with:"
        echo -e "  ${GREEN}sudo pacman -S python python-pyqt6 pipewire wireplumber qt6-declarative${NC}\n"
    elif command -v apt >/dev/null 2>&1; then
        echo -e "Install on Debian/Ubuntu with:"
        echo -e "  ${GREEN}sudo apt install python3 python3-pyqt6 pipewire wireplumber${NC}\n"
    elif command -v dnf >/dev/null 2>&1; then
        echo -e "Install on Fedora with:"
        echo -e "  ${GREEN}sudo dnf install python3 python3-pyqt6 pipewire wireplumber${NC}\n"
    fi
else
    echo -e "${GREEN}✓ All core dependencies found!${NC}"
fi

# 2. Deploy Files
echo -e "\n${CYAN}[2/4] Deploying application files to ${INSTALL_DIR}...${NC}"
mkdir -p "$INSTALL_DIR"
cp -f ixsland.py "$INSTALL_DIR/ixsland.py"
cp -f run-demo.py "$INSTALL_DIR/run-demo.py" 2>/dev/null || true
chmod +x "$INSTALL_DIR/ixsland.py"
chmod +x "$INSTALL_DIR/run-demo.py" 2>/dev/null || true

# Copy default config if none exists
if [ ! -f "$INSTALL_DIR/config.json" ]; then
    if [ -f config.example.json ]; then
        cp config.example.json "$INSTALL_DIR/config.json"
        echo -e "${GREEN}✓ Default configuration created at ${INSTALL_DIR}/config.json${NC}"
    fi
fi

# 3. Configure Systemd User Service
echo -e "\n${CYAN}[3/4] Setting up systemd user service...${NC}"
mkdir -p "$SYSTEMD_USER_DIR"

cat <<EOF > "$SYSTEMD_USER_DIR/ixsland.service"
[Unit]
Description=ixsland Dynamic Island (Linux Native Port)
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
ExecStart=$INSTALL_DIR/ixsland.py
Restart=on-failure
RestartSec=3

[Install]
WantedBy=graphical-session.target
EOF

# 4. Activate Service
echo -e "\n${CYAN}[4/4] Activating ixsland service...${NC}"
systemctl --user daemon-reload
systemctl --user enable --now ixsland.service

echo -e "\n${GREEN}======================================================${NC}"
echo -e "${GREEN}  🎉 ixsland installed and launched successfully!${NC}"
echo -e "${GREEN}======================================================${NC}"
echo -e "• Dynamic Island is now running on your ${CYAN}Primary Display${NC}."
echo -e "• Check status:   ${YELLOW}systemctl --user status ixsland.service${NC}"
echo -e "• View logs:      ${YELLOW}journalctl --user -u ixsland -f${NC}"
echo -e "• Test features:  ${YELLOW}python3 ~/.local/share/ixsland/run-demo.py${NC}"
echo -e "• Configuration:  ${YELLOW}~/.local/share/ixsland/config.json${NC}\n"
