"""
OmniRoute Local AI Gateway Bridge for Jarvis CGI & Realtime VFX Suite
Connects local Python pipelines, character animation scripts, and VFX tools
to the running OmniRoute gateway on port 20128.
"""

import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List

OMNIROUTE_URL = "http://127.0.0.1:20128"
DEFAULT_API_KEY = "sk-cc4d18884ff72840-bad83d-0512c75e"

class OmniRouteClient:
    def __init__(self, base_url: str = OMNIROUTE_URL, api_key: str = DEFAULT_API_KEY):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def ping(self) -> Dict[str, Any]:
        """Check if OmniRoute service is listening and reachable."""
        try:
            req = urllib.request.Request(f"{self.base_url}/")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return {"online": True, "code": resp.getcode(), "port": 20128}
        except Exception as e:
            return {"online": False, "error": str(e), "port": 20128}

    def chat(self, prompt: str, system_prompt: Optional[str] = None, model: str = "auto/chat", max_tokens: int = 150) -> Dict[str, Any]:
        """Send a chat completion through the OmniRoute gateway."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }

        req = urllib.request.Request(
            f"{self.base_url}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )

        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                latency = round((time.time() - t0) * 1000, 1)
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"success": True, "content": content, "model": model, "latency_ms": latency}
        except urllib.error.HTTPError as e:
            return {"success": False, "error": f"HTTP {e.code}: {e.reason}", "model": model}
        except Exception as e:
            return {"success": False, "error": str(e), "model": model}

    def generate_vfx_director_cue(self, stance: str, energy_level: int = 100) -> str:
        """Generate Hollywood director guidance based on active motion capture stance."""
        prompt = f"Actor performed {stance} gesture at {energy_level}% power. Give 1 short, intense, cinematic Marvel/DNEG director command in under 12 words."
        res = self.chat(prompt, system_prompt="You are a Hollywood VFX Fight Director. Be punchy, cinematic, and urgent.")
        if res.get("success"):
            return res.get("content", "").strip()
        
        # Fallback offline cinematic director cues
        cues = {
            "SHANG_CHI": "Hold the low dragon guard! Channel Ta Lo fire through the rings!",
            "BRAHMASTRA": "Focus astral heat at the sternum! Ignite the Agnyastra core!",
            "IRON_MAN": "Lock repulsor targeting! Full auxiliary thrust to flight stabs!",
            "DOCTOR_STRANGE": "Cast the Tao mandala wide! Anchor the mirror dimension fold!"
        }
        return cues.get(stance, "Energy locked! Maintain posture for maximum kinematic tracking!")

if __name__ == "__main__":
    client = OmniRouteClient()
    print("Checking OmniRoute status...")
    status = client.ping()
    print("Status:", status)
    if status.get("online"):
        print("OmniRoute Gateway on port 20128 is ONLINE!")
        print("Test VFX Director Cue (Shang-Chi):")
        print(" ->", client.generate_vfx_director_cue("SHANG_CHI"))
