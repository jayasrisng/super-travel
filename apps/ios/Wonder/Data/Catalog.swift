import Foundation

/// Curated photography (Unsplash).
enum Pic {
    static let oia = "1570077188670-e3a8d69ac5ff"
    static let amalfiTown = "1612698093158-e07ac200d44e"
    static let santoriniTerrace = "1498503182468-3b51cbb6cb24"
    static let santoriniDomes = "1530841377377-3ff06c0ca713"
    static let matterhorn = "1491555103944-7c647fd857e6"
    static let overwaterArc = "1590001155093-a3c66ab0c3ff"
    static let floatingBreakfast = "1586861635167-e5223aadc9fe"
    static let torii = "1601823984263-b87b59798b70"
    static let medAlley = "1515859005217-8a1f08870f59"
    static let comoVarenna = "1589340819076-7d3490f70ca1"
    static let comoBalbianello = "1586974726316-c6302de6a160"
    static let comoDusk = "1582150050076-52baeeba4a74"
    static let comoBellagio = "1606745463199-d7623eee5f8a"
    static let comoArches = "1654011905292-c342dd9fc433"
    static let sakura = "1522383225653-ed111181a951"

    // New York
    static let empireGolden = "1448317971280-6c74e016e49c"
    static let nycDusk = "1541336032412-2048a678540d"
    static let nycAvenue = "1500916434205-0c77489c6cf7"
    static let nycHarbor = "1613968317130-e6565f71b9d3"
    static let nycAerial = "1543716091-a840c05249ec"
    static let nycNight = "1605702012553-e954fbde66eb"
    // San Francisco
    static let goldenGate = "1524523762086-bcecce3611f3"
    static let goldenGateDusk = "1719858403455-9a2582eca805"
    static let goldenGateFog = "1574300328682-e5f390039dc4"
    static let cableCar = "1534050359320-02900022671e"
    static let sfNight = "1558623869-0507000fa875"
    static let goldenGateTower = "1501971687420-ee6a2eca6e03"
    // Chicago
    static let chicagoSunset = "1631548637245-043803a8b776"
    static let chicagoRiverNight = "1596468673770-99f3d7f4999f"
    static let chicagoMillennium = "1531001142232-7d7aac16a63e"
    static let chicagoAerial = "1732740674539-74d1f760acfa"
    static let chicagoTowers = "1627140583146-23077865a2a8"
    static let chicagoRiverBoat = "1558638872-3d7081facdc0"
    static let aegeanView = "1533105079780-92b9be482077"
    static let venice = "1534113414509-0eec2bfb493f"
    static let santoriniDome = "1613395877344-13d4a8e0d49e"
    static let kyotoLane = "1493976040374-85c8e12f0c0e"
    static let duskRidge = "1545569341-9eb8b30979d9"
    static let aboveClouds = "1506905925346-21bda4d32df4"
    static let alpineValley = "1464822759023-fed622ff2c3b"
    static let overwater = "1514282401047-d79a71a590e8"
    static let jetty = "1573843981267-be1999ff37cd"
    static let eiffel = "1502602898657-3e91760cbb34"
    static let dubai = "1512453979798-5ea266f8880c"
    static let wing = "1436491865332-7a61a109cc05"
    static let lodgePool = "1566073771259-6a8506099945"
    static let seaDeck = "1582719508461-905c673771fd"
    static let jet = "1540962351504-03099e0a754b"
    static let blackSand = "1504829857797-ddff29c27927"
    static let aurora = "1531366936337-7c912a4589a7"
    static let tropicalPool = "1520250497591-112f2f40a3f4"
    static let duskPool = "1542314831-068cd1dbfeeb"
    static let braies = "1476514525535-07fb3b4ae5f1"
    static let canyon = "1469854523086-cc02fe5d8800"
    static let shoreline = "1507525428034-b723cf961d3e"
    static let alpineLake = "1501785888041-af3ef285b470"
    static let fuji = "1528164344705-47542687000d"
    static let parisBridge = "1499856871958-5b9627545d1a"
    static let cinqueTerre = "1516483638261-f4dbaf036963"
    static let cliffPool = "1540541338287-41700207dee6"
    static let palmPool = "1551882547-ff40c63fe5fa"
    static let villaEvening = "1571896349842-33c89424de2d"
    static let reef = "1544551763-46a013bb70d5"
    static let granite = "1559128010-7c1ad6e1b6a5"
    static let treehouse = "1586375300773-8384e3e4916f"
    static let cityNight = "1598935898639-81586f7d2129"
}

