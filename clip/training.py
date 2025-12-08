# training.py (수정본)
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import clip
from pathlib import Path
from torchvision import transforms
import json
from PIL import Image

# ===============================
# SlideDataset 정의
# ===============================
class SlideDataset(torch.utils.data.Dataset):
    def __init__(self, image_dir, label_dir, transform=None):
        self.image_paths = sorted(list(Path(image_dir).glob("*.jpg")))
        self.label_paths = sorted(list(Path(label_dir).glob("*.json")))
        self.transform = transform

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img = Image.open(self.image_paths[idx]).convert("RGB")
        if self.transform:
            img = self.transform(img)

        with open(self.label_paths[idx], "r", encoding="utf-8") as f:
            data = json.load(f)
        # overall_scores를 tensor로 변환 (layout, text_amount, color_contrast, visuals, consistency 순)
        scores = data.get("overall_scores", {})
        score_tensor = torch.tensor([
            scores.get("layout", 0.0),
            scores.get("text_amount", 0.0),
            scores.get("color_contrast", 0.0),
            scores.get("visuals", 0.0),
            scores.get("consistency", 0.0)
        ], dtype=torch.float32)
        return img, score_tensor

# ===============================
# CLIPClassifier + Linear probe
# ===============================
class CLIPClassifier(nn.Module):
    def __init__(self, output_dim=5, return_attention=False):
        super().__init__()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.clip_model, _ = clip.load("ViT-B/32", device=self.device, jit=False)
        self.clip_model.eval()
        self.fc = nn.Linear(self.clip_model.visual.output_dim, output_dim)
        self.return_attention = return_attention
        self.to(self.device)

    def forward(self, x):
        with torch.no_grad():
            features = self.clip_model.encode_image(x)
        features = features / features.norm(dim=-1, keepdim=True)
        logits = self.fc(features)
        return logits

# ===============================
# Training Loop
# ===============================
if __name__ == "__main__":
    device = "cuda" if torch.cuda.is_available() else "cpu"

    DATA_DIR = Path(r"C:\Users\naeun\capstone\data")
    IMAGE_DIR = DATA_DIR / "images"
    LABEL_DIR = DATA_DIR / "labels"

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.48145466, 0.4578275, 0.40821073],
            std=[0.26862954, 0.26130258, 0.27577711]
        )
    ])

    dataset = SlideDataset(IMAGE_DIR, LABEL_DIR, transform=transform)
    dataloader = DataLoader(dataset, batch_size=8, shuffle=True)  # 메모리 고려

    model = CLIPClassifier(output_dim=5, return_attention=False)
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.fc.parameters(), lr=1e-3)

    num_epochs = 10
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0
        for imgs, scores in dataloader:
            imgs, scores = imgs.to(device), scores.to(device)
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, scores)
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * imgs.size(0)
        print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {total_loss/len(dataset):.4f}")

    torch.save(model.state_dict(), "clip_linear_probe.pth")
    print("✅ Linear Probe 학습 완료 및 저장됨!")
