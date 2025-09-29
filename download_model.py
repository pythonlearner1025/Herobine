#!/usr/bin/env python3
"""
Script to download the JarvisVLA model from Hugging Face
"""

from huggingface_hub import snapshot_download
import os

def download_jarvis_vla_model():
    """Download the complete JarvisVLA model"""
    
    model_name = "CraftJarvis/JarvisVLA-Qwen2-VL-7B"
    local_dir = "./models/JarvisVLA-Qwen2-VL-7B"
    
    print(f"🚀 Downloading {model_name}...")
    print(f"📁 Local directory: {local_dir}")
    
    try:
        # Create local directory if it doesn't exist
        os.makedirs(local_dir, exist_ok=True)
        
        # Download the model
        snapshot_download(
            repo_id=model_name,
            local_dir=local_dir,
            local_dir_use_symlinks=False,  # Use actual files instead of symlinks
            resume_download=True,  # Resume if partially downloaded
        )
        
        print(f"✅ Model downloaded successfully to {local_dir}")
        print(f"📊 Model size: ~16.6 GB (as shown on Hugging Face)")
        
        # List downloaded files
        print("\n📋 Downloaded files:")
        for root, dirs, files in os.walk(local_dir):
            for file in files:
                file_path = os.path.join(root, file)
                size = os.path.getsize(file_path)
                size_mb = size / (1024 * 1024)
                print(f"  {file}: {size_mb:.1f} MB")
        
        return local_dir
        
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        return None

if __name__ == "__main__":
    print("📥 JarvisVLA Model Downloader")
    print("=" * 40)
    
    model_path = download_jarvis_vla_model()
    
    if model_path:
        print(f"\n🎉 Download complete!")
        print(f"🚀 You can now serve the model with:")
        print(f"   CUDA_VISIBLE_DEVICES=0 vllm serve {model_path} --port 8000 --max-model-len 4096")
        print(f"\n📝 Or use the Hugging Face model name directly:")
        print(f"   CUDA_VISIBLE_DEVICES=0 vllm serve CraftJarvis/JarvisVLA-Qwen2-VL-7B --port 8000 --max-model-len 4096")
    else:
        print("❌ Download failed!")
