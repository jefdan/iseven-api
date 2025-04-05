from fastapi import FastAPI, HTTPException
import torch
import torch.nn as nn
import numpy as np
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from advertisements import generate_advertisement

# Define the model.
class SimpleNN(nn.Module):
    def __init__(self):
        super(SimpleNN, self).__init__()
        self.fc1 = nn.Linear(64, 32)
        self.fc2 = nn.Linear(32, 16)
        self.fc3 = nn.Linear(16, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = self.fc1(x)
        x = torch.nn.functional.relu(x)
        x = self.fc2(x)
        x = torch.nn.functional.relu(x)
        x = self.fc3(x)
        x = self.sigmoid(x)
        return x

def int_to_binary_array(x, width=64):
    return np.array(list(np.binary_repr(x, width=width)), dtype=np.float32)

app = FastAPI(
    title="IsEven API",
    description="An API to predict if a number is even or odd using a neural network.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    global model, device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = SimpleNN().to(device)
    model_path = "iseven-ml.pth"
    try:
        model.load_state_dict(torch.load(model_path, map_location=device, weights_only=True))
        model.eval()
    except Exception as e:
        print(f"Error loading model: {e}")
        raise RuntimeError(f"Failed to load model from {model_path}")

@app.get("/")
async def root():
    return {"message": "Welcome to the IsEven API! Use /predict/{number} to check if a number is even or odd."}

@app.get("/predict/{number}")
async def predict(number: int):
    try:
        # Convert the number to a binary representation.
        binary_data = int_to_binary_array(number)
        # Convert to tensor and move to device.
        input_tensor = torch.tensor([binary_data], dtype=torch.float32).to(device)
        
        # Get prediction.
        with torch.no_grad():
            prediction = model(input_tensor)
        
        # Determine if even or odd based on prediction threshold.
        is_even = bool(prediction.item() < 0.5)
        
        return {
            "even": is_even,
            "odd": not is_even,
            "prediction": prediction.item(),
            "advertisement": generate_advertisement(), # :)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=50000, reload=True)
