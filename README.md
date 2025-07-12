
## FastAPI 서버 실행
* uvicorn main:app --reload

## Svelte 서버 실행
* npm run dev

## alembic
* alembic init migrations
* alembic revision --autogenerate
* alembic upgrade head

## docker
docker build -t myapi . 
docker run --name myapi-container -dit -p 8000:8000 -v $(pwd) myapi
docker ps -a
docker attach CONTAINER_NAME
docker exec -it CONTAINER_NAME /bin/bash
uvicorn main:app --reload  --host 0.0.0.0
# JanDi-backend
