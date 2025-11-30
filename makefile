.PHONY: all setup compile install run uninstall clean distclean format lint test rebuild dist generate-pot merge-translations help

BUILD_DIR = build
APP = luna

PODIR = po
POT = $(PODIR)/io.github.kingorgg.Luna.pot
POFILES = $(wildcard $(PODIR)/*.po)

all: setup compile install run

setup:
	mkdir -p $(BUILD_DIR)
	meson setup --reconfigure $(BUILD_DIR)

compile:
	meson compile -C $(BUILD_DIR) --verbose

install:
	meson install -C $(BUILD_DIR)

run:
	@if [ -x "$(BUILD_DIR)/$(APP)" ]; then \
		$(BUILD_DIR)/$(APP); \
	elif command -v $(APP) >/dev/null 2>&1; then \
		$(APP); \
	else \
		echo "Error: $(APP) not built or installed"; \
		exit 1; \
	fi

uninstall:
	@for f in \
		/usr/local/share/metainfo/io.github.kingorgg.Luna.metainfo.xml \
		/usr/local/share/glib-2.0/schemas/io.github.kingorgg.Luna.gschema.xml \
		/usr/local/share/applications/io.github.kingorgg.Luna.desktop \
		/usr/local/share/$(APP)/ \
		/usr/local/share/dbus-1/services/io.github.kingorgg.Luna.service \
		/usr/local/bin/$(APP); do \
		if [ -e $$f ]; then sudo rm -rf $$f; fi; \
	done
	@echo "Uninstallation complete."

clean:
	meson compile -C $(BUILD_DIR) --clean

distclean:
	rm -rf $(BUILD_DIR)

format:
	black src
	isort src

lint:
	flake8 src

test:
	python3 -m unittest discover -s tests -v

dist:
	meson dist -C $(BUILD_DIR)

rebuild: distclean setup compile

rebuild-install: distclean setup compile install

generate-pot:
	xgettext -c -k_ -kgettext_ --from-code=UTF-8 -f po/POTFILES.in -o po/io.github.kingorgg.Luna.pot

merge-translations:
	for pofile in $(POFILES); do \
		msgmerge --update --backup=none $$pofile $(POT); \
	done

help:
	@echo "Makefile commands:"
	@echo "  setup      		- Set up the build directory"
	@echo "  compile    		- Compile the application"
	@echo "  install    		- Install the application"
	@echo "  run        		- Run the application"
	@echo "  uninstall  		- Uninstall the application"
	@echo "  clean      		- Clean build files"
	@echo "  distclean  		- Remove build directory"
	@echo "  format     		- Format the source code"
	@echo "  lint       		- Lint the source code"
	@echo "  test       		- Run unit tests"
	@echo "  dist       		- Create a distribution package"
	@echo "  rebuild    		- Clean, set up, and compile the application"
	@echo "  rebuild-install 	- Rebuild and install the application"
	@echo "  generate-pot 		- Generates the pot file with new strings"
	@echo "  merge-translations 	- Updates translation files"
	@echo "  help      		- Show this help message"