enum Catalog {
    static let amalfi = Destination(
        id: "amalfi", name: "Amalfi Coast", country: "Italy", adjective: "Italian",
        tagline: "Timeless towns, endless horizons.",
        summary: "Lemon terraces fall to a cobalt sea. Stay high in Ravello, above the noise, and let the coast come to you — by private boat, by vintage car, by long lunches that turn into evening.",
        categories: [.forYou, .coastal], hero: Pic.amalfiTown,
        gallery: [Pic.seaDeck, Pic.medAlley, Pic.cinqueTerre],
        latitude: 40.6492, longitude: 14.6116, bestSeason: "May – Sep",
        airport: "NAP", airportCity: "Naples", flightTime: "8h 50m", fromPrice: 18_400,
        stays: [
            Stay(id: "cimbrone", name: "Hotel Villa Cimbrone", location: "Ravello, Amalfi Coast", photo: Pic.amalfiTown, nightly: 2_150, note: "Terrace of Infinity suite"),
            Stay(id: "sirenuse", name: "Le Sirenuse", location: "Positano", photo: Pic.seaDeck, nightly: 2_900, note: "Sea-view junior suite"),
        ],
        experiences: [
            Experience(title: "Private Riva to Capri", detail: "Skipper, swim stops at the Faraglioni, lunch at Da Luigi", icon: "sailboat"),
            Experience(title: "Lemon grove & cooking", detail: "A morning with the Aceto family above Amalfi", icon: "leaf"),
            Experience(title: "Path of the Gods", detail: "Guided sunrise walk, car waiting in Nocelle", icon: "figure.hiking"),
            Experience(title: "Ravello Festival", detail: "Front-row seats on the Belvedere stage", icon: "music.note"),
            Experience(title: "Pompeii after hours", detail: "Private archaeologist, closed to the public", icon: "building.columns"),
        ],
        dinner: Restaurant(name: "Rossellinis", cuisine: "Terrace dining at Palazzo Avino, Ravello", time: "20:30")
    )

    static let newYork = Destination(
        id: "newyork", name: "New York", country: "United States", adjective: "New York",
        tagline: "The city that never asks you to wait.",
        summary: "House seats on Broadway, the Met after the crowds leave, a suite above Central Park. We open the doors New York keeps closed — and keep the car waiting outside.",
        categories: [.forYou, .cities], hero: Pic.nycDusk,
        gallery: [Pic.empireGolden, Pic.nycAvenue, Pic.nycHarbor],
        latitude: 40.7484, longitude: -73.9857, bestSeason: "Apr – Jun · Sep – Dec",
        airport: "JFK", airportCity: "New York", flightTime: "5h 35m", fromPrice: 14_200,
        stays: [
            Stay(id: "aman-ny", name: "Aman New York", location: "Crown Building, Fifth Avenue", photo: Pic.nycAerial, nightly: 3_200, note: "Corner suite with terrace"),
            Stay(id: "the-mark", name: "The Mark", location: "Upper East Side", photo: Pic.nycNight, nightly: 2_100, note: "Central Park suite"),
        ],
        experiences: [
            Experience(title: "The Met after hours", detail: "Private curator, galleries closed to the public", icon: "building.columns"),
            Experience(title: "Broadway house seats", detail: "Orchestra, centre, with a backstage visit", icon: "theatermasks"),
            Experience(title: "Helicopter over Manhattan", detail: "Doors-off, from the Downtown heliport", icon: "airplane.circle"),
            Experience(title: "Jazz at the Village Vanguard", detail: "Reserved front table, late set", icon: "music.note"),
            Experience(title: "Central Park at dawn", detail: "Guided walk, breakfast at the Boathouse", icon: "sunrise"),
        ],
        dinner: Restaurant(name: "Le Bernardin", cuisine: "Three-star seafood, Midtown", time: "19:30")
    )

