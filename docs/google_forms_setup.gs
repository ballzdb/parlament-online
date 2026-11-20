/**
 * Extends the existing student survey and creates a separate post-event
 * reporting form for parliament members. Safe to run more than once:
 * added survey questions and the event form are tracked in Script Properties.
 *
 * Run extendParlamentSurveyAndCreateEventForm() from Apps Script.
 */

const SURVEY_FORM_ID = '1XbKhgvexX8MpW7UasE9ciEfW5PjxNzutOqP7oBxoty4';
const RESEARCH_SHEET_ID = '1jDcli4v04sMta1o5SFaFg8PnmLDg8DxplvYNg8WIk-8';
const EVENT_FORM_PROPERTY = 'PARLAMENT_EVENT_FORM_ID';
const SURVEY_EXTENSION_PROPERTY = 'PARLAMENT_SURVEY_EXTENSION_V1';

function extendParlamentSurveyAndCreateEventForm() {
  const props = PropertiesService.getScriptProperties();
  const survey = FormApp.openById(SURVEY_FORM_ID);
  const spreadsheet = SpreadsheetApp.openById(RESEARCH_SHEET_ID);

  if (props.getProperty(SURVEY_EXTENSION_PROPERTY) !== 'done') {
    addStudentSurveyQuestions_(survey);
    props.setProperty(SURVEY_EXTENSION_PROPERTY, 'done');
  }

  const eventForm = getOrCreateEventForm_(props, spreadsheet);
  prepareResearchSpreadsheet_(spreadsheet);

  Logger.log('ОПИТУВАННЯ УЧНІВ: ' + survey.getPublishedUrl());
  Logger.log('РЕДАГУВАННЯ ОПИТУВАННЯ: ' + survey.getEditUrl());
  Logger.log('ФОРМА ЗВІТУ ПРО ЗАХІД: ' + eventForm.getPublishedUrl());
  Logger.log('РЕДАГУВАННЯ ФОРМИ ЗВІТУ: ' + eventForm.getEditUrl());
  Logger.log('ТАБЛИЦЯ ДОСЛІДЖЕННЯ: ' + spreadsheet.getUrl());
}

function addStudentSurveyQuestions_(form) {
  form.addPageBreakItem()
    .setTitle('Досвід участі в житті ліцею')
    .setHelpText('Наступні запитання стосуються вашого реального досвіду, а не бажаних відповідей.');

  form.addMultipleChoiceItem()
    .setTitle('Як часто ви берете участь у шкільних заходах або діяльності учнівського самоврядування?')
    .setChoiceValues(['Щотижня або майже щотижня', 'Кілька разів на місяць', 'Приблизно раз на місяць', 'Кілька разів на навчальний рік', 'Не беру участі'])
    .setRequired(true);

  form.addCheckboxItem()
    .setTitle('У яких формах шкільного життя ви брали участь протягом останніх трьох місяців?')
    .setChoiceValues(['Відвідував/ла шкільні заходи', 'Допомагав/ла в організації заходів', 'Пропонував/ла ідеї або ініціативи', 'Брав/ла участь у голосуваннях', 'Допомагав/ла класу або учнівському самоврядуванню', 'Не брав/ла участі', 'Інше']);

  form.addMultipleChoiceItem()
    .setTitle('Чи зверталися ви коли-небудь до учнівського парламенту з пропозицією, проблемою або запитанням?')
    .setChoiceValues(['Так', 'Ні', 'Не пам’ятаю / важко відповісти'])
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Якщо ви зверталися до парламенту, яким був результат?')
    .setChoiceValues(['Отримав/ла відповідь і зрозумів/ла подальші кроки', 'Пропозицію розглянули або реалізували', 'Отримав/ла відповідь, але питання не вирішили', 'Не отримав/ла відповіді', 'Не звертався/лася', 'Важко відповісти']);

  form.addCheckboxItem()
    .setTitle('Що могло б підвищити вашу готовність брати участь у роботі парламенту?')
    .setChoiceValues(['Зрозумілий спосіб подати пропозицію', 'Можливість стежити за статусом пропозиції', 'Публічні звіти про результати', 'Можливість голосувати онлайн', 'Анонімне подання окремих пропозицій', 'Регулярна інформація про заходи та рішення', 'Особисте запрошення долучитися', 'Нічого з переліченого', 'Інше']);

  form.addScaleItem()
    .setTitle('Наскільки важливо для вас бачити, що сталося з поданою пропозицією?')
    .setBounds(1, 5)
    .setLabels('Зовсім не важливо', 'Надзвичайно важливо')
    .setRequired(true);

  form.addMultipleChoiceItem()
    .setTitle('Який спосіб подання пропозицій ви вважаєте прийнятним?')
    .setChoiceValues(['Лише з ім’ям', 'Лише анонімно', 'Обидва способи', 'Не планую подавати пропозиції'])
    .setRequired(true);

  form.addParagraphTextItem()
    .setTitle('Опишіть одну конкретну зміну, яка, на вашу думку, покращила б взаємодію учнів із парламентом.')
    .setRequired(false);
}

