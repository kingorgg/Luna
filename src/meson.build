pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'luna'
gnome = import('gnome')

blueprints = custom_target('blueprints',
    input: files(
        '../data/ui/window.blp',
        '../data/ui/new_period.blp',
        '../data/ui/period_page.blp',
        '../data/ui/day_row.blp',
        '../data/ui/delete_period_dialog.blp',
	),
    output: [
        'window.ui',
        'new_period.ui',
        'period_page.ui',
        'day_row.ui',
        'delete_period_dialog.ui',
    ],
    command: [
    find_program('blueprint-compiler'),
    'batch-compile',
    meson.current_build_dir(),
    meson.project_source_root() / 'data' / 'ui',
    '@INPUT@'
  ],
)

gnome.compile_resources('luna',
    'luna.gresource.xml',
     gresource_bundle: true,
     dependencies: blueprints,
     install: true,
     install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)
conf.set('application_id', APPLICATION_ID)

configure_file(
     input: 'luna.in',
     output: 'luna',
     configuration: conf,
     install: true,
     install_dir: get_option('bindir'),
     install_mode: 'r-xr-xr-x'
)

luna_sources = [
     '__init__.py',
     'constants.py',
     'data_store.py',
     'day_row.py',
     'delete_period_dialog.py',
     'logic.py',
     'main.py',
     'models.py',
     'new_period.py',
     'period_page.py',
     'sqlite_store.py',
     'window.py'
]

install_data(luna_sources, install_dir: moduledir)
