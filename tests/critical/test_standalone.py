"""Critical standalone boundaries only, with synthetic files and no probes."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock
import zipfile

from mapper import standalone
from mapper import frozen_runtime
from mapper import standalone_manifest as manifest


class StandaloneTests(unittest.TestCase):
    def test_dispatch_defaults_cli_and_maintenance_without_external_python(self):
        with patch('mapper.cli.main', return_value=0) as cli:
            self.assertEqual(standalone.main([]), 0)
            cli.assert_called_once_with(['panel'])
        with patch('mapper.maintenance.main', return_value=0) as main:
            self.assertEqual(standalone.main(['maintenance','receipt','--data-dir','test']),0)
            main.assert_called_once_with(['receipt','--data-dir','test'])
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(standalone.main(['verify','fake-secret']),2)
        self.assertNotIn('fake-secret',err.getvalue())
        with contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertNotEqual(standalone.main(['maintenance','receipt','--password','fake-secret']),0)
        self.assertNotIn('fake-secret',err.getvalue())
        from mapper.cli import main as cli_main
        with patch.object(sys,'frozen',True,create=True),contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(cli_main(['doctor']),0)
        self.assertEqual(json.loads(output.getvalue())['runtime'],'bundled')

    def test_manifest_changes_links_and_zip_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'Mapper';root.mkdir()
            app=root/('Mapper.exe' if sys.platform=='win32' else 'Mapper');app.write_text('synthetic');app.chmod(0o755)
            (root/'_internal').mkdir();lib=root/'_internal/library.py';lib.write_text('value=1')
            if sys.platform != 'win32':
                (root/'_internal/current').symlink_to('library.py')
            manifest.write(root,'test','macos-arm64',{})
            manifest.verify(root)
            dest=Path(directory)/'bundle.zip';manifest.archive(root,dest)
            with zipfile.ZipFile(dest) as z:
                if sys.platform != 'win32':
                    self.assertEqual(z.read('Mapper/_internal/current'),b'library.py')
                    self.assertEqual((z.getinfo('Mapper/_internal/current').external_attr>>16)&0o170000,0o120000)
                    self.assertTrue(z.getinfo('Mapper/Mapper').external_attr>>16 & 0o100)
            lib.write_text('value=2')
            with self.assertRaisesRegex(manifest.ManifestError,'BUNDLE_CONTENT_CHANGED'):manifest.verify(root)
            lib.write_text('value=1');(root/'extra').write_text('extra')
            with self.assertRaises(manifest.ManifestError):manifest.verify(root)

    def test_manifest_traversal_escaping_cyclic_and_unexpected_symlinks(self):
        for name in ['../escape','/absolute','C:/evil','a\\evil','a/../evil','a//x']:
            with self.assertRaises(manifest.ManifestError):manifest.safe_name(name)
        from types import SimpleNamespace
        with patch.object(Path,'lstat',return_value=SimpleNamespace(st_file_attributes=0x400,st_mode=0o100600)):
            with self.assertRaisesRegex(manifest.ManifestError,'REPARSE_POINT'):manifest.record(Path('/bundle'),Path('/bundle/file'))
        if sys.platform == 'win32':
            return  # Native reparse/NTFS receipt is separate; no elevated symlink privilege.
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'bundle';root.mkdir();outside=Path(directory)/'other';outside.write_text('x')
            link=root/'link';link.symlink_to('../other')
            with self.assertRaisesRegex(manifest.ManifestError,'LINK_OUTSIDE_BUNDLE'):manifest.inventory(root)
            link.unlink();link.symlink_to('link')
            with self.assertRaisesRegex(manifest.ManifestError,'BROKEN_OR_CYCLIC_LINK'):manifest.inventory(root)

    def test_child_environment_drops_only_bundled_loader_paths(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(sys,'frozen',True,create=True), patch.object(sys,'_MEIPASS',directory,create=True):
            with patch.dict(os.environ,{'DYLD_LIBRARY_PATH':directory+os.pathsep+'/usr/lib','TEST_PROFILE_REF':'test-value'}):
                env=frozen_runtime.child_environment()
                self.assertEqual(env['DYLD_LIBRARY_PATH'],'/usr/lib')
                self.assertEqual(env['TEST_PROFILE_REF'],'test-value')
                self.assertTrue(os.environ['DYLD_LIBRARY_PATH'].startswith(directory))
        with patch.object(sys,'frozen',True,create=True),patch.object(sys,'platform','darwin'),patch('mapper.frozen_runtime.child_environment',return_value={}),patch('subprocess.run') as run:
            run.return_value.returncode=0
            self.assertTrue(frozen_runtime.open_browser('http://127.0.0.1:8050'))
            self.assertEqual(run.call_args.kwargs['timeout'],5)

    def test_windows_dll_search_initialized_once_before_workers(self):
        import ctypes
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'native').mkdir();(root/'native/module.pyd').write_bytes(b'fixture')
            kernel=Mock();kernel.SetDllDirectoryW.return_value=1
            with patch.object(sys,'frozen',True,create=True),patch.object(sys,'_MEIPASS',directory,create=True),patch.object(sys,'platform','win32'),patch.object(sys,'dont_write_bytecode',True),patch.object(os,'add_dll_directory',create=True) as add,patch.object(ctypes,'WinDLL',return_value=kernel,create=True):
                frozen_runtime.initialize()
                kernel.SetDllDirectoryW.assert_called_once_with(None)
                self.assertEqual(add.call_count,2)
