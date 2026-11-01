"""Critical packaging boundaries only; no registry or network access."""
import importlib.util
import json
from pathlib import Path
import sys
from unittest.mock import patch

from test_stage2 import ProtectedTest
from mapper.cli import demo
from mapper.storage import Repository

SCRIPTS = Path(__file__).parents[2] / 'packaging'
spec = importlib.util.spec_from_file_location('mapper_bundle_test', SCRIPTS / 'bundle.py')
bundle = importlib.util.module_from_spec(spec); spec.loader.exec_module(bundle)
spec = importlib.util.spec_from_file_location('mapper_maintenance_test', SCRIPTS / 'maintenance.py')
maintenance = importlib.util.module_from_spec(spec); spec.loader.exec_module(maintenance)


class PackagingTests(ProtectedTest):
    def fixture(self):
        root = self.root / 'bundle'; root.mkdir(); (root/'wheelhouse').mkdir()
        files = ['bundle.py','maintenance.py','requirements.lock','START_TUTAJ.md','LICENSE','THIRD_PARTY_NOTICES.md','wheelhouse/mapper.whl']
        for name in files: (root/name).write_text('synthetic')
        manifest = {'schema_version':1,'version':'fixture','platform':'macos-arm64','release_status':'internal_candidate',
                    'files':[{'path':n,'size':(root/n).stat().st_size,'sha256':bundle.sha256(root/n)} for n in files]}
        self.publish(root, manifest)
        return root, manifest

    def publish(self, root, manifest):
        (root/'manifest.json').write_text(json.dumps(manifest))
        sums = {r['path']:r['sha256'] for r in manifest['files']}; sums['manifest.json']=bundle.sha256(root/'manifest.json')
        (root/'SHA256SUMS').write_text('\n'.join(sums[n]+'  '+n for n in sorted(sums))+'\n')

    def test_manifest_missing_changed_extra_and_traversal_fail_closed(self):
        root, manifest = self.fixture(); self.assertEqual(bundle.verify(root),manifest)
        (root/'LICENSE').write_text('changed')
        with self.assertRaisesRegex(bundle.BundleError,'BUNDLE_HASH_MISMATCH'):bundle.verify(root)
        (root/'LICENSE').write_text('synthetic'); (root/'wheelhouse/unexpected.whl').write_text('extra')
        with self.assertRaisesRegex(bundle.BundleError,'UNEXPECTED_WHEELHOUSE_CONTENT'):bundle.verify(root)
        for name in ['../escape','/absolute','C:/escape','x\\escape','a/../escape']:
            with self.subTest(name=name), self.assertRaises(bundle.BundleError): bundle.regular(root,name)
        (root/'LICENSE').unlink()
        with self.assertRaisesRegex(bundle.BundleError,'BUNDLE_FILE_MISSING'):bundle.verify(root)

    def test_symlink_checksum_and_install_never_overwrites_existing_venv(self):
        root, manifest = self.fixture()
        # POSIX link fixture; creating symlinks on Windows may need privileges.
        # Windows reparse protection still needs native NTFS acceptance.
        if sys.platform != 'win32':
            (root/'LICENSE').unlink(); (root/'LICENSE').symlink_to(root/'bundle.py')
            with self.assertRaisesRegex(bundle.BundleError,'LINK_IN_BUNDLE'):bundle.verify(root)
            (root/'LICENSE').unlink(); (root/'LICENSE').write_text('synthetic')
        (root/'SHA256SUMS').write_text('wrong')
        with self.assertRaisesRegex(bundle.BundleError,'CHECKSUM_LIST_MISMATCH'):bundle.verify(root)
        self.publish(root,manifest); (root/'.venv').mkdir(); marker=root/'.venv/preserve'; marker.write_text('existing')
        with patch.object(bundle,'check_platform'),patch.object(bundle.subprocess,'run') as run:
            with self.assertRaisesRegex(bundle.BundleError,'VENV_ALREADY_EXISTS'):bundle.install(root)
            run.assert_not_called()
        self.assertEqual(marker.read_text(),'existing')

    def test_windows_marker_dependencies_are_checked_against_target(self):
        # Builder is a script, not a runtime package. Bind its sibling explicitly.
        with patch.dict(sys.modules, {'bundle':bundle}):
            spec=importlib.util.spec_from_file_location('mapper_builder_test',SCRIPTS/'build_bundle.py')
            builder=importlib.util.module_from_spec(spec); spec.loader.exec_module(builder)
        records=[{'name':'parent','version':'1','requires_dist':['child>=2; sys_platform == "win32"']}]
        builder.check_closure(records,'macos-arm64')
        with self.assertRaisesRegex(ValueError,'INCOMPLETE_TARGET_DEPENDENCIES'):builder.check_closure(records,'windows-x64')
        builder.check_closure(records+[{'name':'child','version':'2','requires_dist':[]}],'windows-x64')

    def test_consistent_backup_does_not_modify_source_or_overwrite_destination(self):
        pid=demo(self.root)['project_id']
        with Repository(self.root,pid) as repo:source=repo.snapshot_data()
        parent=self.root/'backup';target=parent/pid
        self.assertEqual(maintenance.backup(self.root,pid,target)['status'],'backup_ok')
        with Repository(parent,pid) as copy:self.assertEqual(copy.snapshot_data(),source)
        with Repository(self.root,pid) as repo:self.assertEqual(repo.snapshot_data(),source)
        with self.assertRaises(FileExistsError):maintenance.backup(self.root,pid,target)
        if sys.platform!='win32':self.assertEqual((target/'mapper.sqlite3').stat().st_mode & 0o777,0o600)
