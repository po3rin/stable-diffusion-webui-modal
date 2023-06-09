import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import modal
from colorama import Fore

stub = modal.Stub("stable-diffusion-webui")
volume_main = modal.SharedVolume().persist("stable-diffusion-webui-main")

webui_dir = "/content/stable-diffusion-webui"
sd_dir = webui_dir + "/models/Stable-diffusion/"

# 読み込むモデルのリスト
models = [
    {
        "repo_id": "hakurei/waifu-diffusion-v1-4",
        "model_path": "wd-1-4-anime_e1.ckpt",
        "config_file_path": "wd-1-4-anime_e1.yaml",
    }
]

@stub.function(
    image=modal.Image.from_dockerhub("python:3.10-slim").apt_install(
        "gcc", "git", "libgl1-mesa-dev", "libglib2.0-0", "libsm6",
        "libxrender1", "libxext6", "libcairo2-dev", "libcairo2").
    run_commands(
        "pip install -e git+https://github.com/CompVis/"\
            "taming-transformers.git@master"\
            "#egg=taming-transformers"
    ).pip_install(
        "blendmodes==2022",
        "transformers==4.25.1",
        "accelerate==0.12.0",
        "basicsr==1.4.2",
        "gfpgan==1.3.8",
        "gradio==3.30.0",
        "numpy==1.23.3",
        "Pillow==9.4.0",
        "realesrgan==0.3.0",
        "torch",
        "omegaconf==2.2.3",
        "pytorch_lightning==1.7.6",
        "scikit-image==0.19.2",
        "fonts",
        "font-roboto",
        "timm==0.6.7",
        "piexif==1.1.3",
        "einops==0.4.1",
        "jsonmerge==1.8.0",
        "clean-fid==0.1.29",
        "resize-right==0.0.2",
        "torchdiffeq==0.2.3",
        "kornia==0.6.7",
        "lark==1.1.2",
        "inflection==0.5.1",
        "GitPython==3.1.27",
        "torchsde==0.2.5",
        "safetensors==0.2.7",
        "httpcore<=0.15",
        "tensorboard==2.9.1",
        "taming-transformers==0.0.1",
        "clip",
        "test-tube",
        "diffusers",
        "invisible-watermark",
        "pyngrok",
        "xformers==0.0.17",
        "gdown",
        "huggingface_hub",
        "colorama",
    ).pip_install(
        "git+https://github.com/mlfoundations/open_clip.git"\
            "@bb6e834e9c70d9c27d0dc3ecedeebeaeb1ffad6b"
    ),
    secret=modal.Secret.from_name("huggingface-secret"),
    shared_volumes={webui_dir: volume_main},
    gpu="a10g",
    timeout=6000,
)
async def run_stable_diffusion_webui():
    webui_dir_path = Path(sd_dir)
    if not webui_dir_path.exists():
        subprocess.run(
            f"git clone https://github.com/AUTOMATIC1111/"\
                f"stable-diffusion-webui  {webui_dir}",
            shell=True
        )

    def download_hf_file(repo_id, filename) -> str:
        """
        Hugging faceからファイルをダウンロードしてくる関数
        """
        from huggingface_hub import hf_hub_download

        download_dir = hf_hub_download(repo_id=repo_id, filename=filename)
        return download_dir

    for model in models:
        if not Path(sd_dir + model["model_path"]).exists():
            model_downloaded_dir = download_hf_file(
                model["repo_id"],
                model["model_path"],
            )
            shutil.copy(model_downloaded_dir,
                        sd_dir + os.path.basename(model["model_path"]))

        if "config_file_path" not in model:
            continue

        if not Path(sd_dir + model["config_file_path"]).exists():
            config_downloaded_dir = download_hf_file(
                model["repo_id"], model["config_file_path"])
            shutil.copy(
                config_downloaded_dir,
                sd_dir + os.path.basename(model["config_file_path"]))

        print(Fore.GREEN + model["repo_id"] + "のセットアップが完了しました！")

    sys.path.append(webui_dir)
    sys.argv += shlex.split("--skip-install --xformers")
    os.chdir(webui_dir)
    from launch import prepare_environment, start

    prepare_environment()
    sys.argv = shlex.split(
        "--gradio-debug --share --xformers"\
            " --enable-insecure-extension-access"
    )
    start()


@stub.local_entrypoint()
def main():
    run_stable_diffusion_webui.call()
