"""
AIPAWE - Fire Detection Test Script (Windows)
View YOLOv11 inference results in real-time

Usage:
    python test_inference.py
    
Press 'q' to quit
Press 's' to save current frame
Press 'c' to toggle confidence display
"""

import cv2
import sys
import os
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.utils_common import ConfigLoader
from utils.logger import AIPAWELogger
from utils.fire_detector import FireDetector


class InferenceViewer:
    """Real-time fire detection inference viewer"""
    
    def __init__(self):
        print("=" * 60)
        print("AIPAWE - Fire Detection Inference Viewer")
        print("=" * 60)
        print("\nControls:")
        print("  Q - Quit")
        print("  S - Save current frame")
        print("  C - Toggle confidence display")
        print("  + - Increase confidence threshold")
        print("  - - Decrease confidence threshold")
        print("\n" + "=" * 60)
        
        # Load configuration
        config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
        self.config = ConfigLoader(config_path)
        
        # Initialize logger
        self.logger = AIPAWELogger(self.config)
        
        # Initialize detector
        self.detector = FireDetector(self.config, self.logger)
        
        # Display settings
        self.show_confidence = True
        self.frame_count = 0
        self.fps = 0
        self.last_fps_time = cv2.getTickCount()
        
        # Get initial threshold
        self.confidence_threshold = self.config.get('detection', 'confidence_threshold', default=0.65)
        
        print(f"\nCamera: {self.detector.frame_width}x{self.detector.frame_height}")
        print(f"Model: {self.detector.model_path}")
        print(f"Confidence Threshold: {self.confidence_threshold:.2%}")
        print("\nStarting inference...\n")
    
    def calculate_fps(self):
        """Calculate current FPS"""
        self.frame_count += 1
        if self.frame_count >= 10:
            current_time = cv2.getTickCount()
            elapsed = (current_time - self.last_fps_time) / cv2.getTickFrequency()
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self.last_fps_time = current_time
    
    def draw_info_panel(self, frame, detections):
        """Draw information panel on frame"""
        height, width = frame.shape[:2]
        
        # Semi-transparent overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 80), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # Title
        cv2.putText(frame, "AIPAWE - Fire Detection", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Stats
        stats_text = f"FPS: {self.fps:.1f} | Detections: {len(detections)} | Threshold: {self.confidence_threshold:.0%}"
        cv2.putText(frame, stats_text, (10, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Controls hint
        cv2.putText(frame, "Q:Quit S:Save C:Toggle +/-:Threshold", (10, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        return frame
    
    def draw_detections(self, frame, detections):
        """Draw detection boxes and labels"""
        for i, det in enumerate(detections):
            x, y, w, h = det.bbox
            
            # Color based on confidence (green -> yellow -> red)
            if det.confidence >= 0.8:
                color = (0, 0, 255)  # Red - high confidence
            elif det.confidence >= 0.6:
                color = (0, 165, 255)  # Orange - medium confidence
            else:
                color = (0, 255, 255)  # Yellow - low confidence
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Draw center point
            center_x, center_y = det.center
            cv2.circle(frame, (center_x, center_y), 5, color, -1)
            cv2.circle(frame, (center_x, center_y), 8, color, 2)
            
            # Draw crosshair
            cv2.line(frame, (center_x - 15, center_y), (center_x + 15, center_y), color, 1)
            cv2.line(frame, (center_x, center_y - 15), (center_x, center_y + 15), color, 1)
            
            if self.show_confidence:
                # Label background
                label = f"Fire {i+1}: {det.confidence:.1%}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                cv2.rectangle(frame, (x, y - 25), (x + label_size[0] + 10, y), color, -1)
                
                # Label text
                cv2.putText(frame, label, (x + 5, y - 8),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                # Angle info
                angle_text = f"Az:{det.azimuth:+.1f}° El:{det.elevation:+.1f}°"
                cv2.putText(frame, angle_text, (x + 5, y + h + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        return frame
    
    def run(self):
        """Main viewing loop"""
        cv2.namedWindow('AIPAWE Fire Detection', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('AIPAWE Fire Detection', 
                        self.detector.frame_width * 2, 
                        self.detector.frame_height * 2)
        
        saved_count = 0
        
        try:
            while True:
                # Capture frame
                frame = self.detector.capture_frame()
                
                if frame is None:
                    print("ERROR: Failed to capture frame")
                    break
                
                # Run detection
                detections = self.detector.detect_fires(frame)
                
                # Filter by current threshold
                detections = [d for d in detections if d.confidence >= self.confidence_threshold]
                
                # Draw detections
                display_frame = self.draw_detections(frame.copy(), detections)
                
                # Draw info panel
                display_frame = self.draw_info_panel(display_frame, detections)
                
                # Calculate FPS
                self.calculate_fps()
                
                # Display
                cv2.imshow('AIPAWE Fire Detection', display_frame)
                
                # Handle keyboard input
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q') or key == ord('Q'):
                    print("\nQuitting...")
                    break
                
                elif key == ord('s') or key == ord('S'):
                    # Save current frame
                    filename = f"detection_{saved_count:04d}.jpg"
                    cv2.imwrite(filename, display_frame)
                    saved_count += 1
                    print(f"Saved: {filename}")
                
                elif key == ord('c') or key == ord('C'):
                    # Toggle confidence display
                    self.show_confidence = not self.show_confidence
                    status = "ON" if self.show_confidence else "OFF"
                    print(f"Confidence display: {status}")
                
                elif key == ord('+') or key == ord('='):
                    # Increase threshold
                    self.confidence_threshold = min(1.0, self.confidence_threshold + 0.05)
                    print(f"Confidence threshold: {self.confidence_threshold:.0%}")
                
                elif key == ord('-') or key == ord('_'):
                    # Decrease threshold
                    self.confidence_threshold = max(0.0, self.confidence_threshold - 0.05)
                    print(f"Confidence threshold: {self.confidence_threshold:.0%}")
                
                # Print detections to console
                if detections:
                    det_info = ", ".join([f"{d.confidence:.1%}" for d in detections])
                    print(f"\rFires detected: {len(detections)} [{det_info}]", end="")
                else:
                    print("\rNo fires detected" + " " * 30, end="")
        
        except KeyboardInterrupt:
            print("\n\nInterrupted by user")
        
        finally:
            # Cleanup
            self.detector.cleanup()
            cv2.destroyAllWindows()
            print("\nInference viewer closed.")


def main():
    """Entry point"""
    viewer = InferenceViewer()
    viewer.run()


if __name__ == "__main__":
    main()
