"""4.3.0 fonts stay local, licensed and free of network requests."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FONT_PACKAGES = frozenset({
    "@fontsource-variable/inter",
    "@fontsource-variable/jetbrains-mono",
    "@fontsource-variable/lexend",
})


def test_only_bundled_fontsource_packages():
    package = json.loads((ROOT / "ui/package.json").read_text())
    dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    font_packages = frozenset(
        name for name in dependencies
        if "font" in name.lower() or "typeface" in name.lower()
    )
    assert font_packages == EXPECTED_FONT_PACKAGES
    assert not any("google" in name.lower() for name in dependencies)

    main = (ROOT / "ui/src/main.tsx").read_text()
    for name in sorted(EXPECTED_FONT_PACKAGES):
        assert f'"{name}/index.css"' in main, name

    sources = list((ROOT / "ui/src").rglob("*.css")) + [ROOT / "ui/index.html"]
    for source in sources:
        assert "@import url(" not in source.read_text(), str(source.relative_to(ROOT))

    assert "strip-font-cdn.mjs" in (ROOT / "scripts/build_ui.sh").read_text()


def test_google_sans_flex_decision_is_recorded():
    spec = (ROOT / "docs/design-4.3.md").read_text()
    assert "Google Sans Flex" in spec
    assert "not adopted" in spec
    assert "OFL 1.1" in spec
