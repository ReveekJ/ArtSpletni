from app.db.models import MapVisibility, OrderingMode
from app.domain.demo.catalog import OfferSeed, PointSeed, RouteSeed

MSK_ROUTES: tuple[RouteSeed, ...] = (
    RouteSeed(
        slug="msk-patriarshie",
        title={"ru": "Патриаршие слухи", "en": "Patriarch Ponds Rumours"},
        description="Маршрут-граф: начни с прудов, дальше открываются сад, бар и дом-коммуна.",
        ordering_mode=OrderingMode.GRAPH,
        map_visibility=MapVisibility.VISITED_WITH_HINTS,
        points=(
            PointSeed(
                key="msk-patriki",
                title={"ru": "Патриаршие пруды", "en": "Patriarch Ponds"},
                latitude=55.7637,
                longitude=37.5929,
                address="Малый Патриарший пер.",
                story=(
                    "Здесь, конечно, никогда не разговаривают с незнакомцами. "
                    "Местные уверяют, что трамвая на Патриарших не было никогда, и это подозрительнее всего. "
                    "А разлитое подсолнечное масло, говорят, до сих пор иногда находят у турникетов."
                ),
            ),
            PointSeed(
                key="msk-bar",
                title={"ru": "Бар «Шёпот»", "en": "Whisper Bar"},
                latitude=55.7651,
                longitude=37.5957,
                address="Ермолаевский пер., 9",
                partner="bar",
                is_required=False,
                hint="Вывеска едва заметна — прислушайся.",
                depends_on=("msk-patriki",),
                offer=OfferSeed(
                    title={"ru": "Фирменный лимонад за сплетню", "en": "Signature lemonade for a story"},
                    terms={"ru": "Покажите код бармену. Один лимонад на гостя."},
                    redemption_limit=200,
                    valid_days=60,
                ),
                story=(
                    "В «Шёпоте» не принято говорить громко: бармен уверяет, "
                    "что громкие истории здесь портят вкус лимонада. "
                    "Расскажи свою сплетню вполголоса — и лимонад за счёт заведения."
                ),
            ),
            PointSeed(
                key="msk-ermitazh",
                title={"ru": "Сад «Эрмитаж»", "en": "Hermitage Garden"},
                latitude=55.7710,
                longitude=37.6107,
                address="ул. Каретный Ряд, 3",
                hint="Ищи старую сцену среди деревьев.",
                depends_on=("msk-patriki",),
                story=(
                    "В саду «Эрмитаж» одними из первых в Москве показали кино, "
                    "и, говорят, зрители выбегали из зала, когда на экран ехал поезд. "
                    "С тех пор каждый сезон здесь ищут новую сенсацию, а белки узнают о премьерах раньше критиков."
                ),
            ),
            PointSeed(
                key="msk-narkomfin",
                title={"ru": "Дом Наркомфина", "en": "Narkomfin Building"},
                latitude=55.7569,
                longitude=37.5820,
                address="Новинский бульвар, 25к1",
                hint="Длинный дом на ножках за американским посольством.",
                depends_on=("msk-ermitazh",),
                story=(
                    "В доме-коммуне задумали общие кухни, чтобы жильцы не тратили время на быт. "
                    "По слухам, жильцы всё равно тайком варили борщ на примусах в своих ячейках, "
                    "и коммунальный эксперимент проиграл обычной кастрюле."
                ),
            ),
        ),
    ),
    RouteSeed(
        slug="msk-boulevards",
        title={"ru": "Бульвары шёпотом", "en": "Boulevards in a Whisper"},
        description="От Арбата до Хитровки по порядку: стены, пруды и старые московские легенды.",
        ordering_mode=OrderingMode.SEQUENTIAL,
        map_visibility=MapVisibility.ALL,
        is_repeatable=True,
        points=(
            PointSeed(
                key="msk-tsoi",
                title={"ru": "Стена Цоя", "en": "Tsoi Wall"},
                latitude=55.7495,
                longitude=37.5916,
                address="ул. Арбат, 37",
                story=(
                    "Стену на Арбате закрашивали не раз, но надписи возвращались к утру. "
                    "Говорят, у неё своё расписание: самые свежие строчки появляются в июне и в августе. "
                    "Попробуй отыскать самую старую — местные спорят о ней до сих пор."
                ),
            ),
            PointSeed(
                key="msk-chistye",
                title={"ru": "Чистые пруды", "en": "Chistye Prudy"},
                latitude=55.7612,
                longitude=37.6430,
                address="Чистопрудный бульвар",
                story=(
                    "Когда-то пруд звали Поганым: сюда сливали отходы мясники. "
                    "Князь Меншиков велел его вычистить и переименовать. "
                    "Говорят, это был первый в Москве удачный ребрендинг."
                ),
            ),
            PointSeed(
                key="msk-bakery",
                title={"ru": "Пекарня «Булка на Покровке»", "en": "Bulka Bakery"},
                latitude=55.7591,
                longitude=37.6455,
                address="ул. Покровка, 17",
                partner="bakery",
                is_required=False,
                offer=OfferSeed(
                    title={"ru": "Круассан за пройденную точку", "en": "Croissant for a visited stop"},
                    terms={"ru": "Покажите код на кассе. Действует 48 часов после получения."},
                    ttl_hours=48,
                    redemption_limit=100,
                ),
                story=(
                    "Пекари встают в пять утра и уверяют, что к семи уже знают все новости Покровки: "
                    "кто переехал, кто влюбился и кто опять забыл ключи. "
                    "Заходи за круассаном — и за свежими слухами."
                ),
            ),
            PointSeed(
                key="msk-khitrovka",
                title={"ru": "Хитровка", "en": "Khitrovka"},
                latitude=55.7530,
                longitude=37.6440,
                address="Хитровская площадь",
                story=(
                    "Хитров рынок был самым тёмным местом старой Москвы: "
                    "Гиляровский ходил сюда без провожатых и возвращался с историями. "
                    "Говорят, если долго стоять на площади, кто-нибудь обязательно предложит "
                    "купить самые настоящие часы Гиляровского."
                ),
            ),
        ),
    ),
)
