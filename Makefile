.PHONY: clean lint run package upload cloudformation

env:
	virtualenv env
	. env/bin/activate && pip install -r requirements.txt -r requirements-dev.txt

clean:
	- rm -rf env BUILD pip-repo
	- rm app.zip
	- find . -name "*.pyc" | xargs rm

lint: env
	. env/bin/activate && flake8 src/ tests/ stackerformation/

run: env lint
	# . env/bin/activate && cd src && gunicorn app:app
	. env/bin/activate && python src/app.py

package: clean
	mkdir -p BUILD pip-repo
	virtualenv env
	. env/bin/activate && pip download -r requirements.txt -d pip-repo
	cp -r src BUILD/
	cp -r pip-repo BUILD/
	cd BUILD; zip -r -X app.zip .
	mv BUILD/app.zip .

upload: package
	aws s3 cp app.zip s3://oliviervg1-code/euro2016/app.zip

cloudformation: env lint
	cp -r stackerformation/stacks env/lib/python2.7/site-packages/
	. env/bin/activate && stacker build -r eu-west-1 stackerformation/conf/euro2016.env stackerformation/conf/euro2016.yaml
