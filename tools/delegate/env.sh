# Sourced by the job scripts and by llm-router/scripts/ralph.sh: one place that knows WSL vs Windows (Git Bash).
# Jobs live in $HOME/work/<id>; the WSL home and the Windows home are separate, so job ids do not collide.
case "$(uname -s)" in
  MINGW*|MSYS*) DG_WIN=1; DG_LL=/c/Users/mda/llm-router; DG_SRC=/c/Users/mda/games/Yu-Gi-Oh-Forbidden-Memories-Recompiled
                DG_PY=python; DG_OC=opencode; DG_OCCFG=opencode-ralph-win.json ;;
  *)            DG_WIN=0; DG_LL=/mnt/c/Users/mda/llm-router; DG_SRC=/mnt/c/Users/mda/games/Yu-Gi-Oh-Forbidden-Memories-Recompiled
                DG_PY=python3; DG_OC="$HOME/.opencode/bin/opencode"; DG_OCCFG=opencode-ralph.json ;;
esac
export DG_WIN DG_LL DG_SRC DG_PY DG_OC DG_OCCFG
