"""Application entry point"""
if __name__ == "__main__":
    import uvicorn
    from src.api.app import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
