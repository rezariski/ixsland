#!/usr/bin/env bash
# ==============================================================================
# ixsland Dynamic Island Uninstaller
# https://github.com/rezariski/ixsland
# ==============================================================================

set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}==> Stopping and removing ixsland Dynamic Island...${NC}"

# Stop systemd service
if systemctl --user is-active --quiet ixsland.service 2>/dev/null; then
    systemctl --user stop ixsland.service
    echo -e "${GREEN}✓ Stopped ixsland service.${NC}"
fi

systemctl --user disable ixsland.service 2>/dev/null || true
rm -f "$HOME/.config/systemd/user/ixsland.service"
systemctl --user daemon-reload

# Remove app files
rm -rf "$HOME/.local/share/ixsland"
echo -e "${GREEN}✓ Removed files from ~/.local/share/ixsland.${NC}"

echo -e "\n${GREEN}ixsland has been completely uninstalled from your system.${NC}"
