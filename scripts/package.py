"""Сборка релизного архива: dist/rental-service-<версия>.zip

Запуск:  python scripts/package.py --version 7
"""
import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ["run.py", "requirements.txt"]  # отдельные файлы в релиз
FOLDERS = ["app"]  # папки в релиз (тесты и скрипты в релиз не попадают)


def build(version):
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    archive = dist / f"rental-service-{version}.zip"

    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for name in FILES:
            bundle.write(ROOT / name, name)
        for folder in FOLDERS:
            for path in sorted((ROOT / folder).rglob("*")):
                if path.is_dir() or "__pycache__" in path.parts or path.suffix == ".pyc":
                    continue
                bundle.write(path, path.relative_to(ROOT).as_posix())
        bundle.writestr("VERSION", f"{version}\n")
    return archive


def main():
    parser = argparse.ArgumentParser(description="Собрать релизный архив")
    parser.add_argument("--version", default="dev", help="версия релиза (номер сборки Jenkins)")
    args = parser.parse_args()
    archive = build(args.version)
    print(f"Release archive created: {archive}")


if __name__ == "__main__":
    main()
