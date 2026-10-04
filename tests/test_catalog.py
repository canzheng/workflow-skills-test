import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from app import catalog

ROOT = pathlib.Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = pathlib.Path(self.temp.name) / 'catalog.json'

    def cli(self, *args):
        return subprocess.run([sys.executable, '-m', 'app.catalog', '--file', str(self.path), *args], cwd=ROOT, capture_output=True, text=True)

    def test_actual_cli_round_trip_independent_design_example_and_empty(self):
        self.assertEqual(json.loads(self.cli('show').stdout), {})
        self.assertFalse(self.path.exists())
        self.assertEqual(self.cli('add', 'oats', '500').returncode, 0)
        self.assertEqual(self.cli('add', 'lentils', '300').returncode, 0)
        self.assertEqual(self.cli('show').stdout.strip(), '{"lentils": 300, "oats": 500}')
        self.assertEqual(json.loads(self.path.read_text()), {'oats': 500, 'lentils': 300})
        self.assertEqual(self.cli('add', 'salt', '0').returncode, 0)

    def test_duplicate_negative_noninteger_and_empty_id_leave_bytes_unchanged(self):
        self.assertEqual(self.cli('add', 'oats', '500').returncode, 0)
        original = self.path.read_bytes()
        for args in [('add', 'oats', '900'), ('add', 'salt', '-1'), ('add', 'salt', '1.5'), ('add', '', '4')]:
            with self.subTest(args=args):
                result = self.cli(*args)
                self.assertNotEqual(result.returncode, 0)
                self.assertTrue(result.stderr)
                self.assertEqual(self.path.read_bytes(), original)

    def test_malformed_and_invalid_stored_data_are_not_replaced(self):
        for text in ('not JSON', '[]', '{"oats": true}', '{"oats": 1.5}', '{"oats": -1}', '{"": 4}', '{"oats": 1, "oats": 2}'):
            with self.subTest(text=text):
                self.path.write_text(text)
                for args in [('show',), ('add', 'salt', '5')]:
                    self.assertEqual(self.cli(*args).returncode, 1)
                    self.assertEqual(self.path.read_text(), text)

    def test_missing_parent_and_symlink_fail_without_selecting_other_target(self):
        self.path = self.path.parent / 'missing' / 'catalog.json'
        self.assertEqual(self.cli('add', 'oats', '500').returncode, 1)
        self.assertFalse(self.path.parent.exists())
        self.path = self.path.parent.parent / 'link.json'
        real = self.path.parent / 'actual.json'
        real.write_text('{"oats": 500}')
        self.path.symlink_to(real)
        self.assertEqual(self.cli('add', 'salt', '10').returncode, 1)
        self.assertEqual(real.read_text(), '{"oats": 500}')

    def test_interrupted_replace_restores_original_and_cleans_staging(self):
        self.path.write_text('{"oats": 500}')
        with patch.object(catalog.os, 'replace', side_effect=OSError('Injected replacement failure')):
            with self.assertRaises(OSError):
                catalog.add(self.path, 'salt', 10)
        self.assertEqual(self.path.read_text(), '{"oats": 500}')
        self.assertEqual(list(self.path.parent.glob('.pantry-*')), [])
        self.assertEqual(catalog.add(self.path, 'salt', 10), {'oats': 500, 'salt': 10})

    def test_denied_staging_preserves_original_and_surfaces_failure(self):
        self.path.write_text('{"oats": 500}')
        with patch.object(catalog.tempfile, 'NamedTemporaryFile', side_effect=PermissionError('Injected permission denial')):
            with self.assertRaises(PermissionError):
                catalog.add(self.path, 'salt', 10)
        self.assertEqual(self.path.read_text(), '{"oats": 500}')

    def test_atomic_update_preserves_existing_file_mode(self):
        self.path.write_text('{"oats": 500}')
        self.path.chmod(0o640)
        catalog.add(self.path, 'salt', 10)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o640)

    def test_real_permission_loss_reports_both_errors_and_recoverable_residue(self):
        self.path.write_text('{"oats": 500}')
        script = '''
import os, pathlib, sys
from unittest.mock import patch
from app import catalog
path = pathlib.Path(sys.argv[1])
if os.geteuid() == 0:
    os.chown(path.parent, 65534, 65534)
    os.chown(path, 65534, 65534)
    os.setuid(65534)
replace = os.replace
def revoke_permission(source, target):
    path.parent.chmod(0o500)
    return replace(source, target)
try:
    with patch.object(catalog.os, 'replace', side_effect=revoke_permission):
        catalog.add(path, 'salt', 10)
except OSError as error:
    assert isinstance(error.__cause__, PermissionError), repr(error)
    print(str(error))
else:
    raise AssertionError('replacement should be denied for an unprivileged writer')
finally:
    path.parent.chmod(0o700)
'''
        result = subprocess.run([sys.executable, '-c', script, str(self.path)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Permission denied', result.stdout)
        self.assertIn('staging cleanup failed', result.stdout)
        self.assertEqual(self.path.read_text(), '{"oats": 500}')
        residue = list(self.path.parent.glob('.pantry-*'))
        self.assertEqual(len(residue), 1)
        self.assertIn(str(residue[0]), result.stdout)
        residue[0].unlink()
        self.assertEqual(catalog.add(self.path, 'salt', 10), {'oats': 500, 'salt': 10})

    def test_closed_output_pipe_reports_failure_after_committing_data(self):
        self.path.write_text('{"oats": 500}')
        read_fd, write_fd = os.pipe()
        os.close(read_fd)
        try:
            result = subprocess.run([sys.executable, '-m', 'app.catalog', '--file', str(self.path), 'add', 'lentils', '300'], cwd=ROOT, stdout=write_fd, stderr=subprocess.PIPE, text=True)
        finally:
            os.close(write_fd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Broken pipe', result.stderr)
        self.assertEqual(json.loads(self.cli('show').stdout), {'oats': 500, 'lentils': 300})
        self.assertEqual(self.cli('add', 'lentils', '300').returncode, 1)
