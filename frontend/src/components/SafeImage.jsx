import { useState } from "react";
import { PLACEHOLDER } from "../utils/hotel";

// Image avec solution de remplacement si le chargement échoue.
export default function SafeImage({ src, alt = "", className = "" }) {
  const [failed, setFailed] = useState(false);
  return (
    <img
      className={className}
      src={failed || !src ? PLACEHOLDER : src}
      alt={alt}
      loading="lazy"
      onError={() => setFailed(true)}
    />
  );
}
