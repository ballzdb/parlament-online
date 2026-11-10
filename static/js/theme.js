(function () {
  const storageKey = 'parlament-online-theme';
  const root = document.documentElement;
  let savedTheme = null;

  try {
    savedTheme = localStorage.getItem(storageKey);
  } catch {
    savedTheme = null;
  }

  const systemPrefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  const initialTheme = savedTheme === 'light' || savedTheme === 'dark'
    ? savedTheme
    : systemPrefersDark ? 'dark' : 'light';
  root.dataset.theme = initialTheme;

  function updateToggle(theme) {
    const button = document.querySelector('.theme-toggle');
    if (!button) return;

    const nextThemeLabel = theme === 'dark' ? 'денну' : 'нічну';
    button.setAttribute('aria-label', `Увімкнути ${nextThemeLabel} тему`);
    button.title = `Увімкнути ${nextThemeLabel} тему`;
    button.querySelector('.theme-toggle-icon').textContent = theme === 'dark' ? '☀' : '☾';
    button.querySelector('.theme-toggle-label').textContent = theme === 'dark' ? 'Денна тема' : 'Нічна тема';
  }

  function setTheme(theme, save) {
    root.dataset.theme = theme;
    updateToggle(theme);

    if (save) {
      try {
        localStorage.setItem(storageKey, theme);
      } catch {
        return;
      }
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    updateToggle(initialTheme);
    document.querySelector('.theme-toggle').addEventListener('click', function () {
      setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark', true);
    });

    if (savedTheme !== 'light' && savedTheme !== 'dark' && window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (event) {
        setTheme(event.matches ? 'dark' : 'light', false);
      });
    }
  });
})();
