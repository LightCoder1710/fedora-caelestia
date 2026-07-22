#!/usr/bin/env bash

set -e

echo "=========================================================="
echo "🚀 HỆ THỐNG TỰ ĐỘNG CÀI ĐẶT HYPRLAND + CAELESTIA + FCITX5"
echo "=========================================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1. Cập nhật hệ thống & RPM Fusion
echo "📦 1. Đang kiểm tra và cài đặt RPM Fusion..."
sudo dnf update -y
sudo dnf install -y https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm || true

# 2. Cài đặt các phần mềm và gói phụ thuộc
echo "📦 2. Đang cài đặt Hyprland, Fcitx5 (Bộ gõ tiếng Việt) và các công cụ Wayland..."
sudo dnf install -y \
    hyprland \
    kitty \
    waybar \
    rofi-wayland \
    dunst \
    grim \
    slurp \
    wl-clipboard \
    polkit-gnome \
    qt5-qtwayland \
    qt6-qtwayland \
    brightnessctl \
    pamixer \
    playerctl \
    fastfetch \
    fish \
    btop \
    starship \
    qt5ct \
    qt6ct \
    fcitx5 \
    fcitx5-autostart \
    fcitx5-bamboo \
    fcitx5-gtk \
    fcitx5-qt \
    curl \
    unzip \
    git \
    rsync

# 3. Cài đặt JetBrainsMono Nerd Font nếu chưa có
FONT_DIR="$HOME/.local/share/fonts"
mkdir -p "$FONT_DIR"

if [ ! -d "$FONT_DIR/JetBrainsMono" ] && [ ! -d "$FONT_DIR/JetBrainsMonoNerd" ]; then
    echo "🔤 3. Đang tải và cài đặt JetBrainsMono Nerd Font..."
    TEMP_FONT_DIR="$(mktemp -d)"
    curl -fLo "$TEMP_FONT_DIR/JetBrainsMono.zip" https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.zip
    unzip -q "$TEMP_FONT_DIR/JetBrainsMono.zip" -d "$FONT_DIR/JetBrainsMonoNerd"
    rm -rf "$TEMP_FONT_DIR"
fi

# 4. Sao chép Font tùy chỉnh (MaterialYou)
if [ -d "$SCRIPT_DIR/dotfiles/.local/share/fonts" ]; then
    echo "🔤 4. Đang cài đặt font giao diện Caelestia..."
    cp -rf "$SCRIPT_DIR/dotfiles/.local/share/fonts/"* "$FONT_DIR/" 2>/dev/null || true
fi

# 5. Sao chép dữ liệu Caelestia & Configs
echo "⚙️ 5. Đang sao chép các cấu hình Caelestia, Quickshell & Fcitx5..."
mkdir -p "$HOME/.config" "$HOME/.local/share"

if [ -d "$SCRIPT_DIR/dotfiles/.local/share/caelestia" ]; then
    mkdir -p "$HOME/.local/share/caelestia"
    rsync -av --exclude='.git' "$SCRIPT_DIR/dotfiles/.local/share/caelestia/" "$HOME/.local/share/caelestia/"
fi

if [ -d "$SCRIPT_DIR/dotfiles/.config" ]; then
    cp -rf "$SCRIPT_DIR/dotfiles/.config/"* "$HOME/.config/"
fi

# 6. Tạo các Symlinks liên kết cho Caelestia
echo "🔗 6. Đang liên kết cấu hình Caelestia..."
CAELESTIA_DIR="$HOME/.local/share/caelestia"

create_symlink() {
    local target="$1"
    local link="$2"
    if [ -e "$target" ]; then
        rm -rf "$link"
        ln -s "$target" "$link"
    fi
}

create_symlink "$CAELESTIA_DIR/hypr" "$HOME/.config/hypr"
create_symlink "$CAELESTIA_DIR/btop" "$HOME/.config/btop"
create_symlink "$CAELESTIA_DIR/fastfetch" "$HOME/.config/fastfetch"
create_symlink "$CAELESTIA_DIR/fish" "$HOME/.config/fish"
create_symlink "$CAELESTIA_DIR/foot" "$HOME/.config/foot"
create_symlink "$CAELESTIA_DIR/qt5ct" "$HOME/.config/qt5ct"
create_symlink "$CAELESTIA_DIR/qt6ct" "$HOME/.config/qt6ct"
create_symlink "$CAELESTIA_DIR/starship.toml" "$HOME/.config/starship.toml"
create_symlink "$CAELESTIA_DIR/uwsm" "$HOME/.config/uwsm"
create_symlink "$CAELESTIA_DIR/vscode/flags.conf" "$HOME/.config/code-flags.conf"

# 7. Đảm bảo cấu hình gõ tiếng Việt Fcitx5 trong Hyprland
HYPR_VARS="$HOME/.config/caelestia/hypr-vars.conf"
if [ -f "$HYPR_VARS" ]; then
    if ! grep -q "FCITX5_CONFIGURED" "$HYPR_VARS"; then
        cat << 'ENVEOF' >> "$HYPR_VARS"

# --- FCITX5_CONFIGURED: Cấu hình gõ tiếng Việt ---
env = XMODIFIERS, @im=fcitx
env = QT_IM_MODULE, fcitx
env = GTK_IM_MODULE, fcitx
exec-once = fcitx5 -d -r
ENVEOF
    fi
fi

# 8. Cập nhật Cache Font
echo "🔄 8. Cập nhật cache font chữ..."
fc-cache -fv

echo "=========================================================="
echo "🎉 TẤT CẢ ĐÃ CÀI ĐẶT HOÀN TẤT!"
echo "👉 Hãy Log out hoặc Reboot máy, sau đó chọn đăng nhập phiên Hyprland."
echo "=========================================================="
