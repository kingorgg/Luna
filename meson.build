project('luna',
          version: '49.9',
    meson_version: '>= 1.0.0',
  default_options: [ 'warning_level=2', 'werror=false', ],
)

i18n = import('i18n')
gnome = import('gnome')

APPLICATION_ID = 'io.github.kingorgg.Luna'

subdir('data')
subdir('src')
subdir('po')

gnome.post_install(
     glib_compile_schemas: true,
    gtk_update_icon_cache: true,
  update_desktop_database: true,
)

test(
  'python-tests',
  find_program('python3'),
  args: ['-m', 'unittest', 'discover', '-s', meson.project_source_root() / 'tests', '-v'],
  env: {'PYTHONPATH': meson.project_source_root()}
)
