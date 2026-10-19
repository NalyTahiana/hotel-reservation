import { useState } from "react";
import { EyeIcon, EyeOffIcon } from "./Icons";

export default function PasswordInput(props) {
  const [visible, setVisible] = useState(false);
  const label = visible ? "Masquer le mot de passe" : "Afficher le mot de passe";
  return (
    <div className="password-input">
      <input {...props} type={visible ? "text" : "password"} />
      <button type="button" className="password-toggle" onClick={() => setVisible((v) => !v)} aria-label={label} aria-pressed={visible} title={label}>
        {visible ? <EyeOffIcon /> : <EyeIcon />}
      </button>
    </div>
  );
}