    static let sanFrancisco = Destination(
        id: "sanfrancisco", name: "San Francisco", country: "United States", adjective: "Californian",
        tagline: "Fog, light, and the open Pacific.",
        summary: "Sail under the Golden Gate at dusk, lunch among the vines in Napa, and come back to a suite over the Bay. A city that rewards knowing exactly where to stand.",
        categories: [.cities, .coastal], hero: Pic.goldenGate,
        gallery: [Pic.goldenGateDusk, Pic.cableCar, Pic.goldenGateFog],
        latitude: 37.8199, longitude: -122.4783, bestSeason: "Sep – Nov",
        airport: "SFO", airportCity: "San Francisco", flightTime: "6h 30m", fromPrice: 13_900,
        stays: [
            Stay(id: "fs-embarcadero", name: "Four Seasons at Embarcadero", location: "Financial District", photo: Pic.sfNight, nightly: 1_600, note: "Bay-view suite"),
            Stay(id: "ritz-sf", name: "The Ritz-Carlton", location: "Nob Hill", photo: Pic.goldenGateTower, nightly: 1_400, note: "Club-level suite"),
        ],
        experiences: [
            Experience(title: "Sail under the Golden Gate", detail: "Private yacht at sunset, Sausalito return", icon: "sailboat"),
            Experience(title: "Napa by helicopter", detail: "Two estates, cellar tastings, lunch among the vines", icon: "wineglass"),
            Experience(title: "Alcatraz after dark", detail: "Private night tour with a historian", icon: "moon.stars"),
            Experience(title: "Muir Woods at first light", detail: "Before the gates open, with a naturalist", icon: "leaf"),
            Experience(title: "Cable car & Chinatown", detail: "A local guide and a dim sum lunch", icon: "tram"),
        ],
        dinner: Restaurant(name: "Atelier Crenn", cuisine: "Poetic culinaria, Cow Hollow", time: "19:30")
    )

    static let chicago = Destination(
        id: "chicago", name: "Chicago", country: "United States", adjective: "Chicago",
        tagline: "Architecture, blues, and a lake like a sea.",
        summary: "See the skyline from your own boat on the river, step into the Art Institute before it opens, and end the night at a jazz club Al Capone used to frequent.",
        categories: [.cities], hero: Pic.chicagoSunset,
        gallery: [Pic.chicagoRiverNight, Pic.chicagoMillennium, Pic.chicagoAerial],
        latitude: 41.8864, longitude: -87.6244, bestSeason: "May – Oct",
        airport: "ORD", airportCity: "Chicago", flightTime: "2h 45m", fromPrice: 9_800,
        stays: [
            Stay(id: "peninsula-chi", name: "The Peninsula Chicago", location: "Magnificent Mile", photo: Pic.chicagoTowers, nightly: 1_300, note: "Lake-view suite"),
            Stay(id: "waldorf-chi", name: "Waldorf Astoria Chicago", location: "Gold Coast", photo: Pic.chicagoRiverBoat, nightly: 1_100, note: "Signature suite"),
        ],
        experiences: [
            Experience(title: "Private architecture cruise", detail: "Your own boat on the river, with an architect", icon: "sailboat"),
            Experience(title: "Art Institute before opening", detail: "Impressionist galleries with a curator", icon: "paintpalette"),
            Experience(title: "Jazz at the Green Mill", detail: "Reserved booth for the late set", icon: "music.note"),
            Experience(title: "Skybox at Wrigley Field", detail: "Cubs game, catered", icon: "baseball"),
            Experience(title: "Sail Lake Michigan", detail: "Sunset charter with the skyline behind you", icon: "water.waves"),
        ],
        dinner: Restaurant(name: "Alinea", cuisine: "Three-star progressive, Lincoln Park", time: "19:00")
    )

