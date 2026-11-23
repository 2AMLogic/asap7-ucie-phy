# Shared tool-pin guard for the verification benches; sourced, never executed.
# Binds to the tool-versions.txt beside it and defines pin/die/check plus one
# probe per pinned host tool, with check_host_tools running all three. die()
# takes the calling bench's name from $0 and every refusal exits 2: the host
# is never changed to match a pin; a pin moves only by a reviewed change.
PIN="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/tool-versions.txt"

pin() { sed -n "s/^$1=//p" "$PIN"; }
die() { echo "$(basename "$0"): $*" >&2; exit 2; }

check() { # name installed
  local want; want="$(pin "$1")"
  [ "$2" = "$want" ] || die "$1 is '$2' but $PIN pins '$want'. Not changing host tools; fix the pin by a reviewed change or use the pinned tool."
}

check_yosys() { check yosys "$(yosys -V 2>/dev/null | awk '{print $2}' | sed 's/+.*//')"; }
check_verilator() { check verilator "$(verilator --version 2>/dev/null | awk '{print $2}')"; }
check_iverilog() { check iverilog "$(iverilog -V 2>/dev/null | head -1 | sed -n 's/.*version \([0-9.]*\).*/\1/p')"; }
check_host_tools() { check_yosys; check_verilator; check_iverilog; }
