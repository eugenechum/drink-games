import { useEffect, useState } from "react";
import QRCode from "qrcode";

export default function QrCode({ value, size = 200 }) {
  const [dataUrl, setDataUrl] = useState(null);

  useEffect(() => {
    let cancelled = false;
    QRCode.toDataURL(value, { width: size, margin: 1, color: { dark: "#082c21", light: "#f3ede1" } }).then(
      (url) => {
        if (!cancelled) setDataUrl(url);
      }
    );
    return () => {
      cancelled = true;
    };
  }, [value, size]);

  if (!dataUrl) {
    return <div style={{ width: size, height: size }} className="animate-pulse bg-white/10 rounded-lg" />;
  }
  return <img src={dataUrl} alt="Room QR code" width={size} height={size} className="rounded-lg" />;
}
