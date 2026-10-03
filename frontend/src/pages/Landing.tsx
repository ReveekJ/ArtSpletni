import { useEffect, useRef } from "react";
import "../styles/landing.css";

const stops = [
  { name: "Дом-музей Мамина-Сибиряка", story: "Мария Абрамова", area: "Центр" },
  { name: "Дом Севастьянова", story: "Золотой купол и чугунные калоши", area: "Центр" },
  { name: "«Эта музыка будет вечной»", story: "Как сохранили «Стену Цоя»", area: "Плотинка" },
  { name: "Памятник клавиатуре", story: "Желание и большая перезагрузка", area: "Исеть" },
  { name: "Музей андеграунда", story: "«Рождение звезды»: Цой?", area: "Уралмаш" },
  { name: "Дом Агафуровых", story: "История Биби-Азизы", area: "Центр" },
  { name: "Белая башня", story: "Любовная магия или проект за одну ночь", area: "Уралмаш" },
];

export default function Landing() {
  const landingRef = useRef<HTMLElement>(null);

  const handleShare = async () => {
    const shareData = {
      title: "Арт-сплетни",
      text: "Истории Екатеринбурга, которые пересказывают",
      url: window.location.href,
    };

    if (navigator.share) {
      try {
        await navigator.share(shareData);
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") return;
        throw error;
      }
      return;
    }

    await navigator.clipboard.writeText(shareData.url);
    window.alert("Ссылка скопирована");
  };

  useEffect(() => {
    const landing = landingRef.current;
    if (!landing) return;

    landing.classList.add("reveal-ready");
    const revealItems = landing.querySelectorAll<HTMLElement>("[data-reveal]");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.14, rootMargin: "0px 0px -7%" },
    );

    revealItems.forEach((item) => observer.observe(item));
    return () => observer.disconnect();
  }, []);

  return (
    <main className="landing" ref={landingRef}>
      <header className="landing-header">
        <a className="landing-logo" href="#top" aria-label="Арт-сплетни, наверх">
          <span className="logo-mark">А</span>
          <span>Арт-сплетни</span>
        </a>
        <nav aria-label="Основная навигация">
          <a href="#idea">Идея</a>
          <a href="#route">Маршрут</a>
          <a href="/predlozhenie">Предложить</a>
        </nav>
        <a className="header-link" href="#route">7 историй <span aria-hidden="true">↘</span></a>
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <p className="eyebrow"><span className="live-dot" /> Екатеринбург, который пересказывают</p>
          <h1>У города<br />есть <em>секреты.</em></h1>
          <p className="hero-intro">Мы собрали их в короткие аудиоистории. Подойди к месту, коснись NFC-метки и послушай, о чём обычно говорят шёпотом.</p>
          <p className="hero-description">Арт-сплетни — городские истории Екатеринбурга</p>
          <a className="primary-link" href="#idea">Узнать, как это работает <span aria-hidden="true">↓</span></a>
          <p className="hero-note">История города. Никакой кафедры.</p>
        </div>
        <div className="hero-art" aria-label="Схематичная карта маршрута по Екатеринбургу">
          <div className="art-topline"><span>СЛУХИ ХОДЯТ ПО ГОРОДУ</span><span>56°50′ N / 60°36′ E</span></div>
          <div className="map-lines" aria-hidden="true">
            <svg viewBox="0 0 620 520" role="presentation">
              <path className="street" d="M-20 90 140 130 270 70 420 125 650 80M-20 220 120 190 260 250 390 190 650 260M-20 390 150 340 290 400 450 335 650 410M90 -20 130 120 90 260 160 540M300 -20 270 100 330 240 280 390 340 540M500 -20 440 120 490 270 430 390 510 540" />
              <path className="route-line" d="M140 130 270 70 390 190 260 250 290 400 450 335 500 460" />
            </svg>
            {["Дом Севастьянова", "Стена Цоя", "Памятник клавиатуре", "Белая башня"].map((label, index) => (
              <span className={`map-pin pin-${index + 1}`} key={label}><i>{String(index + 1).padStart(2, "0")}</i><b>{label}</b></span>
            ))}
            <span className="map-water">ИСЕТЬ</span>
            <span className="map-stamp">СЛУХ<br />№ 001</span>
          </div>
          <div className="art-bottomline"><span>НЕОФИЦИАЛЬНЫЙ ПУТЕВОДИТЕЛЬ</span><span>СЛУШАЙ ВНИМАТЕЛЬНО</span></div>
        </div>
        <div className="hero-index">01 <span>/</span> 07</div>
      </section>

      <section className="idea-section" id="idea">
        <div className="section-label" data-reveal><span>01 — ЗАМЫСЕЛ</span><span>СНАЧАЛА ЭТО БЫЛ СЛУХ</span></div>
        <div className="idea-grid" data-reveal>
          <h2>Историю проще<br />услышать, чем <em>выучить.</em></h2>
          <div className="idea-text">
            <p>Мы привыкли узнавать новости от знакомых: коротко, эмоционально и с неожиданной деталью. Почему бы не рассказывать так же о городе?</p>
            <p>«Арт-сплетни» — это городские легенды, малоизвестные факты и локальные истории, рассказанные живым языком. Не лекция, а повод посмотреть на знакомое место иначе.</p>
            <button className="margin-note" type="button" onClick={handleShare}>
              ПЕРЕДАЙ ДАЛЬШЕ <b aria-hidden="true">↗</b>
            </button>
          </div>
        </div>
        <div className="principles" data-reveal>
          <article><span>01</span><h3>Услышать</h3><p>Короткая история начинается прямо там, где всё произошло.</p></article>
          <article><span>02</span><h3>Удивиться</h3><p>Факт, легенда или версия, которую не найдёшь на табличке.</p></article>
          <article><span>03</span><h3>Пересказать</h3><p>Хорошая сплетня не заканчивается на одном слушателе.</p></article>
        </div>
      </section>

      <section className="how-section" aria-labelledby="how-title">
        <div className="section-label" data-reveal><span>02 — КАК ЭТО УСТРОЕНО</span><span>МЕНЬШЕ ЭКРАНА, БОЛЬШЕ ГОРОДА</span></div>
        <div className="how-heading" data-reveal><h2 id="how-title">Нашёл место.<br /><em>Нашёл историю.</em></h2><p>Никаких приложений и длинных инструкций. Только город, телефон и любопытство.</p></div>
        <div className="steps" data-reveal>
          <article><span className="step-number">01</span><span className="step-icon nfc-icon" aria-hidden="true">✦</span><h3>Коснись</h3><p>Найди NFC-стикер рядом с объектом и поднеси смартфон.</p></article>
          <span className="step-arrow" aria-hidden="true">→</span>
          <article><span className="step-number">02</span><span className="step-icon audio-icon" aria-hidden="true">▶</span><h3>Послушай</h3><p>Откроется страница с короткой аудиоисторией об этом месте.</p></article>
          <span className="step-arrow" aria-hidden="true">→</span>
          <article><span className="step-number">03</span><span className="step-icon share-icon" aria-hidden="true">↗</span><h3>Передай дальше</h3><p>Продолжи прогулку или поделись историей с друзьями.</p></article>
        </div>
      </section>

      <section className="route-section" id="route">
        <div className="section-label" data-reveal><span>03 — ГОРОДСКОЙ МАРШРУТ</span><span>7 ТОЧЕК / МЕНЬШЕ 3 ЧАСОВ</span></div>
        <div className="route-heading" data-reveal><h2>Семь остановок.<br /><em>Семь поводов свернуть.</em></h2><p>От купола в центре до Белой башни. Иди в своём темпе — истории никуда не денутся.</p></div>
        <div className="stops-list" data-reveal>
          {stops.map((stop, index) => (
            <article className="stop-row" key={stop.name}>
              <span className="stop-index">{String(index + 1).padStart(2, "0")}</span>
              <div className="stop-name"><h3>{stop.name}</h3><span>{stop.area}</span></div>
              <p className="stop-story">{stop.story}</p>
              <span className="stop-mark" aria-hidden="true">↗</span>
            </article>
          ))}
        </div>
        <div className="route-foot"><span>МАРШРУТ В РАБОТЕ</span><span>СЛЕДУЮЩАЯ ОСТАНОВКА — ТА, КОТОРУЮ ТЫ НЕ ЗАМЕЧАЛ</span></div>
      </section>

      <footer className="landing-footer">
        <p className="footer-kicker">СЛУХИ ХОДЯТ ПО ГОРОДУ</p>
        <h2>Теперь ты <em>знаешь.</em></h2>
        <a href="/predlozhenie" className="footer-link">Предложить свою историю <span aria-hidden="true">↗</span></a>
        <div className="footer-partners">
          <div className="footer-partner">
            <span className="footer-partner-role">Создано</span>
            <a className="footer-media" href="https://vk.ru/lyceum.urfu" target="_blank" rel="noreferrer" aria-label="Открыть страницу SESC MEDIA">
              SESC <span>MEDIA</span>
            </a>
          </div>
          <div className="footer-partner">
            <span className="footer-partner-role">При поддержке</span>
            <a className="footer-wordmark" href="https://sesc-it-team.ru/" target="_blank" rel="noreferrer" aria-label="Открыть сайт SESC IT Team">
              <img src="/image.png" alt="SESC IT Team" width="1042" height="161" />
            </a>
          </div>
        </div>
        <div className="footer-bottom">
          <span>АРТ-СПЛЕТНИ · ЕКАТЕРИНБУРГ</span>
          <span>КУЛЬТУРА ТОЖЕ МОЖЕТ БЫТЬ ЛИЧНОЙ</span>
        </div>
      </footer>
    </main>
  );
}
