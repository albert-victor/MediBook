/**

 * FAQ page - accordion interactions

 */



import { i18nReady } from "../i18n/languageManager.js";



function initFaq() {

  document.querySelectorAll("[data-faq-trigger]").forEach((trigger) => {

    trigger.addEventListener("click", () => {

      const item = trigger.closest("[data-faq-item]");

      const answer = item.querySelector(".med-faq__answer");

      const isOpen = item.classList.contains("is-open");



      document.querySelectorAll("[data-faq-item].is-open").forEach((openItem) => {

        if (openItem !== item) {

          openItem.classList.remove("is-open");

          openItem.querySelector("[data-faq-trigger]").setAttribute("aria-expanded", "false");

          openItem.querySelector(".med-faq__answer").hidden = true;

        }

      });



      item.classList.toggle("is-open", !isOpen);

      trigger.setAttribute("aria-expanded", String(!isOpen));

      answer.hidden = isOpen;

    });

  });

}



document.addEventListener("DOMContentLoaded", async () => {

  await i18nReady;

  initFaq();

});

