.PHONY: clean lint run package upload cloudformation

export GIT_HASH=$(shell git log -1 --format="%H")

env:
	virtualenv env
	. env/bin/activate && pip install -r requirements.txt -r requirements-dev.txt

clean:
	- rm -rf env BUILD pip-repo
	- rm app.zip
	- rm src/euro2016.db
	- find . -name "*.pyc" | xargs rm

lint: env
	. env/bin/activate && flake8 src/ lambda/ stackerformation/

run: env lint
	# . env/bin/activate && cd src && gunicorn app:app
	. env/bin/activate && cd src && python app.py

lambda-clean:
	- rm lambda/config{.cfg,.cfg.bak}
	- rm lambda/{models.py,football_data_client.py}

lambda-prepare: env lint
	cp src/{models.py,football_data_client.py,config/config.cfg} lambda/

lambda-run: lambda-clean lambda-prepare
	sed -i.bak -e 's|sqlite:///euro2016.db|sqlite:///../src/euro2016.db|' lambda/config.cfg
	. env/bin/activate && cd lambda && python update_points.py

package: clean
	mkdir -p BUILD pip-repo
	virtualenv env
	. env/bin/activate && pip download -r requirements.txt -d pip-repo
	cp -r src/* BUILD/
	cp -r pip-repo BUILD/
	cp requirements.txt BUILD/
	cd BUILD; zip -r -X app.zip .
	mv BUILD/app.zip .

upload: package
	aws s3 cp app.zip s3://oliviervg1-code/euro2016/app-$$GIT_HASH.zip

cloudformation: clean env lint
	cp -r stackerformation/stacks env/lib/python2.7/site-packages/
	. env/bin/activate && stacker build -r eu-west-1 -p AppVersion=$$GIT_HASH -p DBPassword=$$DBPassword_cloudreach stackerformation/conf/euro2016.env stackerformation/conf/euro2016-cloudreach.yaml
	. env/bin/activate && stacker build -r eu-west-1 -p AppVersion=$$GIT_HASH -p DBPassword=$$DBPassword_www stackerformation/conf/euro2016.env stackerformation/conf/euro2016-www.yaml
