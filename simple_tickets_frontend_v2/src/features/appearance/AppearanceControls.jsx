import { t } from '../../shared/i18n/messages.js';
import './appearance.css';

function AppearanceSelect({ label, value, options, onChange }) {
  return (
    <label className="appearance-control">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map(({ id, label: optionLabel }) => <option key={id} value={id}>{optionLabel}</option>)}
      </select>
    </label>
  );
}

export default function AppearanceControls({
  theme,
  language,
  selectedLanguage,
  themes = [],
  languages = [],
  onThemeChange,
  onLanguageChange,
  languagePending = false,
  languageError = false,
}) {
  const showThemes = themes.length > 1;
  const showLanguages = languages.length > 1;
  if (!showThemes && !showLanguages && !languageError) return null;

  return (
    <div className="appearance-controls">
      {showThemes && (
        <AppearanceSelect label={t('appearance.theme')} value={theme} options={themes} onChange={onThemeChange} />
      )}
      {showLanguages && (
        <AppearanceSelect
          label={t('appearance.language')}
          value={selectedLanguage || language}
          options={languages}
          onChange={onLanguageChange}
        />
      )}
      {(showLanguages || languageError) && (
        <p className="appearance-status" role="status">
          {languagePending && t('appearance.languagePending')}
          {!languagePending && languageError && t('appearance.languageError')}
        </p>
      )}
    </div>
  );
}
