# IoT-Driven Paddy Moisture Monitoring and Grain Quality Management Platform

Sensor (ESP32) -> FastAPI -> SQLite -> React dashboard.

## Run the backend
```
cd backend
python -m venv venv && source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest                                              # run the tests
uvicorn main:app --reload                           # API docs at http://localhost:8000/docs
```
In a second terminal (no hardware needed): `python simulate.py`

## Run the dashboard
```
cd frontend
npm install
npm run dev                                         # http://localhost:5173
```

## How it works
- `quality.py`: moisture thresholds (dry < 12%, optimal 12-14%, excess > 14%) and alert rules. Verify these values with your guide.
- `main.py`: endpoints `POST /devices`, `POST /readings`, `GET /readings`, `GET /summary`, `GET /alerts`, `POST /alerts/{id}/ack`.
- Devices authenticate with the `X-API-Key` header. Set `DEVICE_API_KEY` as an environment variable and change `"change-me"` everywhere.
- `esp32/paddy_sensor.ino`: sends a reading every 30 s. **The probe must be calibrated** against grain samples of known moisture.

## Ideas to extend (and to discuss in your viva)
User login (JWT), PostgreSQL, email/SMS alerts, an ML model trained on real readings, Docker deployment.