    static let lakeComo = Destination(
        id: "como", name: "Lake Como", country: "Italy", adjective: "Lakeside",
        tagline: "Timeless beauty, endless discovery.",
        summary: "Villas at the water’s edge, gardens that tumble to the lake, mountains still white in May. Arrive by Riva, stay in Bellagio, and let the afternoons drift.",
        categories: [.forYou, .nature], hero: Pic.comoVarenna,
        gallery: [Pic.comoBalbianello, Pic.comoBellagio, Pic.comoDusk],
        latitude: 45.9853, longitude: 9.2598, bestSeason: "Apr – Oct",
        airport: "MXP", airportCity: "Milan Malpensa", flightTime: "8h 20m", fromPrice: 19_600,
        stays: [
            Stay(id: "villadeste", name: "Villa d’Este", location: "Cernobbio, Lake Como", photo: Pic.comoArches, nightly: 2_300, note: "Lake-view suite"),
            Stay(id: "passalacqua", name: "Passalacqua", location: "Moltrasio, Lake Como", photo: Pic.comoBalbianello, nightly: 3_400, note: "Garden suite"),
        ],
        experiences: [
            Experience(title: "Riva to Villa del Balbianello", detail: "Private launch, gardens before opening", icon: "sailboat"),
            Experience(title: "Lunch in Bellagio", detail: "Terrace table above the lake", icon: "fork.knife"),
            Experience(title: "Silk atelier, Como", detail: "Behind the scenes with a master weaver", icon: "scissors"),
            Experience(title: "Seaplane over the lake", detail: "From Aero Club Como, 30 minutes", icon: "airplane.circle"),
            Experience(title: "Monte Bisbino hike", detail: "Guide and picnic, views to the Alps", icon: "figure.hiking"),
        ],
        dinner: Restaurant(name: "Ristorante Mistral", cuisine: "Lakeside fine dining, Bellagio", time: "20:30")
    )

    static let santorini = Destination(
        id: "santorini", name: "Santorini", country: "Greece", adjective: "Aegean",
        tagline: "White light on a caldera of blue.",
        summary: "Wake to the caldera from a cave suite in Oia. We choreograph the island around the crowds — sunset on your own catamaran, wineries opened just for you.",
        categories: [.coastal, .islands], hero: Pic.oia,
        gallery: [Pic.santoriniDomes, Pic.santoriniDome, Pic.aegeanView],
        latitude: 36.4618, longitude: 25.3753, bestSeason: "May – Oct",
        airport: "JTR", airportCity: "Santorini", flightTime: "12h 10m", fromPrice: 16_900,
        stays: [
            Stay(id: "canaves", name: "Canaves Oia Epitome", location: "Oia, Santorini", photo: Pic.santoriniTerrace, nightly: 2_400, note: "Pool suite facing the caldera"),
            Stay(id: "katikies", name: "Katikies", location: "Oia, Santorini", photo: Pic.duskPool, nightly: 1_650, note: "Honeymoon suite"),
        ],
        experiences: [
            Experience(title: "Caldera by catamaran", detail: "Private crew, hot springs, sunset off Oia", icon: "sailboat"),
            Experience(title: "Assyrtiko tasting", detail: "Cellar door at Gaia, opened early for you", icon: "wineglass"),
            Experience(title: "Akrotiri with an archaeologist", detail: "The Bronze Age city, before opening", icon: "building.columns"),
            Experience(title: "Helicopter to Folegandros", detail: "Lunch on a quiet island, back by dusk", icon: "airplane.circle"),
        ],
        dinner: Restaurant(name: "Selene", cuisine: "Modern Cycladic, Pyrgos", time: "20:30")
    )

