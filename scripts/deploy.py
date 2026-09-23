"""Развёртывание релиза (Continuous Deployment).

Что делает скрипт:
  1. останавливает предыдущую версию приложения (если она запущена);
  2. распаковывает архив в <target>/releases/<имя релиза>;
  3. создаёт (один раз) виртуальное окружение <target>/venv и ставит зависимости;
  4. запускает приложение отдельным процессом (waitress) на указанном порту;
  5. проверяет, что GET /health отвечает 200, иначе завершается с ошибкой.

База данных лежит в <target>/data и переживает обновления версий.

Запуск:  python scripts/deploy.py --archive dist/rental-service-7.zip --target deploy --port 5000
"""
import argparse
import os
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

IS_WINDOWS = os.name == "nt"


def venv_python(venv_dir):
    return venv_dir / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")


def stop_previous(pid_file):
    """Останавливает процесс предыдущего релиза по PID из файла."""
    if not pid_file.exists():
        return
    pid = pid_file.read_text().strip()
    if pid.isdigit():
        print(f"Stopping previous release (pid {pid})")
        if IS_WINDOWS:
            subprocess.run(["taskkill", "/PID", pid, "/T", "/F"], capture_output=True)
        else:
            try:
                os.kill(int(pid), signal.SIGTERM)
            except OSError:
                pass  # процесса уже нет
        time.sleep(2)
    pid_file.unlink()


def start_app(python, release_dir, port, db_path, log_file):
    """Запускает приложение так, чтобы оно не завершилось вместе со сборкой Jenkins."""
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "production",
            "PORT": str(port),
            "DATABASE_PATH": str(db_path),
            # Jenkins убивает процессы, порождённые сборкой; эти переменные это отключают
            "JENKINS_NODE_COOKIE": "dontKillMe",
            "BUILD_ID": "dontKillMe",
        }
    )
    options = {}
    if IS_WINDOWS:
        options["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        options["start_new_session"] = True

    log = open(log_file, "ab")
    return subprocess.Popen(
        [str(python), "run.py"],
        cwd=release_dir,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=log,
        stderr=subprocess.STDOUT,
        **options,
    )


def wait_for_health(process, port, timeout=30):
    """Ждёт, пока приложение ответит на /health."""
    url = f"http://127.0.0.1:{port}/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process.poll() is not None:
            return False  # процесс завершился сам — запуск не удался
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            time.sleep(1)
    return False


def main():
    parser = argparse.ArgumentParser(description="Развернуть релиз")
    parser.add_argument("--archive", required=True, help="zip-архив релиза")
    parser.add_argument("--target", default="deploy", help="папка развёртывания")
    parser.add_argument("--port", type=int, default=5000, help="порт приложения")
    args = parser.parse_args()

    archive = Path(args.archive).resolve()
    target = Path(args.target).resolve()
    release_dir = target / "releases" / archive.stem
    data_dir = target / "data"
    pid_file = target / "app.pid"
    log_file = target / "app.log"
    data_dir.mkdir(parents=True, exist_ok=True)

    stop_previous(pid_file)

    if release_dir.exists():
        shutil.rmtree(release_dir)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(release_dir)
    print(f"Release unpacked to {release_dir}")

    venv_dir = target / "venv"
    if not venv_dir.exists():
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])
    python = venv_python(venv_dir)
    subprocess.check_call(
        [str(python), "-m", "pip", "install", "--disable-pip-version-check",
         "-r", str(release_dir / "requirements.txt")]
    )

    process = start_app(python, release_dir, args.port, data_dir / "rental.db", log_file)
    pid_file.write_text(str(process.pid))

    if not wait_for_health(process, args.port):
        print("DEPLOY FAILED: application did not answer on /health. Last log lines:")
        if log_file.exists():
            print("\n".join(log_file.read_text(errors="replace").splitlines()[-20:]))
        sys.exit(1)

    (target / "current_release.txt").write_text(archive.stem + "\n")
    print(f"DEPLOY OK: {archive.stem} is running at http://localhost:{args.port}")


if __name__ == "__main__":
    main()
