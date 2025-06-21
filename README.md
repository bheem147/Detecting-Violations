# 📹 Exam Monitoring System

A real-time webcam-based cheating detection system for online exams using computer vision and AI.

## 🚀 Features

- **Real-time Face Detection**: Monitors student's face position and orientation
- **Multiple Violation Detection**:
  - Face away from screen
  - Multiple people in frame
  - Phone usage detection
  - Looking down (possibly at notes/phone)
  - No person visible
- **Live Video Streaming**: Real-time webcam feed with detection overlays
- **Instant Alerts**: Immediate notifications when violations are detected
- **Web Dashboard**: Modern, responsive interface for monitoring
- **Adjustable Thresholds**: Customizable detection sensitivity

## 🛠️ Technologies Used

- **Python 3.11**
- **OpenCV** - Computer vision and camera handling
- **MediaPipe** - Face, hand, and pose detection
- **Flask** - Web framework
- **Flask-SocketIO** - Real-time communication
- **HTML/CSS/JavaScript** - Frontend interface

## 📋 Requirements

- Python 3.11 or higher
- Webcam
- Modern web browser (Chrome, Firefox, Safari, Edge)

## 🚀 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/exam-monitoring-system.git
   cd exam-monitoring-system
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   python app.py
   ```

4. **Open your browser:**
   Navigate to `http://localhost:5000`

## 📖 Usage

1. **Start Monitoring**: Click the "Start Monitoring" button
2. **View Live Feed**: Watch the real-time video with detection overlays
3. **Monitor Alerts**: Check the alerts panel for violations
4. **Stop Monitoring**: Click "Stop Monitoring" when done

## 🎯 Detection Features

### Face Detection
- **Green mesh overlay** on detected faces
- Tracks face position and orientation

### Hand Detection
- **Red dots** on hand landmarks
- Detects phone usage patterns

### Pose Detection
- **Yellow lines** for body pose
- Monitors overall body position

### Violation Types
- **Face Away**: Student looking away from screen
- **Multiple Faces**: More than one person detected
- **Phone Usage**: Hands in typical phone-holding position
- **Looking Down**: Head tilted down (possibly at notes)
- **No Person**: No face detected in frame

## ⚙️ Configuration

The system uses configurable thresholds for each violation type:
- Face away threshold: 2.0 seconds
- Multiple faces threshold: 3.0 seconds
- Phone usage threshold: 2.0 seconds
- No person threshold: 3.0 seconds

## 🔧 Customization

You can modify detection parameters in `monitoring_system.py`:
- Adjust detection confidence levels
- Change violation thresholds
- Add new violation types
- Customize alert messages

## 🚨 Alerts

The system provides real-time alerts for:
- Violation detection with timestamps
- Violation counts and statistics
- Visual and audio notifications

## 📱 Browser Compatibility

- Chrome (recommended)
- Firefox
- Safari
- Edge

## 🔒 Privacy & Security

- **Local Processing**: All video processing happens locally
- **No Data Storage**: Video is not recorded or stored
- **Real-time Only**: No persistent video data
- **Camera Permissions**: Requires explicit camera access

## 🐛 Troubleshooting

### Camera Issues
- Ensure camera permissions are granted
- Check if camera is being used by another application
- Try refreshing the browser page

### Performance Issues
- Close other applications using the camera
- Reduce browser tab count
- Ensure adequate lighting

### Detection Issues
- Ensure good lighting conditions
- Position face clearly in camera view
- Avoid rapid movements

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

If you encounter any issues or have questions, please open an issue on GitHub.

---

**Note**: This system is designed for educational and testing purposes. For production use in actual exams, ensure compliance with privacy laws and institutional policies. 