    static let kyoto = Destination(
        id: "kyoto", name: "Kyoto", country: "Japan", adjective: "Japanese",
        tagline: "A thousand years, kept quietly.",
        summary: "Temples before dawn, tea with a master, kaiseki that follows the season. We secure what can’t be booked: private gardens, a maiko evening, the last room at Aman.",
        categories: [.forYou, .cities], hero: Pic.kyotoLane,
        gallery: [Pic.sakura, Pic.torii, Pic.fuji],
        latitude: 35.0116, longitude: 135.7681, bestSeason: "Mar – May · Nov",
        airport: "KIX", airportCity: "Osaka Kansai", flightTime: "14h 05m", fromPrice: 22_300,
        stays: [
            Stay(id: "aman-kyoto", name: "Aman Kyoto", location: "Takagamine, Kyoto", photo: Pic.treehouse, nightly: 2_700, note: "Garden pavilion"),
            Stay(id: "hoshinoya", name: "Hoshinoya Kyoto", location: "Arashiyama", photo: Pic.lodgePool, nightly: 1_900, note: "River-view suite"),
        ],
        experiences: [
            Experience(title: "Dawn at Fushimi Inari", detail: "Before the gates fill, with a Shinto priest", icon: "sunrise"),
            Experience(title: "Tea with Sen family master", detail: "Private chakai in Urasenke", icon: "cup.and.saucer"),
            Experience(title: "Kaiseki at Kikunoi", detail: "Chef’s counter, 3-star", icon: "fork.knife"),
            Experience(title: "Gion evening", detail: "Ochaya dinner with a geiko", icon: "moon.stars"),
            Experience(title: "Shinkansen to Fuji", detail: "Green Car, guide at Kawaguchiko", icon: "tram"),
        ],
        dinner: Restaurant(name: "Kikunoi Honten", cuisine: "Seasonal kaiseki, Higashiyama", time: "19:00")
    )

    static let zermatt = Destination(
        id: "zermatt", name: "Zermatt", country: "Switzerland", adjective: "Alpine",
        tagline: "Under the Matterhorn, above it all.",
        summary: "Car-free streets, a chalet with a chef, guides who know where the snow is best this morning. Helicopter access when the lifts won’t do.",
        categories: [.alpine, .nature], hero: Pic.aboveClouds,
        gallery: [Pic.matterhorn, Pic.alpineValley, Pic.duskRidge],
        latitude: 46.0207, longitude: 7.7491, bestSeason: "Dec – Apr",
        airport: "ZRH", airportCity: "Zurich", flightTime: "8h 05m", fromPrice: 24_800,
        stays: [
            Stay(id: "omnia", name: "The Omnia", location: "Zermatt", photo: Pic.matterhorn, nightly: 1_850, note: "Matterhorn suite"),
            Stay(id: "chalet", name: "Chalet Les Anges", location: "Zermatt", photo: Pic.duskRidge, nightly: 6_500, note: "Fully staffed, sleeps 10"),
        ],
        experiences: [
            Experience(title: "Heli-ski the Monte Rosa", detail: "IFMGA guide, first tracks", icon: "snowflake"),
            Experience(title: "Lunch at Chez Vrony", detail: "Terrace table, Matterhorn view", icon: "fork.knife"),
            Experience(title: "Private ski school", detail: "Instructor for the children, all week", icon: "figure.skiing.downhill"),
            Experience(title: "Gornergrat at night", detail: "Stargazing above 3,000 m", icon: "sparkles"),
        ],
        dinner: Restaurant(name: "Chez Vrony", cuisine: "Alpine terrace above Zermatt", time: "19:30")
    )

