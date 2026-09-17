import os
from huggingface_hub import HfApi

REPO = "SoulInPsyAbstract/hermes3-8b-exp044-8stage-curriculum-loras"
CKPT_DIR = "/home/shadeform/checkpoints"
KEEP_FILES = {"adapter_config.json", "adapter_model.safetensors", "chat_template.jinja",
              "README.md", "tokenizer_config.json", "tokenizer.json"}

api = HfApi()
stages = sorted(os.listdir(CKPT_DIR))
for stage in stages:
    stage_dir = os.path.join(CKPT_DIR, stage)
    if not os.path.isdir(stage_dir):
        continue
    print(f"=== uploading {stage} ===")
    for fname in sorted(os.listdir(stage_dir)):
        fpath = os.path.join(stage_dir, fname)
        if os.path.isdir(fpath):
            continue
        if fname not in KEEP_FILES and not fname.startswith("adapter"):
            continue
        print(f"  {fname}")
        api.upload_file(
            path_or_fileobj=fpath,
            path_in_repo=f"{stage}/{fname}",
            repo_id=REPO,
            repo_type="model",
        )
    print(f"=== done {stage} ===")
print("ALL DONE")
huge-red-chipmunk
