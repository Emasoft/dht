#!/bin/bash
# Directory di questo script (…/project_root/DHT)
SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Directory di progetto = cartella superiore che contiene DHT
PROJECT_ROOT="$( cd -- "${SCRIPT_DIR}/.." &> /dev/null && pwd )"

# --- DHTL alias ---------------------------------------------------------
# azzera eventuali alias/path obsoleti
unalias dhtl 2>/dev/null || true
hash -d  dhtl 2>/dev/null || true   # zsh fix

# alias corretto → launcher nella root del progetto
alias dhtl="${PROJECT_ROOT}/DHT/dhtl.sh"
export -f dhtl 2>/dev/null || true  # compatibilità bash/zsh
