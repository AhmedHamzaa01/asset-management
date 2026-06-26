from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


# auth_headers = {
#     "Authorization": (
#         "Bearer YOUR_ACCESS_TOKEN"
#     )
# }   
# a non expired token can be generated using the /api/v1/auth/login endpoint with valid credentials.