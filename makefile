.PHONY: setup compile install run uninstall clean distclean

all: setup compile install run

setup:
	meson setup --reconfigure build

compile:
	meson compile -C build

install:
	meson install -C build

run:
	luna

uninstall:
	sudo rm /usr/local/share/metainfo/io.github.kingorgg.Luna.metainfo.xml
	sudo rm /usr/local/share/glib-2.0/schemas/io.github.kingorgg.Luna.gschema.xml
	sudo rm /usr/local/share/applications/io.github.kingorgg.Luna.desktop
	sudo rm -rf /usr/local/share/luna/
	sudo rm /usr/local/share/dbus-1/services/io.github.kingorgg.Luna.service
	sudo rm /usr/local/bin/luna

clean:
	meson compile -C build --clean

distclean:
	rm -rf build

format:
	black src
	isort src

lint:
	flake8 src

test:
	python3 -m unittest discover -s tests -v