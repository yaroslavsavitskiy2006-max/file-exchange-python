"""Практическая работа: файловая система и обмен данными (Python 3.9+).
Запускайте без интернета. Дописывайте участки # TODO.
Команды: prepare, scan, pack, receive, report.
"""
from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "workspace"
DATA = WORK / "data"
OUTBOX = WORK / "outbox"
INBOX = WORK / "inbox"


def prepare() -> None:
    """Создать учебные файлы. Эта функция уже готова."""
    for folder in (DATA, OUTBOX, INBOX, DATA / "nested"):
        folder.mkdir(parents=True, exist_ok=True)
    samples = {
        DATA / "notes.txt": "Заметка: основы файловой системы\nUTF-8: привет!\n",
        DATA / "log.txt": "2026-01-10;start\n2026-01-10;finish\n",
        DATA / "nested" / "task.txt": "Задание для соседней команды\n",
    }
    for path, content in samples.items():
        if not path.exists():
            path.write_text(content, encoding="utf-8")
    bin_path = DATA / "sample.bin"
    if not bin_path.exists():
        bin_path.write_bytes(bytes([0, 1, 2, 254, 255]))
    print("Создана учебная структура:", WORK)


def scan_files(folder: Path, pattern: str = "*", min_size: int = 0) -> list[dict]:
    """TODO 1: рекурсивный поиск; фильтрация по имени и размеру; сортировка."""
    result = []
    for file in folder.rglob("*"):
        if not file.is_file():
            continue
        info = file.stat()
        # TODO 1А: пропускайте файл, если имя не подходит к pattern (fnmatch.fnmatch)
        if not fnmatch.fnmatch(file.name, pattern):
            continue
        # TODO 1Б: пропускайте файл, если info.st_size меньше min_size
        if info.st_size < min_size:
            continue
        result.append({
            "name": file.name,
            "relative_path": str(file.relative_to(folder)),
            "size_bytes": info.st_size,
            "modified": datetime.fromtimestamp(info.st_mtime).isoformat(timespec="seconds"),
        })
    # TODO 1В: отсортируйте записи по имени; при равенстве — по relative_path
    result.sort(key=lambda x: (x["name"], x["relative_path"]))
    return result


def sha256_file(path: Path) -> str:
    """TODO 2: получить SHA-256 бинарного файла по блокам по 4096 байт."""
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        while True:
            chunk = file.read(4096)
            # TODO 2А: если chunk пустой — завершите цикл
            if not chunk:
                break
            # TODO 2Б: добавьте блок в hasher через update()
            hasher.update(chunk)
    return hasher.hexdigest()


def create_package(source: Path, sender: str, recipient: str, outbox: Path = OUTBOX) -> Path:
    """TODO 3: создать ZIP с manifest.json и files/<имя_файла>."""
    source = Path(source)
    if not source.is_file():
        raise FileNotFoundError(source)
    if not sender.isidentifier() or not recipient.isidentifier():
        raise ValueError("Используйте имя из букв, цифр и _; первый символ — не цифра")
    outbox.mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": 1,
        "sender": sender,
        "recipient": recipient,
        "filename": source.name,
        "size_bytes": source.stat().st_size,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        # TODO 3А: добавьте поле "sha256" со значением sha256_file(source)
        "sha256": sha256_file(source),
    }
    package = outbox / f"{sender}__{recipient}__{source.stem}.zip"
    if package.exists():
        raise FileExistsError("Пакет с таким именем существует: " + str(package))
    with ZipFile(package, "w", compression=ZIP_DEFLATED) as archive:
        # TODO 3Б: поместите манифест как строку JSON в manifest.json (writestr)
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        # TODO 3В: поместите файл внутрь ZIP под именем files/<имя_файла> (write)
        archive.write(source, arcname="files/" + source.name)
    return package


def receive_package(package: Path, inbox: Path = INBOX, recipient: Optional[str] = None) -> Path:
    """TODO 4: проверить манифест и контрольную сумму, сохранить файл безопасно."""
    inbox.mkdir(parents=True, exist_ok=True)
    with ZipFile(package, "r") as archive:
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        name = manifest["filename"]
        # TODO 4А: убедитесь, что name — простое имя, а не путь ('..', '/', '\\')
        if Path(name).name != name or "/" in name or "\\" in name or ".." in name:
            raise ValueError("Недопустимое имя файла в манифесте")
        # TODO 4Б: если recipient задан, проверьте manifest['recipient']
        if recipient is not None and manifest.get("recipient") != recipient:
            raise ValueError("Получатель не совпадает")
        content = archive.read("files/" + name)
        # TODO 4В: сравните len(content) и manifest['size_bytes']
        if len(content) != manifest["size_bytes"]:
            raise ValueError("Размер файла не совпадает с манифестом")
        # TODO 4Г: сравните hashlib.sha256(content).hexdigest() и manifest['sha256']
        if hashlib.sha256(content).hexdigest() != manifest["sha256"]:
            raise ValueError("Контрольная сумма SHA-256 не совпадает")
        # TODO 4Д: при любой ошибке выбрасывайте ValueError; НЕ сохраняйте файл
    destination = inbox / name
    # TODO 4Е: запишите content через режим 'xb', не перезаписывая существующий файл
    try:
        with destination.open("xb") as f:
            f.write(content)
    except Exception as e:
        raise ValueError(f"Не удалось записать файл: {e}") from e
    return destination


def save_report(items: list[dict], path: Path) -> None:
    """Необязательное усложнение: сохранить отчёт CSV для второй команды."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # TODO 5: используйте csv.DictWriter и передайте fieldnames
    fieldnames = ["name", "relative_path", "size_bytes", "modified"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            writer.writerow(item)


def main() -> None:
    parser = argparse.ArgumentParser(description="Файловая почта (учебная практика)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare", help="Создать учебные файлы")
    scan = sub.add_parser("scan", help="Поиск файлов в workspace/data")
    scan.add_argument("--pattern", default="*", help="Например, *.txt")
    scan.add_argument("--min-size", type=int, default=0)
    pack = sub.add_parser("pack", help="Подготовить пакет для соседней команды")
    pack.add_argument("--file", default="notes.txt", help="Имя файла в workspace/data")
    pack.add_argument("--sender", required=True)
    pack.add_argument("--recipient", required=True)
    get = sub.add_parser("receive", help="Принять ZIP-пакет")
    get.add_argument("--package", required=True)
    get.add_argument("--recipient", required=True)
    sub.add_parser("report", help="Сохранить CSV-отчёт (дополнительное)")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare()
    elif args.command == "scan":
        print(json.dumps(scan_files(DATA, args.pattern, args.min_size), ensure_ascii=False, indent=2))
    elif args.command == "pack":
        file = DATA / args.file
        print("Создан пакет:", create_package(file, args.sender, args.recipient))
    elif args.command == "receive":
        print("Принято:", receive_package(Path(args.package), INBOX, args.recipient))
    else:
        save_report(scan_files(DATA), WORK / "report.csv")
        print("Отчёт:", WORK / "report.csv")


if __name__ == "__main__":
    main()
