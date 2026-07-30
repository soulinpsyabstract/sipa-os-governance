#!/bin/bash
set -e
echo "=== SIPA Binary SFT Pipeline ==="

# 1. venv
python3 -m venv ~/venv && source ~/venv/bin/activate

# 2. PyTorch CUDA 12.4
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu124 --quiet

# 3. Dependencies
pip install transformers==4.46.3 accelerate==0.34.2 datasets==2.21.0 bitsandbytes==0.44.1 trl==0.12.2 peft==0.13.2 --quiet

# 4. Verify CUDA
python3 -c "import torch; print(f'CUDA OK: {torch.cuda.is_available()}')"

# 5. Download dataset
pip install huggingface_hub --quiet
python3 -c "
from huggingface_hub import hf_hub_download
import shutil
path = hf_hub_download('SoulInPsyAbstract/sipa-os-governance', 'AI_EXPERIMENTS/DATASETS/protocol0_binary_sft.jsonl', repo_type='dataset', token='$HF_TOKEN')
shutil.copy(path, '$HOME/protocol0_binary_sft.jsonl')
print('Dataset OK')
"

# 6. Download training scripts
for script in train_hermes3_std.py train_qwen25_std.py train_r1_std.py; do
    curl -fsSL "https://raw.githubusercontent.com/soulinpsyabstract/sipa-os-governance/main/scripts/$script" -o "$HOME/$script"
done

# 7. Train
source ~/venv/bin/activate
python3 ~/train_hermes3_std.py 2>&1 | tee ~/train_hermes3.log
echo "=== HERMES DONE ==="
python3 ~/train_qwen25_std.py 2>&1 | tee ~/train_qwen25.log  
echo "=== QWEN DONE ==="
python3 ~/train_r1_std.py 2>&1 | tee ~/train_r1.log
echo "=== ALL THREE DONE ==="