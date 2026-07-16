.PHONY: build run debug clean

build:
	@bash scripts/build_app.sh release

debug:
	@bash scripts/build_app.sh debug

run: build
	@open build/AppCleaner.app

clean:
	@rm -rf .build build
