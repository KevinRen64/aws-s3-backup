from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List
import fnmatch

@dataclass(frozen=True)
class FileItem:
  path: Path      # local absolute path
  rel: str        # local relative path (posix)
  size: int
  mtime: int      # epoch seconds

def iter_files(root: Path, excludes: List[str]) -> Iterable[FileItem]:
  root = root.resolve()
  for p in root.rglob("*"):
    if p.is_dir():
      continue
    rel = p.relative_to(root).as_posix()
    if is_excluded(rel, excludes):
      continue
    st = p.stat()
    yield FileItem(path=p, rel=rel, size=int(st.st_size), mtime=int(st.st_mtime))

def is_excluded(rel_posix: str, excludes: List[str]) -> bool:
  for pattern in excludes:
    # patterns like "*.log", "node_modules/*", "tmp/**"
    if fnmatch.fnmatch(rel_posix, pattern):
      return True
  return False

def join_s3_key(prefix: str, rel_posix:str) -> str:
  prefix = (prefix or "").strip("/")
  if not prefix:
    return rel_posix
  return f"{prefix}/{rel_posix}"