#!/usr/bin/env bash
set -euo pipefail
SKILLS_DIR="${HOME}/.claude/skills"
TARGET="${SKILLS_DIR}/project-due-diligence"
SRC="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "${SKILLS_DIR}"
if [ -L "${TARGET}" ]; then rm "${TARGET}"; fi
if [ -e "${TARGET}" ]; then
  echo "拒绝：${TARGET} 已存在且不是软链，请手动处理" >&2; exit 1
fi
ln -s "${SRC}" "${TARGET}"
echo "已安装：${TARGET} -> ${SRC}"
echo "验证：ls -l ${TARGET}/SKILL.md"
