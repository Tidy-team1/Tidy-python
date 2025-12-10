import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import clip
from pathlib import Path
from PIL import Image
import json

# ===============================
# SlideDataset 정의 (기존과 동일)
# ===============================
class SlideDataset(torch.utils.data.Dataset):
    def __init__(self, image_dir, label_dir, transform=None):
        self.image_paths = sorted(list(Path(image_dir).glob("*.jpg")) + list(Path(image_dir).glob("*.png")))
        self.label_paths = {p.stem: p for p in Path(label_dir).glob("*.json")}
        self.transform = transform

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        img_path = self.image_paths[idx]
        img = Image.open(img_path).convert("RGB")
        
        if self.transform:
            img = self.transform(img)

        label_path = self.label_paths.get(img_path.stem)
        if not label_path:
            score_tensor = torch.tensor([0.5]*5, dtype=torch.float32)
        else:
            with open(label_path, "r", encoding="utf-8") as f:
                data = json.load(f)
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
# CLIPClassifier (학습된 구조와 변수명 일치화)
# ===============================
class CLIPClassifier(nn.Module):
    def __init__(self, output_dim=5, device='cpu'):
        super().__init__()
        
        # [수정 1] 변수명을 'clip_model' -> 'clip'으로 변경 (저장된 pth 파일과 일치시키기 위함)
        self.clip, self.preprocess = clip.load("ViT-B/32", device=device, jit=False)
        
        for p in self.clip.parameters():
            p.requires_grad = False
            
        self.clip.eval()
        
        feature_dim = self.clip.visual.output_dim

        # [수정 2] 변수명을 'fc' -> 'probe'로 변경 (저장된 pth 파일과 일치시키기 위함)
        # [수정 3] LayerNorm 추가 (학습 코드 StableLinearProbe와 구조 일치시키기 위함)
        self.probe = nn.Sequential(
            nn.LayerNorm(feature_dim),
            nn.Linear(feature_dim, 256),
            nn.ReLU(inplace=True),
            nn.Linear(256, output_dim),
            nn.Sigmoid()
        )
        
        # 가중치 초기화
        for m in self.probe:
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
        
        self.to(device)

    def forward(self, x):
        with torch.no_grad():
            # self.clip 사용
            features = self.clip.encode_image(x).float()
            
        # self.probe 사용
        logits = self.probe(features)
        return logits

# ===============================
# Training Loop (실행 시 사용)
# ===============================
if __name__ == "__main__":
    # (이 부분은 모델 구조 수정과 관계 없으므로 기존 로직 유지)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🔥 Device: {device}")

    # 경로 설정
    DATA_DIR = Path(r"C:\Users\naeun\capstone\data")
    IMAGE_DIR = DATA_DIR / "images"
    LABEL_DIR = DATA_DIR / "labels"

    model = CLIPClassifier(output_dim=5, device=device)
    print("✅ Using CLIP built-in preprocess:", model.preprocess)
    
    dataset = SlideDataset(IMAGE_DIR, LABEL_DIR, transform=model.preprocess)
    print(f"📊 Dataset size: {len(dataset)}")
    
    if len(dataset) > 0:
        dataloader = DataLoader(dataset, batch_size=16, shuffle=True)
        criterion = nn.MSELoss() 
        # optimizer도 model.probe로 수정
        optimizer = optim.Adam(model.probe.parameters(), lr=1e-3)

        num_epochs = 10
        print("🚀 Training Start...")
        
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
                
            avg_loss = total_loss / len(dataset)
            print(f"Epoch [{epoch+1}/{num_epochs}], Loss: {avg_loss:.4f}")

        save_path = "clip_linear_probe.pth"
        torch.save(model.state_dict(), save_path)
        print(f"✅ Linear Probe 학습 완료 및 저장됨! -> {save_path}")
