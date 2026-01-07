from __future__ import annotations
from typing import Dict, Optional, Tuple, List
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound

def session(profile: Optional[str]) -> boto3.session.Session:
  if profile:
    return boto3.session.Session(profile_name=profile)
  return boto3.session.Session()

def s3_client(profile: Optional[str], region: Optional[str]):
  return session(profile).client("s3", region_name=region)

def head_object_etag_size_mtime(client, bucket: str, key: str) -> Optional[Tuple[str, int, Optional[int]]]:
  """
  Returns (etag, size, mtime_epoch?) if object exists, else None.
  Note: S3 doesn't guarantee mtime as epoch; we store local mtime into metadata.
  """
  try: 
    r = client.head_object(Bucket=bucket, Key=key)
    etag = (r.get("ETag") or "").strip('"')
    size = int(r.get("ContentLength") or 0)
    meta = r.get("Metadata") or {}
    mtime = meta.get("mtime")
    mtime_epoch = int(mtime) if mtime and mtime.isdigit() else None
    return etag, size, mtime_epoch
  except ClientError as e:
    code = e.response.get("Error", {}).get("Code", "")
    if code in ("404", "NoSuchKey", "NotFound"):
      return None
    raise

def list_objects_keys(client, bucket: str, prefix: str) -> List[str]:
  keys: List[str] = []
  paginator = client.get_paginator("list_objects_v2")
  for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
    for obj in page.get("Contents", []) or []:
      keys.append(obj["Key"])
  return keys

def upload_file(client, bucket: str, key: str, local_path: str, mtime_epoch: int, dry_run: bool) -> Dict:
  if dry_run:
    return {"action": "upload", "bucket": bucket, "key": key, "local": local_path, "dry_run": True}
  extra = {
    "Metadata": {
      "mtime": str(mtime_epoch)
    }
  }
  client.upload_file(local_path, bucket, key, ExtraArgs=extra)
  return {"action": "upload", "bucket": bucket, "key": key, "local": local_path, "dry_run": False}

def delete_object(client, bucket: str, key: str, dry_run: bool) -> Dict:
  if dry_run:
    return {"action": "delete", "bucket": bucket, "key": key, "dry_run": True}
  client.delete_object(Bucket=bucket, Key=key)
  return {"action": "delete", "bucket": bucket, "key": key, "dry_run": False}

def validate_creds(profile: Optional[str]) -> None:
  try:
    session(profile).client("sts").get_caller_identity()
  except (NoCredentialsError, ProfileNotFound) as e:
    raise RuntimeError(f"AWS credentials/profile error: {e}") from e
  
  
