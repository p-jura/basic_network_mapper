from PyInstaller.utils.hooks import collect_data_files, collect_submodules
module_collection_mode = 'py'
datas = collect_data_files('setuptools')
hiddenimports = collect_submodules('setuptools._vendor.autocommand')
