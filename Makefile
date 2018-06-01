run: build
	docker run -p 8000:8000 -e XBOX_IP=192.168.2.5 -e XBOX_LIVEID=FD00000000000000 xbox-rpc python ./app.py

app: build
	docker-compose up
	docker-compose stop

build:
	docker build . -t xbox-rpc
