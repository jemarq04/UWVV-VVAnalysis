RUFF      := $(shell which ruff 2>/dev/null || echo uvx ruff)
PRECOMMIT := $(shell which pre-commit 2>/dev/null || echo uvx pre-commit)

build:
	scram b -j 12 UWVV

lint:
	$(PRECOMMIT) run -a

ruff-check:
	$(RUFF) check

format: clang-format ruff-format

clang-format:
	find . -regex '.*\.\(cpp\|hpp\|cc\|cxx\|h\)' | xargs clang-format -i

ruff-format:
	$(RUFF) format