    static let maldives = Destination(
        id: "maldives", name: "The Maldives", country: "Maldives", adjective: "Island",
        tagline: "Nothing but water and time.",
        summary: "An overwater villa with a slide into the lagoon. Seaplane in, shoes off. We plan the days around the tide and the manta season.",
        categories: [.forYou, .islands, .coastal], hero: Pic.overwater,
        gallery: [Pic.overwaterArc, Pic.floatingBreakfast, Pic.reef],
        latitude: 5.3170, longitude: 73.0620, bestSeason: "Nov – Apr",
        airport: "MLE", airportCity: "Malé", flightTime: "18h 30m", fromPrice: 28_700,
        stays: [
            Stay(id: "soneva", name: "Soneva Jani", location: "Noonu Atoll", photo: Pic.floatingBreakfast, nightly: 4_200, note: "Water retreat with slide"),
            Stay(id: "cheval", name: "Cheval Blanc Randheli", location: "Noonu Atoll", photo: Pic.tropicalPool, nightly: 3_600, note: "Island villa"),
        ],
        experiences: [
            Experience(title: "Manta snorkel, Hanifaru Bay", detail: "Marine biologist, dawn departure", icon: "water.waves"),
            Experience(title: "Sandbank dinner", detail: "Your own island for an evening", icon: "moon.stars"),
            Experience(title: "Seaplane photography", detail: "Doors-off flight over the atoll", icon: "camera"),
            Experience(title: "Overwater spa ritual", detail: "Two-hour couples treatment", icon: "leaf"),
        ],
        dinner: Restaurant(name: "The Gathering", cuisine: "Overwater dining at Soneva Jani", time: "19:30")
    )

    static let dolomites = Destination(
        id: "dolomites", name: "The Dolomites", country: "Italy", adjective: "Dolomite",
        tagline: "Pale mountains, green water.",
        summary: "Lakes the colour of glass and peaks that blush at sunset. Hike hut to hut with a guide, return to a spa carved into the forest.",
        categories: [.alpine, .nature], hero: Pic.braies,
        gallery: [Pic.alpineLake, Pic.duskRidge],
        latitude: 46.6943, longitude: 12.0857, bestSeason: "Jun – Sep",
        airport: "VCE", airportCity: "Venice", flightTime: "8h 55m", fromPrice: 15_200,
        stays: [
            Stay(id: "forestis", name: "Forestis", location: "Brixen, South Tyrol", photo: Pic.alpineLake, nightly: 1_400, note: "Tower suite"),
            Stay(id: "rosa", name: "Rosa Alpina", location: "San Cassiano", photo: Pic.alpineValley, nightly: 1_750, note: "Dolomites suite"),
        ],
        experiences: [
            Experience(title: "Seceda ridge walk", detail: "Guide and lift tickets arranged", icon: "figure.hiking"),
            Experience(title: "Rowing on Lago di Braies", detail: "Early boat before the crowds", icon: "sailboat"),
            Experience(title: "Lunch at a rifugio", detail: "Table held at Rifugio Scotoni", icon: "fork.knife"),
            Experience(title: "Via ferrata, Tofane", detail: "Private mountain guide", icon: "mountain.2"),
        ],
        dinner: Restaurant(name: "St. Hubertus", cuisine: "Three-star Alpine, San Cassiano", time: "19:30")
    )

