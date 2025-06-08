from pathlib import Path
from dreamos.core.gpt_router.prompt_router import PromptRouter


def test_decide_prompt_tmp(tmp_path):
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    (profiles / "default.yaml").write_text("prompt: d\ngpt_profile: base")
    router = PromptRouter(profiles_dir=profiles)
    result = router.decide_prompt("http://example.com")
    assert result["prompt"] == "d"
    assert result["gpt_profile"] == "base"
