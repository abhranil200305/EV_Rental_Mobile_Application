#app/controllers/vehicle/__init__.py
from .create_vehicle import router as create_vehicle_router
from .get_vehicle import router as get_vehicle_router
from .update_vehicle import router as update_vehicle_router
from .delete_vehicle import router as delete_vehicle_router

routers = [
    create_vehicle_router,
    get_vehicle_router,
    update_vehicle_router,
    delete_vehicle_router,
]