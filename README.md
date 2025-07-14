
## FastAPI 서버 실행
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

## React 서버 실행
npm run dev

## alembic
alembic init migrations
alembic revision --autogenerate
alembic upgrade head

alembic revision --autogenerate -m "change_xxx"
alembic upgrade head

alembic stamp head
alembic revision --autogenerate -m "init"
alembic upgrade head

## celery
* 별도의 터미널에서 실행
# 워커
celery -A scheduler.celery_app.celery_app \
       --broker redis://localhost:6379/0 \
       worker --loglevel info

# 비트
celery -A scheduler.celery_app.celery_app \
       --broker redis://localhost:6379/0 \
       beat   --loglevel info


## docker
docker build -t myapi . 
docker run --name myapi-container -dit -p 8000:8000 -v $(pwd) myapi
docker ps -a
docker attach CONTAINER_NAME
docker exec -it CONTAINER_NAME /bin/bash
uvicorn main:app --reload  --host 0.0.0.0
