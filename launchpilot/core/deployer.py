import os
import subprocess
import shutil
from typing import Dict, Any

class Deployer:
    """
    Controla o deploy automatizado para Vercel ou Cloudflare Pages.
    """
    def __init__(self, provider: str = "vercel"):
        self.provider = provider

    def deploy(self, dist_dir: str, vercel_json_path: str = None) -> Dict[str, Any]:
        if self.provider == "vercel":
            # Copia vercel.json para a pasta de dist se existir
            if vercel_json_path and os.path.exists(vercel_json_path):
                shutil.copy(vercel_json_path, os.path.join(dist_dir, "vercel.json"))

            # Tenta rodar vercel --prod
            try:
                cmd = ["vercel", "--prod", "--yes"]
                res = subprocess.run(cmd, cwd=dist_dir, capture_output=True, text=True, check=True)
                url = res.stdout.strip().split("\n")[-1]
                return {"status": "success", "url": url}
            except Exception as e:
                return {
                    "status": "simulated",
                    "note": "Vercel CLI nao detectada ou sem login ativo. Arquivos gerados prontos em dist/.",
                    "error": str(e)
                }
        return {"status": "unsupported_provider"}
