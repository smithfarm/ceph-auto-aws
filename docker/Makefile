TARGETS := \
	openSUSE_13.2 \
	openSUSE_Leap_42.1 \
	openSUSE_Tumbleweed

.PHONY: all
all: $(TARGETS)

openSUSE_13.2:
	cp Dockerfile.in Dockerfile
	sed -i 's/BASE_IMAGE/opensuse:13.2/' Dockerfile
	sed -i 's/BUILD_TARGET/openSUSE_13.2/' Dockerfile
	docker build -t aws-13.2 .

openSUSE_Leap_42.1:
	cp Dockerfile.in Dockerfile
	sed -i 's/BASE_IMAGE/opensuse:42.1/' Dockerfile
	sed -i 's/BUILD_TARGET/openSUSE_Leap_42.1/' Dockerfile
	docker build -t aws-42.1 .

openSUSE_Tumbleweed:
	cp Dockerfile.in Dockerfile
	sed -i 's/BASE_IMAGE/opensuse:tumbleweed/' Dockerfile
	sed -i 's/BUILD_TARGET/openSUSE_Tumbleweed/' Dockerfile
	docker build -t aws-tumbleweed .
