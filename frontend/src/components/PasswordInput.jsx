import { useState } from "react";
import { EyeIcon, EyeOffIcon } from "./Icons";

// Champ mot de passe avec bouton "oeil" pour afficher / masquer la saisie.
// Accepte les mêmes props qu'un <input> classique (value, onChange, autoComplete, ...).
export default function PasswordInput(props) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="password-wrap">
      <input {...props} type={visible ? "text" : "password"} />
      <button
        type="button"
        className="password-toggle"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? "Masquer le mot de passe" : "Afficher le mot de passe"}
        aria-pressed={visible}
        title={visible ? "Masquer le mot de passe" : "Afficher le mot de passe"}
      >
        {visible ? <EyeOffIcon /> : <EyeIcon />}
      </button>
    </div>
  );
}
