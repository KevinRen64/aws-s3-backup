from __future__ import annotations
import argparse
import json
import logging
from pathlib import Path
from typing import List, Optional

from . import __version__
from .utils import iter_files, join_s3_key
from .s3 import s3_client, head_object_etag_size_mtime, upload_file, list_objects_keys, delete_object, validate_creds

EXIT_OK = 0
EXIT_ERROR = 2

def build_parser() -> argparse.ArgumentParser:
  p = argparse.ArgumentParser(
    prog="s3-backup",
    description="Production-ready S3 backup/sync CLI using boto3."
  )
  p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
  p.add_argument("--profile", default=None, help="AWS profile name (optional).")
  p.add_argument("--region", default="ap-southeast-2", help="AWS region (default: ap-southeast-2).")
  p.add_argument("--json", action="store_true", help="Output JSON report.")
  p.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")

  sub = p.add_subparsers(dest="cmd", required=True)

  sync = sub.add_parser("sync", help="Sync a local folder to S3 prefix.")
  sync.add_argument("local_dir", help="Local directory to upload.")
  sync.add_argument("s3_uri", help="S3 target like s3://bucket/prefix")
  sync.add_argument("--exclude", action="append", default=[], help="Exclude pattern(repeatable), e.g. *.log or tmp/*")
  sync.add_argument("--dry-run", action="store_true", help="Show actions without uploading/deleting.")
  sync.add_argument("--delete", action="store_true", help="Delete S3 objects not present locally (within the prefix).")
  sync.add_argument("--strategy", choices=["size-mtime", "size-only"], default="size-mtime", help="Decide whether to upload: compare remote size and stored mtime metadata (default), or size only.")

  return p

def parse_s3_uri(uri: str) -> tuple[str, str]:
  if not uri.startswith("s3://"):
    raise ValueError("s3_uri must start with s3://bucket/prefix")
  rest = uri[5:]
  parts = rest.split("/", 1)
  bucket = parts[0]
  prefix = parts[1] if len(parts) > 1 else ""
  prefix = prefix.strip("/")
  if not bucket:
    raise ValueError("Invalid s3_uri: missing bucket")
  return bucket, prefix

def main(argv: Optional[List[str]] = None) -> int:
  args = build_parser().parse_args(argv)
  logging.basicConfig(level=getattr(logging, args.log_level), format="%(asctime)s %(levelname)s %(message)s")

  try:
    validate_creds(args.profile)

    if args.cmd == "sync":
      local_root = Path(args.local_dir).expanduser().resolve()
      if not local_root.exists() or not local_root.is_dir():
        raise ValueError(f"local_dir not found or not a directory: {local_root}")
      
      bucket, prefix = parse_s3_uri(args.s3_uri)
      client = s3_client(args.profile, args.region)

      actions = []
      uploaded = 0
      skipped = 0

      local_key_set = set()

      for f in iter_files(local_root, args.exclude):
        key = join_s3_key(prefix, f.rel)
        local_key_set.add(key)

        remote = head_object_etag_size_mtime(client, bucket, key)
        if remote is None:
          actions.append(upload_file(client, bucket, key, str(f.path), f.mtime, args.dry_run))
          uploaded += 1
          continue

        _etag, r_size, r_mtime = remote

        should_upload = False
        if args.strategy == "size-only":
          should_upload = (r_size != f.size)
        else:
          # size-mtime strategy: upload if size differs OR mtime metadata differs/absent
          should_upload = (r_size != f.size) or (r_mtime is None) or (r_mtime != f.mtime)
        
        if should_upload:
          actions.append(upload_file(client, bucket, key, str(f.path), f.mtime, args.dry_run))
          uploaded += 1
        else:
          skipped += 1
      
      deleted = 0
      if args.delete:
        # List all objects under the prefix and delete those not in local set
        list_prefix = prefix + "/" if prefix else ""
        remote_keys = list_objects_keys(client, bucket, list_prefix)
        for k in remote_keys:
          # If the key is outside local set, delete
          if k not in local_key_set:
            actions.append(delete_object(client, bucket, k, args.dry_run))
            deleted += 1
      
      summary = {
        "cmd": "sync",
        "local_dir": str(local_root),
        "bucket": bucket,
        "prefix": prefix,
        "dry_run": bool(args.dry_run),
        "uploaded": uploaded,
        "skipped": skipped,
        "deleted": deleted,
        "total_actions": len(actions),        
      }

      if args.json:
        print(json.dumps({"summary": summary, "actions": actions}, indent=2, ensure_ascii=False))
      else:
        print(f"SYNC -> s3://{bucket}/{prefix}")
        print(f"uploaded={uploaded} skipped={skipped} deleted={deleted} dry_run={args.dry_run}")
      return EXIT_OK
    
    return EXIT_ERROR

  except Exception as e:
    logging.error(str(e))
    return EXIT_ERROR
  
# if __name__ == "__main__":
#     raise SystemExit(main())


          





      