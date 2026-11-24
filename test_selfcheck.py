"""Самопроверка: сначала будут ошибки TODO; исправляйте код поэтапно."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from file_exchange_starter import scan_files, sha256_file, create_package, receive_package, save_report

class FileExchangeChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'a.txt').write_text('привет', encoding='utf-8')
        (self.root / 'b.bin').write_bytes(b'\x00\x01\xff')
        (self.root / 'nested').mkdir()
        (self.root / 'nested' / 'c.txt').write_text('другая строка', encoding='utf-8')

    def test_01_scan_pattern(self):
        names = [item['name'] for item in scan_files(self.root, '*.txt')]
        self.assertEqual(names, ['a.txt', 'c.txt'])

    def test_02_sha256(self):
        file = self.root / 'a.txt'
        self.assertEqual(sha256_file(file), hashlib.sha256(file.read_bytes()).hexdigest())

    def test_03_exchange(self):
        outbox = self.root / 'outbox'
        inbox = self.root / 'inbox'
        package = create_package(self.root / 'a.txt', 'team_A', 'team_B', outbox)
        result = receive_package(package, inbox, 'team_B')
        self.assertEqual(result.read_bytes(), (self.root / 'a.txt').read_bytes())

    def test_04_corrupted_file_is_rejected(self):
        outbox = self.root / 'outbox'
        package = create_package(self.root / 'a.txt', 'team_A', 'team_B', outbox)
        manifest = json.loads(ZipFile(package).read('manifest.json'))
        with ZipFile(package, 'w', compression=ZIP_DEFLATED) as z:
            z.writestr('manifest.json', json.dumps(manifest))
            z.writestr('files/a.txt', 'подменено')
        with self.assertRaises(ValueError):
            receive_package(package, self.root / 'inbox', 'team_B')
        self.assertFalse((self.root / 'inbox' / 'a.txt').exists())

    def test_05_csv_report(self):
        path = self.root / 'report.csv'
        save_report(scan_files(self.root, '*.txt'), path)
        self.assertIn('relative_path', path.read_text(encoding='utf-8-sig'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
