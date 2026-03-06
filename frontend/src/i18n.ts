import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

import en from "./locales/en/translation.json";
import ptBR from "./locales/pt-BR/translation.json";

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      en: { translation: en },
      "pt-BR": { translation: ptBR },
    },
    fallbackLng: "pt-BR",
    supportedLngs: ["en", "pt-BR"],
    nonExplicitSupportedLngs: true,
    detection: {
      order: ["localStorage", "navigator"],
      caches: ["localStorage"],
      lookupLocalStorage: "i18n_lang",
      convertDetectedLanguage: (lng: string) =>
        lng.toLowerCase().startsWith("pt") ? "pt-BR" : "en",
    },
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;
