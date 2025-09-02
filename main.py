import torch
import cv2
from PIL import Image
from fastapi import FastAPI, File, UploadFile
import io
import nest_asyncio
import uvicorn

# =============================
# Modelo Siamese
# =============================
class SmallCNN(torch.nn.Module):
    def __init__(self, out_dim=128):
        super().__init__()
        self.conv = torch.nn.Sequential(
            torch.nn.Conv2d(1,32,3,padding=1), torch.nn.ReLU(), torch.nn.MaxPool2d(2),
            torch.nn.Conv2d(32,64,3,padding=1), torch.nn.ReLU(), torch.nn.MaxPool2d(2),
            torch.nn.Conv2d(64,128,3,padding=1), torch.nn.ReLU(), torch.nn.AdaptiveAvgPool2d((1,1))
        )
        self.fc = torch.nn.Linear(128, out_dim)
    def forward(self, x):
        x = self.conv(x)
        x = x.view(x.size(0), -1)
        x = self.fc(x)
        return torch.nn.functional.normalize(x, dim=1)

class SiameseNet(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.embed = SmallCNN()
    def forward(self, a, b):
        ea = self.embed(a)
        eb = self.embed(b)
        dist = torch.nn.functional.pairwise_distance(ea, eb)
        return dist

# =============================
# Preprocesamiento
# =============================
def preprocess_signature(path, img_size=(220,155)):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    _, th = cv2.threshold(img,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)
    coords = cv2.findNonZero(th)
    x,y,w,h = cv2.boundingRect(coords)
    crop = th[y:y+h, x:x+w]
    resized = cv2.resize(crop, img_size[::-1])
    return resized.astype('float32')/255.0

# =============================
# Cargar modelo
# =============================
device = "cuda" if torch.cuda.is_available() else "cpu"
model = SiameseNet()
model.load_state_dict(torch.load("./models/verify_signature_model.pth", map_location=device))
model.eval()

THRESHOLD = 0.078  # ajusta según tu Colab

# =============================
# FastAPI
# =============================
app = FastAPI()

@app.post("/verify")
async def verify(file_ref: UploadFile = File(...), file_test: UploadFile = File(...)):
    ref_bytes = await file_ref.read()
    test_bytes = await file_test.read()
    ref_img = Image.open(io.BytesIO(ref_bytes)).convert("L")
    test_img = Image.open(io.BytesIO(test_bytes)).convert("L")
    
    # Guardar temporal
    ref_path = "/tmp/ref.png"
    test_path = "/tmp/test.png"
    ref_img.save(ref_path)
    test_img.save(test_path)

    # Preprocesar
    A = torch.tensor(preprocess_signature(ref_path)).unsqueeze(0).unsqueeze(0).float().to(device)
    B = torch.tensor(preprocess_signature(test_path)).unsqueeze(0).unsqueeze(0).float().to(device)

    # Inferencia
    with torch.no_grad():
        dist = model(A, B).item()
    decision = "genuine" if dist < THRESHOLD else "forged"
    return {"distance": dist, "decision": decision}

# =============================
# Correr servidor
# =============================
if __name__ == "__main__":
    nest_asyncio.apply()
    uvicorn.run(app, host="127.0.0.1", port=8000)
