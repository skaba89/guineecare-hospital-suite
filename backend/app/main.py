from fastapi import FastAPI

app = FastAPI(
    title="GuinéeCare Hospital Suite API",
    version="0.1.0",
    description="API MVP pour la plateforme hospitalière GuinéeCare."
)


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "guineecare-backend"}


@app.get("/api/v1")
def api_root():
    return {
        "name": "GuinéeCare Hospital Suite",
        "version": "0.1.0",
        "modules": [
            "auth",
            "facilities",
            "patients",
            "admissions",
            "clinical",
            "emergency",
            "hospitalization",
            "pharmacy",
            "laboratory",
            "billing",
            "reporting"
        ]
    }
