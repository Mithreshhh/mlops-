import os
import pandas as pd
import mlflow
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.preprocessing import LabelEncoder
from prometheus_fastapi_instrumentator import Instrumentator

TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
MODEL_NAME = "StudentPerformanceModel"
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "student-mat.csv")

CATEGORICAL_COLS = [
    "school", "sex", "address", "famsize", "Pstatus",
    "Mjob", "Fjob", "reason", "guardian",
    "schoolsup", "famsup", "paid", "activities",
    "nursery", "higher", "internet", "romantic",
]

FEATURE_COLS = [
    "school", "sex", "age", "address", "famsize", "Pstatus",
    "Medu", "Fedu", "Mjob", "Fjob", "reason", "guardian",
    "traveltime", "studytime", "failures",
    "schoolsup", "famsup", "paid", "activities",
    "nursery", "higher", "internet", "romantic",
    "famrel", "freetime", "goout", "Dalc", "Walc",
    "health", "absences", "G1", "G2",
]

model = None
label_encoders: dict[str, LabelEncoder] = {}


def load_model():
    global model
    mlflow.set_tracking_uri(TRACKING_URI)
    for stage in ["Production", "None"]:
        try:
            uri = f"models:/{MODEL_NAME}/{stage}"
            model = mlflow.pyfunc.load_model(uri)
            print(f"Loaded model: {uri}")
            return
        except Exception:
            print(f"Stage '{stage}' not found, trying next...")
    raise RuntimeError(f"Could not load model '{MODEL_NAME}' from any stage")


def fit_label_encoders():
    df = pd.read_csv(DATA_PATH, sep=";")
    for col in CATEGORICAL_COLS:
        le = LabelEncoder()
        le.fit(df[col])
        label_encoders[col] = le
    print(f"Fitted {len(label_encoders)} label encoders from training data")


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_model()
    fit_label_encoders()
    yield


app = FastAPI(
    title="Student Performance Predictor",
    description="Predict student pass/fail using MLflow-registered model",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


class StudentInput(BaseModel):
    school: str
    sex: str
    age: int
    address: str
    famsize: str
    Pstatus: str
    Medu: int
    Fedu: int
    Mjob: str
    Fjob: str
    reason: str
    guardian: str
    traveltime: int
    studytime: int
    failures: int
    schoolsup: str
    famsup: str
    paid: str
    activities: str
    nursery: str
    higher: str
    internet: str
    romantic: str
    famrel: int
    freetime: int
    goout: int
    Dalc: int
    Walc: int
    health: int
    absences: int
    G1: int
    G2: int

    model_config = {"json_schema_extra": {
        "examples": [{
            "school": "GP", "sex": "F", "age": 18, "address": "U",
            "famsize": "GT3", "Pstatus": "A", "Medu": 4, "Fedu": 4,
            "Mjob": "at_home", "Fjob": "teacher", "reason": "course",
            "guardian": "mother", "traveltime": 2, "studytime": 2,
            "failures": 0, "schoolsup": "yes", "famsup": "no",
            "paid": "no", "activities": "no", "nursery": "yes",
            "higher": "yes", "internet": "no", "romantic": "no",
            "famrel": 4, "freetime": 3, "goout": 4, "Dalc": 1,
            "Walc": 1, "health": 3, "absences": 6, "G1": 5, "G2": 6,
        }]
    }}


class PredictionResponse(BaseModel):
    prediction: int
    label: str
    probability: float


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=PredictionResponse)
def predict(student: StudentInput):
    try:
        data = student.model_dump()
        df = pd.DataFrame([data], columns=FEATURE_COLS)

        for col in CATEGORICAL_COLS:
            le = label_encoders[col]
            val = df[col].iloc[0]
            if val not in le.classes_:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown value '{val}' for column '{col}'. "
                           f"Expected one of: {list(le.classes_)}",
                )
            df[col] = le.transform(df[col])

        prediction = int(model.predict(df)[0])

        proba = model._model_impl.predict_proba(df)[0]
        probability = float(proba[1])

        return PredictionResponse(
            prediction=prediction,
            label="PASS" if prediction == 1 else "FAIL",
            probability=round(probability, 4),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