    static let paris = Destination(
        id: "paris", name: "Paris", country: "France", adjective: "Parisian",
        tagline: "The city, as insiders know it.",
        summary: "Private viewings, ateliers that don’t take appointments, the table that’s always full. For boards and families alike, the city opens differently with Wonder.",
        categories: [.cities], hero: Pic.eiffel,
        gallery: [Pic.parisBridge],
        latitude: 48.8584, longitude: 2.2945, bestSeason: "Apr – Jun · Sep",
        airport: "CDG", airportCity: "Paris", flightTime: "7h 15m", fromPrice: 14_600,
        stays: [
            Stay(id: "cheval-paris", name: "Cheval Blanc Paris", location: "1st arrondissement", photo: Pic.parisBridge, nightly: 2_300, note: "Seine-view suite"),
            Stay(id: "bristol", name: "Le Bristol", location: "8th arrondissement", photo: Pic.duskPool, nightly: 1_800, note: "Panoramic suite"),
        ],
        experiences: [
            Experience(title: "Louvre before opening", detail: "Private curator, Denon wing", icon: "building.columns"),
            Experience(title: "Atelier visit, Rue Cambon", detail: "Haute couture fitting", icon: "scissors"),
            Experience(title: "Dinner at Plénitude", detail: "Chef’s table, Arnaud Donckele", icon: "fork.knife"),
            Experience(title: "Seine by private boat", detail: "Champagne at golden hour", icon: "sailboat"),
        ],
        dinner: Restaurant(name: "Plénitude", cuisine: "Chef’s table, Cheval Blanc", time: "20:00")
    )

    static let iceland = Destination(
        id: "iceland", name: "Iceland", country: "Iceland", adjective: "Nordic",
        tagline: "Fire, ice, and the northern lights.",
        summary: "Black-sand beaches, glaciers by super-jeep, and an aurora alarm at the lodge. We fly you by helicopter to places the roads don’t reach.",
        categories: [.nature], hero: Pic.aurora,
        gallery: [Pic.blackSand],
        latitude: 63.4186, longitude: -19.0060, bestSeason: "Sep – Mar",
        airport: "KEF", airportCity: "Reykjavík", flightTime: "5h 40m", fromPrice: 19_900,
        stays: [
            Stay(id: "retreat", name: "The Retreat at Blue Lagoon", location: "Grindavík", photo: Pic.blackSand, nightly: 1_700, note: "Lagoon suite"),
            Stay(id: "deplar", name: "Deplar Farm", location: "Troll Peninsula", photo: Pic.aurora, nightly: 2_600, note: "All-inclusive, heli-access"),
        ],
        experiences: [
            Experience(title: "Glacier by helicopter", detail: "Landing on Langjökull", icon: "airplane.circle"),
            Experience(title: "Aurora watch", detail: "Wake-up call when the lights appear", icon: "sparkles"),
            Experience(title: "Ice cave, Vatnajökull", detail: "Private guide and super-jeep", icon: "snowflake"),
            Experience(title: "Reynisfjara at dawn", detail: "Photographer-led", icon: "camera"),
        ],
        dinner: Restaurant(name: "Dill", cuisine: "New Nordic, Reykjavík", time: "19:30")
    )

    static let bali = Destination(
        id: "bali", name: "Ubud, Bali", country: "Indonesia", adjective: "Balinese",
        tagline: "Jungle, ritual, and rest.",
        summary: "A tented villa above the Wos river, a healer in the morning, rice terraces by bicycle. Slow days, carefully arranged.",
        categories: [.nature, .islands], hero: Pic.tropicalPool,
        gallery: [Pic.treehouse, Pic.lodgePool],
        latitude: -8.5069, longitude: 115.2625, bestSeason: "Apr – Oct",
        airport: "DPS", airportCity: "Denpasar", flightTime: "21h 40m", fromPrice: 17_800,
        stays: [
            Stay(id: "capella", name: "Capella Ubud", location: "Keliki, Ubud", photo: Pic.treehouse, nightly: 1_500, note: "Lodge tent"),
            Stay(id: "sayan", name: "Four Seasons Sayan", location: "Ayung River", photo: Pic.lodgePool, nightly: 1_200, note: "Riverfront villa"),
        ],
        experiences: [
            Experience(title: "Water blessing, Tirta Empul", detail: "With a local priest", icon: "drop"),
            Experience(title: "Rice terraces by bike", detail: "Jatiluwih, guided", icon: "bicycle"),
            Experience(title: "Mount Batur sunrise", detail: "Breakfast at the summit", icon: "sunrise"),
            Experience(title: "Locavore NXT", detail: "Chef’s table tasting", icon: "fork.knife"),
        ],
        dinner: Restaurant(name: "Locavore NXT", cuisine: "Chef’s table, Ubud", time: "19:00")
    )