function getOrCreateEventForm_(props, spreadsheet) {
  const existingId = props.getProperty(EVENT_FORM_PROPERTY);
  if (existingId) {
    try {
      return FormApp.openById(existingId);
    } catch (error) {
      props.deleteProperty(EVENT_FORM_PROPERTY);
    }
  }

  const form = FormApp.create('Парламент.Online — звіт про проведений захід');
  form.setDescription(
    'Форму заповнює організатор або відповідальний представник парламенту після проведення заходу. ' +
    'Вказуйте фактичні дані. Якщо точна кількість учасників невідома, зазначте приблизну кількість і позначте це в описі.'
  );
  form.setConfirmationMessage('Дякуємо. Інформацію про захід збережено для звітності парламенту.');
  form.setCollectEmail(false);

  form.addTextItem().setTitle('Назва заходу').setRequired(true);
  form.addDateItem().setTitle('Дата проведення').setRequired(true);
  form.addMultipleChoiceItem()
    .setTitle('Хто був основним організатором?')
    .setChoiceValues(['Учнівський парламент', 'Комісія парламенту', 'Клас / класний колектив', 'Педагог / адміністрація', 'Спільна організація', 'Інше'])
    .setRequired(true);
  form.addTextItem().setTitle('Назва комісії, класу або ім’я/посада організатора').setRequired(true);
  form.addCheckboxItem()
    .setTitle('Які класи брали участь?')
    .setChoiceValues(['5', '6', '7', '8', '9', '10', '11', 'Інші / змішані групи'])
    .setRequired(true);
  const count = form.addTextItem().setTitle('Фактична кількість учасників (лише число)').setRequired(true);
  const numberValidation = FormApp.createTextValidation()
    .requireNumberBetween(0, 10000)
    .setHelpText('Введіть ціле число від 0 до 10000.')
    .build();
  count.setValidation(numberValidation);
  form.addParagraphTextItem().setTitle('Мета заходу та короткий опис').setRequired(true);
  form.addParagraphTextItem().setTitle('Що фактично відбулося? Який результат або підсумок?').setRequired(true);
  form.addTextItem().setTitle('Посилання на фото, публікацію, документ або інше підтвердження (за наявності)').setRequired(false);
  form.addTextItem().setTitle('Хто заповнив форму (ім’я та роль)').setRequired(true);

  form.setDestination(FormApp.DestinationType.SPREADSHEET, spreadsheet.getId());
  props.setProperty(EVENT_FORM_PROPERTY, form.getId());
  return form;
}

function prepareResearchSpreadsheet_(spreadsheet) {
  let sheet = spreadsheet.getSheetByName('Облік заходів');
  if (!sheet) sheet = spreadsheet.insertSheet('Облік заходів');

  const headers = [
    'Назва заходу', 'Дата', 'Організатор', 'Комісія / клас / відповідальна особа',
    'Класи, які брали участь', 'Кількість учасників',
    'Мета та опис', 'Результат / підсумок', 'Посилання на підтвердження', 'Джерело даних'
  ];
  if (sheet.getLastRow() === 0) {
    sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  }
  sheet.setFrozenRows(1);
  sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold').setWrap(true);
  sheet.autoResizeColumns(1, headers.length);

  let guide = spreadsheet.getSheetByName('Інструкція');
  if (!guide) guide = spreadsheet.insertSheet('Інструкція');
  if (guide.getLastRow() === 0) {
    guide.getRange(1, 1, 1, 2).setValues([['Поле', 'Правило заповнення']]);
    guide.getRange(2, 1, 7, 2).setValues([
      ['Кількість учасників', 'Вказуйте фактичне число; якщо воно приблизне — зазначте це в описі.'],
      ['Класи', 'Перелічуйте лише класи, участь яких підтверджена організатором.'],
      ['Організатор', 'Вкажіть фактичного організатора, а не лише того, хто заповнює форму.'],
      ['Результат', 'Опишіть конкретний підсумок; не використовуйте загальні оцінки без доказів.'],
      ['Підтвердження', 'За можливості додайте посилання на фото, допис, оголошення або документ.'],
      ['Порожні дані', 'Не вигадуйте відсутні значення. Залишайте поле порожнім або пишіть «невідомо».'],
      ['Приватність', 'Не вносьте персональні дані учнів, які не потрібні для дослідження.']
    ]);
    guide.setFrozenRows(1);
    guide.getRange(1, 1, 1, 2).setFontWeight('bold');
    guide.autoResizeColumns(1, 2);
  }
}
