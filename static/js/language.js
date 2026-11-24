(() => {
  const translations = {
    "Головна":"Home","Ідеї":"Ideas","Події та архів":"Events & archive","Опитування":"Surveys","Правила":"Rules","Відгуки":"Feedback","Підтримка":"Support","Дошка завдань":"Task board","Модерація":"Moderation","Обмеження":"Restrictions","Аналітика":"Analytics","Керування ролями":"Role management","Увійти":"Sign in","Реєстрація":"Register","Вийти":"Sign out","Перейти до основного вмісту":"Skip to main content","Контактна пошта:":"Contact email:","Модерація ідей":"Idea moderation","ПЕРЕВІРКА ПРОПОЗИЦІЙ":"PROPOSAL REVIEW","Перевіряйте нові пропозиції, публікуйте схвалені та прибирайте ті, що порушують правила.":"Review new proposals, publish approved ones, and remove those that break the rules.","Правила":"Rules","Блокування користувачів":"User restrictions","очікують":"awaiting review","Очікують перевірки":"Awaiting review","Опубліковані ідеї":"Published ideas","Останні 30":"Latest 30","Відповідальний:":"Assigned moderator:","Не призначено":"Not assigned","Призначити модератора":"Assign a moderator","Оберіть відповідального":"Choose a moderator","Призначити":"Assign","Коментар / причина (обов’язково для відхилення)":"Comment / reason (required when rejecting)","Пояснення рішення для автора":"Explain the decision to the author","Дозволити публікацію":"Approve publication","Відхилити":"Reject","Видалити ідею":"Delete idea","Нових ідей на перевірку немає.":"There are no new ideas awaiting review.","Опубліковано:":"Published:","Дата не зазначена":"Date not provided","Голосів:":"Votes:","Опублікованих ідей поки немає.":"There are no published ideas yet.","Назва ідеї":"Idea title","Опис":"Description","Комісія":"Committee","Статус":"Status","Причина":"Reason","Дата та час проведення":"Event date and time","Назва події":"Event title","Опис події":"Event description","Організатор":"Organiser","Кількість учасників (якщо відома)":"Number of participants (if known)","Результат / короткий опис (можна заповнити після події)":"Outcome / short report (may be completed after the event)","Подано":"Submitted","На розгляді":"Under review","В роботі":"In progress","Виконано":"Completed","Відхилено":"Rejected","Опубліковано":"Published","Очікує модерації":"Awaiting moderation","Відхилено модератором":"Rejected by moderator"
  };
  const original = new WeakMap();
  function translateNode(node, enabled) {
    if (node.nodeType === Node.TEXT_NODE) {
      const current = node.nodeValue.trim();
      if (!current) return;
      if (!original.has(node)) original.set(node, node.nodeValue);
      const source = original.get(node).trim();
      if (enabled && translations[source]) node.nodeValue = node.nodeValue.replace(source, translations[source]);
      else if (!enabled) node.nodeValue = original.get(node);
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      for (const attr of ["placeholder", "title", "aria-label", "value"]) {
        if (node.hasAttribute(attr)) {
          const key = "data-original-" + attr;
          if (!node.hasAttribute(key)) node.setAttribute(key, node.getAttribute(attr));
          const source = node.getAttribute(key);
          if (enabled && translations[source]) node.setAttribute(attr, translations[source]);
          else if (!enabled) node.setAttribute(attr, source);
        }
      }
      node.childNodes.forEach(child => translateNode(child, enabled));
    }
  }
  function setLanguage(language) {
    const english = language === "en";
    document.documentElement.lang = english ? "en" : "uk";
    document.cookie = "site_language=" + (english ? "en" : "uk") + "; path=/; max-age=31536000; SameSite=Lax";
    document.querySelectorAll("[data-set-language]").forEach(button => {
      button.setAttribute("aria-pressed", String(button.dataset.setLanguage === language));
    });
    translateNode(document.body, english);
    try { localStorage.setItem("site_language", language); } catch (_) {}
  }
  document.addEventListener("click", event => {
    const button = event.target.closest("[data-set-language]");
    if (button) setLanguage(button.dataset.setLanguage);
  });
  const saved = (() => { try { return localStorage.getItem("site_language"); } catch (_) { return null; } })();
  const cookie = document.cookie.split("; ").find(value => value.startsWith("site_language="));
  setLanguage(saved || (cookie ? cookie.split("=")[1] : "uk"));
  new MutationObserver(records => {
    const english = document.documentElement.lang === "en";
    if (!english) return;
    records.forEach(record => record.addedNodes.forEach(node => translateNode(node, true)));
  }).observe(document.body, {childList:true,subtree:true});
})();