    static let dubai = Destination(
        id: "dubai", name: "Dubai", country: "UAE", adjective: "Arabian",
        tagline: "Desert stillness, city light.",
        summary: "Dunes at dawn by vintage Land Rover, then a suite above the Gulf. Ideal for a long weekend, an investor roadshow, or both.",
        categories: [.cities], hero: Pic.dubai,
        gallery: [Pic.palmPool, Pic.canyon],
        latitude: 25.1972, longitude: 55.2744, bestSeason: "Nov – Mar",
        airport: "DXB", airportCity: "Dubai", flightTime: "12h 30m", fromPrice: 16_200,
        stays: [
            Stay(id: "oneandonly", name: "One&Only Royal Mirage", location: "Jumeirah", photo: Pic.palmPool, nightly: 1_400, note: "Prince suite"),
            Stay(id: "almaha", name: "Al Maha Desert Resort", location: "Dubai Desert Reserve", photo: Pic.canyon, nightly: 1_900, note: "Emir suite with pool"),
        ],
        experiences: [
            Experience(title: "Dunes by vintage Land Rover", detail: "Falconry and breakfast in the desert", icon: "sun.horizon"),
            Experience(title: "Private dhow on the Creek", detail: "Old Dubai at dusk", icon: "sailboat"),
            Experience(title: "Dinner at Trèsind Studio", detail: "Chef’s counter", icon: "fork.knife"),
            Experience(title: "Burj Khalifa, level 154", detail: "Private lounge at sunset", icon: "building.2"),
        ],
        dinner: Restaurant(name: "Trèsind Studio", cuisine: "Progressive Indian, Dubai", time: "20:00")
    )

    static let seychelles = Destination(
        id: "seychelles", name: "Seychelles", country: "Seychelles", adjective: "Island",
        tagline: "Granite, palms, and private coves.",
        summary: "Islands of sculpted granite and turtle beaches. Take a whole island for the family, with a boat and a naturalist on call.",
        categories: [.islands, .coastal], hero: Pic.granite,
        gallery: [Pic.shoreline, Pic.reef],
        latitude: -4.3594, longitude: 55.8398, bestSeason: "Apr – May · Oct – Nov",
        airport: "SEZ", airportCity: "Mahé", flightTime: "19h 20m", fromPrice: 31_500,
        stays: [
            Stay(id: "north", name: "North Island", location: "North Island", photo: Pic.granite, nightly: 6_800, note: "Private villa, all-inclusive"),
            Stay(id: "zil", name: "Six Senses Zil Pasyon", location: "Félicité", photo: Pic.cliffPool, nightly: 2_100, note: "Ocean pool villa"),
        ],
        experiences: [
            Experience(title: "Anse Source d’Argent", detail: "By boat, before the day-trippers", icon: "sun.max"),
            Experience(title: "Turtle walk", detail: "With the island’s conservationist", icon: "tortoise"),
            Experience(title: "Vallée de Mai", detail: "Coco de mer forest, guided", icon: "leaf"),
            Experience(title: "Deep-sea fishing", detail: "Sportfisher, catch and release", icon: "water.waves"),
        ],
        dinner: Restaurant(name: "Le Château de Feuilles", cuisine: "Creole seafood, Praslin", time: "19:30")
    )

    static let all: [Destination] = [newYork, lakeComo, sanFrancisco, chicago, amalfi, kyoto, maldives, santorini, zermatt, dolomites, paris, iceland, bali, dubai, seychelles]

    static func destination(id: String) -> Destination? { all.first { $0.id == id } }
}
