from pathlib import Path


def test_render_blueprint_defines_backend_and_ui_services():
    content = Path("render.yaml").read_text(encoding="utf-8")

    assert "name: resolveai-api" in content
    assert "name: resolveai-ui" in content
    assert "fromService:" in content
    assert "property: hostport" in content
