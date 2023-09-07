import uvicorn

from app import Routes

if __name__ == '__main__':
    app = Routes.app
    uvicorn.run(app, host='127.0.0.1', port=8000)

