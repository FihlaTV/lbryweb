.PHONY: js
js:
	scripts/build_js.sh

.PHONY: test
test:
	(cd lbryweb && pytest)

.PHONY: runserver
runserver:
	lbryweb/manage.py runserver
