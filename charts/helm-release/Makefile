CURRENT=$(pwd)
#_NAME := customize!project.name
NAME := diskover # Please do not edit this line! Managed by customize.sh
NAME := $(strip $(NAME))
OS := $(shell uname)
RELEASE_VERSION := $(shell cat ../../VERSION)

build: clean
	rm -rf requirements.lock
	helm dependency build
	helm lint

print: clean
	rm -rf requirements.lock
	helm template

install: clean build
	helm install . --name ${NAME}

upgrade: clean build
	helm upgrade ${NAME} .

delete:
	helm delete --purge ${NAME}

clean:
	rm -rf charts
	rm -rf ${NAME}*.tgz

release: clean
	helm dependency build
	helm lint
	helm init --client-only
	helm package .
	curl --fail -u$(CHARTMUSEUM_CREDS) -T "$(NAME)-$(shell sed -n 's/^version: //p' Chart.yaml).tgz" "$(CHART_REPOSITORY)/$(NAME)-$(shell sed -n 's/^version: //p' Chart.yaml).tgz"
	rm -rf ${NAME}*.tgz%

tag:
ifeq ($(OS),Darwin)
	sed -i "" -e "s/version:.*/version: $(RELEASE_VERSION)/" Chart.yaml
	sed -i "" -e "s/tag:.*/tag: $(RELEASE_VERSION)/" values.yaml
else ifeq ($(OS),Linux)
	sed -i -e "s/version:.*/version: $(RELEASE_VERSION)/" Chart.yaml
	sed -i -e "s|repository:.*|repository: $(DOCKER_REGISTRY)\/kayosportsau\/diskover|" values.yaml # Please do not edit this line! Managed by customize.sh
	sed -i -e "s/tag:.*/tag: $(RELEASE_VERSION)/" values.yaml
else
	echo "platfrom $(OS) not supported to release from"
	exit -1
endif
	git add --all
	git commit -m "release $(RELEASE_VERSION)" --allow-empty # if first release then no verion update is performed
	git tag -fa v$(RELEASE_VERSION) -m "Release version $(RELEASE_VERSION)"
	git push origin v$(RELEASE_VERSION)
