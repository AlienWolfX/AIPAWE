from pathlib import Path
from typing import Optional
import torch
from ultralytics import YOLO


def _select_device() -> str:
    return "cuda:0" if torch.cuda.is_available() else "cpu"


def _model_path() -> Path:
    current = Path(__file__).resolve()
    for parent in list(current.parents)[:6]:
        candidate = parent / "model" / "weights" / "v1.pt"
        if candidate.exists():
            return candidate

    repo_root = current.parents[1] if len(current.parents) > 1 else current.parent
    return repo_root / "model" / "weights" / "v1.pt"


def infer_camera(imgsz: int = 640, conf: float = 0.25, save_dir: Optional[Path] = None, show_preview: bool = False):
    model_path = _model_path()
    if not model_path.exists():
        raise FileNotFoundError(f"Model not found at {model_path}. Place v1.pt there.")

    device = _select_device()
    model = YOLO(str(model_path))
    
    if hasattr(model, 'model') and hasattr(model.model, 'names'):
        model.model.names = {0: 'fire'}

    cv2 = None
    if show_preview:
        try:
            import cv2 as _cv2
            cv2 = _cv2
        except Exception:
            print("OpenCV not available, cannot show preview. Install opencv-python to enable preview.")
            show_preview = False

    if save_dir:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

    try:
        results = model.predict(source=0, imgsz=imgsz, conf=conf, device=device, stream=True)
        
        for i, res in enumerate(results):
            try:
                annotated = res.plot()
            except Exception:
                annotated = None

            src_name = Path(getattr(res, 'path', f'frame_{i}.jpg')).name
            
            if save_dir and annotated is not None and cv2 is not None:
                out_path = save_dir / src_name
                cv2.imwrite(str(out_path), annotated)

            if show_preview and annotated is not None and cv2 is not None:
                cv2.imshow('YOLO Preview - Color', annotated)
                
                gray = cv2.cvtColor(annotated, cv2.COLOR_BGR2GRAY)
                cv2.imshow('YOLO Preview - B&W', gray)
                
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    print('Preview closed by user.')
                    break

    finally:
        if show_preview and cv2 is not None:
            cv2.destroyAllWindows()

    print(f"Inference complete using model={model_path} on device={device}")
