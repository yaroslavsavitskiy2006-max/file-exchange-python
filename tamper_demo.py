"""Создать ИСПОРЧЕННУЮ КОПИЮ учебного ZIP для проверки отказа (оригинал не меняет)."""
import json
import sys
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def main():
    if len(sys.argv) != 2:
        print('Использование: python tamper_demo.py путь_к_пакету.zip')
        raise SystemExit(2)
    src = Path(sys.argv[1])
    dst = src.with_name('corrupted_' + src.name)
    if dst.exists():
        raise FileExistsError('Тестовая копия уже существует: ' + str(dst))
    with ZipFile(src, 'r') as z:
        manifest_bytes = z.read('manifest.json')
        manifest = json.loads(manifest_bytes.decode('utf-8'))
        entry = 'files/' + manifest['filename']
        data = z.read(entry)
    # Меняем ровно один байт. Размер не изменяется, проверка SHA-256 должна сработать.
    changed = (bytes([data[0] ^ 1]) + data[1:]) if data else b'!'
    with ZipFile(dst, 'x', compression=ZIP_DEFLATED) as z:
        z.writestr('manifest.json', manifest_bytes)
        z.writestr(entry, changed)
    print('Создан повреждённый тестовый пакет:', dst)
    print('Исходный пакет не изменён.')

if __name__ == '__main__':
    main()
