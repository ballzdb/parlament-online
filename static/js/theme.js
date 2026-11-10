(function () {
  const storageKey = 'parlament-online-theme';
  const consentStorageKey = 'parlament-online-anonymous-analytics';
  const root = document.documentElement;
  root.classList.add('js-enabled');
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
  let analyticsConsent = null;

  try {
    const savedConsent = localStorage.getItem(consentStorageKey);
    analyticsConsent = savedConsent === 'yes' || savedConsent === 'no' ? savedConsent : null;
  } catch {
    analyticsConsent = null;
  }

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

  function getPageSection() {
    const path = window.location.pathname;
    if (path === '/') return 'home';
    if (path === '/decisions/') return 'decisions';

    const sections = {
      '/ideas/': 'ideas',
      '/appeals/': 'appeals',
      '/support/': 'support',
      '/kanban/': 'kanban',
      '/analytics/': 'analytics',
    };

    for (const prefix of Object.keys(sections)) {
      if (path.startsWith(prefix)) return sections[prefix];
    }

    return 'other';
  }

  function sendAnonymousPageView() {
    const banner = document.querySelector('.privacy-consent');
    const csrfToken = document.querySelector('.csrf-token-form [name="csrfmiddlewaretoken"]').value;

    fetch(banner.dataset.endpoint, {
      method: 'POST',
      credentials: 'same-origin',
      referrerPolicy: 'no-referrer',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
        'X-Anonymous-Analytics-Consent': 'yes',
      },
      body: JSON.stringify({ section: getPageSection() }),
    }).then(function (response) {
      if (!response.ok) console.warn('Не вдалося надіслати анонімну статистику:', response.status);
    }).catch(function (error) {
      console.warn('Не вдалося надіслати анонімну статистику:', error);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    updateToggle(initialTheme);
    document.querySelector('.theme-toggle').addEventListener('click', function () {
      setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark', true);
    });

    const menuButton = document.querySelector('.nav-menu-toggle');
    const navigation = document.querySelector('.nav-links');

    function setMenuOpen(isOpen) {
      menuButton.setAttribute('aria-expanded', String(isOpen));
      navigation.classList.toggle('is-open', isOpen);
      menuButton.querySelector('.nav-menu-icon').textContent = isOpen ? '×' : '☰';
      menuButton.querySelector('.nav-menu-label').textContent = isOpen ? 'Закрити' : 'Меню';
    }

    menuButton.addEventListener('click', function () {
      setMenuOpen(menuButton.getAttribute('aria-expanded') !== 'true');
    });

    navigation.addEventListener('click', function (event) {
      if (event.target.closest('a')) setMenuOpen(false);
    });

    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && menuButton.getAttribute('aria-expanded') === 'true') {
        setMenuOpen(false);
        menuButton.focus();
      }
    });

    const consentBanner = document.querySelector('.privacy-consent');
    const privacySettings = document.querySelector('#privacy-settings');
    const closeConsentBanner = function () {
      consentBanner.hidden = true;
    };

    if (analyticsConsent === null) consentBanner.hidden = false;
    if (analyticsConsent === 'yes') sendAnonymousPageView();

    consentBanner.addEventListener('click', function (event) {
      const choice = event.target.closest('[data-consent-choice]');
      if (!choice) return;

      analyticsConsent = choice.dataset.consentChoice === 'accept' ? 'yes' : 'no';
      try {
        localStorage.setItem(consentStorageKey, analyticsConsent);
      } catch {
        console.warn('Налаштування згоди діятиме лише до закриття цієї вкладки.');
      }

      closeConsentBanner();
      if (analyticsConsent === 'yes') sendAnonymousPageView();
    });

    if (privacySettings) {
      privacySettings.addEventListener('click', function () {
        consentBanner.hidden = false;
        document.querySelector('[data-consent-choice="accept"]').focus();
      });
    }

    if (savedTheme !== 'light' && savedTheme !== 'dark' && window.matchMedia) {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function (event) {
        setTheme(event.matches ? 'dark' : 'light', false);
      });
    }
  });
})();
