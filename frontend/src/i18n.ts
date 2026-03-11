import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./locales/en/translation.json";
import ptBR from "./locales/pt-BR/translation.json";

function detectLanguage(): string {
  const stored = localStorage.getItem("i18n_lang");
  if (stored) {
    return stored.toLowerCase().startsWith("pt") ? "pt-BR" : "en";
  }
  const nav = navigator.language || "";
  return nav.toLowerCase().startsWith("pt") ? "pt-BR" : "en";
}

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    "pt-BR": { translation: ptBR },
  },
  lng: detectLanguage(),
  fallbackLng: "pt-BR",
  interpolation: {
    escapeValue: false,
  },
});

export default i18n;
