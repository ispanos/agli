#!/usr/bin/env sh

# sudo install -Dm755 sway-ptinopedila.sh /usr/local/bin/sway-ptinopedila
# sudo install -Dm644 "sway-ptinopedila.desktop" "/usr/share/wayland-sessions/sway-ptinopedila.desktop"

# Source profile (lifted from some gnome stuff)
if [ "x$XDG_SESSION_TYPE" = "xwayland" ] &&
  [ "x$XDG_SESSION_CLASS" != "xgreeter" ] &&
  [  -n "$SHELL" ] &&
  grep -q "$SHELL" /etc/shells &&
  ! (echo "$SHELL" | grep -q "false") &&
  ! (echo "$SHELL" | grep -q "nologin"); then
  if [ "$1" != '-l' ]; then
    exec bash -c "exec -l '$SHELL' -c '$0 -l $*'"
  else
    shift
  fi
fi

export EDITOR="code"
export TERMINAL="alacritty"
export BROWSER="firefox"

# Set WLRoots renderer to Vulkan to avoid flickering (if you can make it work)
# export WLR_RENDERER=vulkan

export XDG_CURRENT_DESKTOP=sway

appendpath () {
	case ":$PATH:" in
		*:"$1":*)
			;;
		*)
			PATH="${PATH:+$PATH:}$1"
	esac
}

[ -d "$HOME/.local/bin/wm-scripts" ] && appendpath "$HOME/.local/bin/wm-scripts"
unset appendpath

# General wayland environment variables
export XDG_SESSION_TYPE=wayland
export QT_QPA_PLATFORM=wayland
export QT_WAYLAND_DISABLE_WINDOWDECORATION=1
# Firefox wayland environment variable
export MOZ_ENABLE_WAYLAND=1
export MOZ_USE_XINPUT2=1

# noscanout fixes this issue: https://www.reddit.com/r/swaywm/comments/wiq06i/games_have_lines_on_screen_when_fullscreen_on/
# exec sway -D noscanout "$@"
lspci -k | sgrep -A 2 -E "(VGA|3D)" | grep -q "NVIDIA" &&
exec sway --unsupported-gpu "$@"

exec sway "$@"
