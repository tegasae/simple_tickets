export default function ThemeSwitcher({ theme, themes, onThemeChange, compact = false }) {
  return (
    <div className={compact ? "theme-switcher theme-switcher-compact" : "theme-switcher"}>
      {themes.map((item) => (
        <button
          key={item.id}
          type="button"
          className={item.id === theme ? "theme-option active" : "theme-option"}
          onClick={() => onThemeChange(item.id)}
        >
          {item.label}
        </button>
      ))}
    </div>
  );
}
