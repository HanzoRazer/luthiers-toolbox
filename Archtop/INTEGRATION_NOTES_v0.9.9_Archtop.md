
v0.9.9 (Archtop + Demo Runner)
- New: /exports/archtop route (csv | outline) wrapping archtop_contour_generator.py
- New: /demo/run route to enqueue multi_model_demo.json jobs into queue (requires server.lib.jobs.append_job).
To enable:
    from server.routes.archtop import router as archtop_router
    from server.routes.demo import router as demo_router
    app.include_router(archtop_router)
    app.include_router(demo_router)
