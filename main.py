from utils.inference import infer_camera


def main():
	infer_camera(imgsz=320, conf=0.25, show_preview=True)


if __name__ == "__main__":
	main()
