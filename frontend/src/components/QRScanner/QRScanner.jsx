import { useState, useRef, useEffect } from 'react';
import './QRScanner.css';

const QRScanner = ({ onScan, onClose }) => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [scannedCode, setScannedCode] = useState(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, []);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' }
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        setIsStreaming(true);
        setError(null);
      }
    } catch (err) {
      setError('Camera access denied. Please enable camera permissions.');
      console.error('Camera error:', err);
    }
  };

  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
      videoRef.current.srcObject = null;
    }
    setIsStreaming(false);
  };

  const captureFrame = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const context = canvas.getContext('2d');
    context.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    // Simple QR code detection using jsQR library (fallback to text input)
    const imageData = context.getImageData(0, 0, canvas.width, canvas.height);
    
    // For now, show manual input since we're not including jsQR library
    // In production, integrate jsQR: https://github.com/cozmo/jsQR
    showManualInput();
  };

  const showManualInput = () => {
    const qrCode = prompt('Enter QR code manually or paste from camera:');
    if (qrCode && qrCode.trim()) {
      setScannedCode(qrCode.trim());
      handleScannedCode(qrCode.trim());
    }
  };

  const handleScannedCode = (code) => {
    stopCamera();
    onScan(code);
    setScannedCode(code);
  };

  return (
    <div className="qr-scanner-modal">
      <div className="qr-scanner-content">
        <div className="qr-scanner-header">
          <h2>📱 QR Code Scanner</h2>
          <button className="close-btn" onClick={onClose}>✕</button>
        </div>

        {error ? (
          <div className="qr-error">
            <p>{error}</p>
            <button onClick={() => setError(null)} className="retry-btn">
              Retry
            </button>
          </div>
        ) : (
          <>
            <div className="qr-scanner-viewport">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                className="qr-video"
              />
              <canvas ref={canvasRef} className="hidden" width={640} height={480} />
              <div className="qr-overlay">
                <div className="qr-frame" />
              </div>
            </div>

            <div className="qr-controls">
              {isStreaming ? (
                <>
                  <button onClick={captureFrame} className="capture-btn">
                    📸 Capture & Scan
                  </button>
                  <button onClick={showManualInput} className="manual-btn">
                    ✎ Enter Manually
                  </button>
                </>
              ) : (
                <button onClick={startCamera} className="capture-btn">
                  🔄 Restart Camera
                </button>
              )}
            </div>

            {scannedCode && (
              <div className="qr-result">
                <p className="result-label">Scanned Code:</p>
                <p className="result-code">{scannedCode}</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default QRScanner;
