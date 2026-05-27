from __future__ import annotations

import shutil
import subprocess


def refine_email_with_hermes(base_draft: str, voice_guidelines: str, *, timeout: int = 90) -> str:
    """Optionally refine a deterministic draft through Hermes/Codex OAuth.

    This is best-effort by design. Operator's MVP remains usable without live
    OAuth, network, or model availability. If the refinement call fails, callers
    should keep the deterministic draft.
    """
    if not shutil.which("hermes"):
        raise RuntimeError("Hermes CLI is not installed or not on PATH")

    prompt = f"""
You are refining a draft customer email for a luxury boutique men's grooming business.
Keep the same facts, subject, customer name, and signature.
Make it concise, polished, personal, and non-pushy.
Return only the refined email.

Voice guidelines:
{voice_guidelines}

Draft:
{base_draft}
""".strip()
    proc = subprocess.run(
        ["hermes", "chat", "-q", prompt, "-m", "gpt-5.5", "--provider", "openai-codex", "-Q", "--ignore-rules"],
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "Hermes refinement failed")
    output = proc.stdout.strip()
    if not output:
        raise RuntimeError("Hermes refinement returned empty output")
    return output
