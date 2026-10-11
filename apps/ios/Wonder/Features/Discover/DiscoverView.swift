import SwiftUI

struct DiscoverView: View {
    @Environment(WonderStore.self) private var store
    @State private var category: TravelCategory = .forYou
    @State private var featuredID: String?
    @State private var query = ""
    @FocusState private var searchFocused: Bool

    private var filtered: [Destination] {
        Catalog.all.filter { $0.categories.contains(category) }
    }

    /// The place currently filling the screen.
    private var featured: Destination {
        filtered.first { $0.id == featuredID } ?? filtered.first ?? Catalog.amalfi
    }

    var body: some View {
        NavigationStack {
            ScrollViewReader { proxy in
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    // First screen: the photograph is the hero.
                    VStack(alignment: .leading, spacing: 0) {
                        header.legible()
                        Text("Where shall\nwe go?")
                            .font(WFont.display(42))
                            .foregroundStyle(Color.ink)
                            .lineSpacing(-2)
                            .legible()
                            .padding(.top, 28)
                            .padding(.horizontal, 24)

                        searchField
                            .padding(.top, 24)
                            .padding(.horizontal, 20)

                        categoryBar
                            .padding(.top, 26)

                        Spacer(minLength: 24)

                        featuredPager
                    }
                    .containerRelativeFrame(.vertical) { height, _ in height - 24 }

                    NearbyCard()
                        .id("nearby")
                        .padding(.horizontal, 20)
                        .padding(.top, 28)

                    AgentPulseCard()
                        .padding(.horizontal, 20)
                        .padding(.top, 20)

                    SectionHeader(title: "Everywhere we go", eyebrow: "\(Catalog.all.count) destinations")
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 14) {
                            ForEach(Catalog.all) { d in
                                NavigationLink(value: d) { DestinationTile(destination: d) }
                                    .buttonStyle(PressableStyle())
                            }
                        }
                        .padding(.horizontal, 20)
                    }
                    .scrollClipDisabled()

                    SectionHeader(title: "Iconic stays", eyebrow: "Held for members")
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 14) {
                            ForEach(Catalog.all.prefix(7)) { d in
                                NavigationLink(value: d) { StayTile(stay: d.stays[0], destination: d) }
                                    .buttonStyle(PressableStyle())
                            }
                        }
                        .padding(.horizontal, 20)
                    }
                    .scrollClipDisabled()

                    BusinessBanner()
                        .padding(.horizontal, 20)
                        .padding(.top, 36)

                    Text("Considered journeys.\nQuiet intelligence.")
                        .font(WFont.display(17))
                        .italic()
                        .foregroundStyle(Color.textSoft)
                        .multilineTextAlignment(.center)
                        .frame(maxWidth: .infinity)
                        .padding(.top, 44)
                        .padding(.bottom, 40)
                }
            }
            .onChange(of: store.nearbyFocusRequests) {
                withAnimation(.spring(duration: 0.6)) { proxy.scrollTo("nearby", anchor: .top) }
            }
            }
            .scrollDismissesKeyboard(.interactively)
            .statusBarScrim(.black.opacity(0.25))
            .background { Backdrop(photo: featured.hero, veil: 0.4) }
            .toolbar(.hidden, for: .navigationBar)
            .navigationDestination(for: Destination.self) { d in
                DestinationDetailView(destination: d)
            }
            .onChange(of: category) { featuredID = filtered.first?.id }
        }
    }

    private var featuredPager: some View {
        VStack(spacing: 14) {
            ScrollView(.horizontal, showsIndicators: false) {
                LazyHStack(spacing: 0) {
                    ForEach(filtered) { d in
                        // No caption: the photograph behind is the feature. Swipe to change it, tap to open it.
                        NavigationLink(value: d) {
                            Color.clear
                                .frame(height: 220)
                                .contentShape(.rect)
                        }
                        .buttonStyle(.plain)
                        .accessibilityLabel("\(d.name), \(d.country)")
                            .padding(.horizontal, 24)
                            .containerRelativeFrame(.horizontal)
                    }
                }
                .scrollTargetLayout()
            }
            .scrollTargetBehavior(.paging)
            .scrollPosition(id: $featuredID)
            .id(category)

            HStack(spacing: 6) {
                ForEach(filtered) { d in
                    Capsule()
                        .fill(d.id == featured.id ? Color.ink : Color.textFaint)
                        .frame(width: d.id == featured.id ? 18 : 6, height: 6)
                }
            }
            .animation(.spring(duration: 0.35), value: featured.id)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 24)
        }
    }

    private var header: some View {
        HStack {
            WonderLogo(height: 22)
            Spacer()
            Button {
                store.selectedTab = .profile
            } label: {
                Image(systemName: "person")
                    .font(.system(size: 15, weight: .medium))
                    .foregroundStyle(Color.ink)
                    .frame(width: 40, height: 40)
                    .glassCircle()
            }
        }
        .padding(.horizontal, 24)
        .padding(.top, 8)
    }

    private var searchField: some View {
        HStack(spacing: 12) {
            Image(systemName: "magnifyingglass")
                .font(.system(size: 15, weight: .medium))
                .foregroundStyle(Color.textSoft)
            TextField(
                "",
                text: $query,
                prompt: Text("A quiet week by the lake").foregroundStyle(Color.textSoft)
            )
            .font(WFont.body(15))
            .foregroundStyle(Color.ink)
            .focused($searchFocused)
            .submitLabel(.go)
            .onSubmit(submit)
            Button(action: submit) {
                Image(systemName: "arrow.right")
                    .font(.system(size: 15, weight: .medium))
                    .foregroundStyle(Color.ink)
                    .frame(width: 34, height: 34)
            }
        }
        .padding(.leading, 18)
        .padding(.trailing, 10)
        .frame(height: 52)
        .glassCapsule()
    }

    private func submit() {
        let text = query.isEmpty ? "A quiet week by the lake" : query
        searchFocused = false
        query = ""
        store.ask(text)
    }

    private var categoryBar: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(TravelCategory.allCases) { c in
                    let selected = category == c
                    Button {
                        withAnimation(.spring(duration: 0.4)) { category = c }
                    } label: {
                        Group {
                            if selected {
                                Text(c.rawValue)
                                    .foregroundStyle(.white)
                                    .padding(.horizontal, 16)
                                    .frame(height: 36)
                                    .background(.black, in: .capsule)
                            } else {
                                Text(c.rawValue)
                                    .foregroundStyle(Color.ink)
                                    .padding(.horizontal, 16)
                                    .frame(height: 36)
                                    .frostedCapsule()
                            }
                        }
                        .font(WFont.body(13, weight: .medium))
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 20)
        }
    }
}

// MARK: - Pieces

struct SectionHeader: View {
    let title: String
    var eyebrow: String? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            if let eyebrow { Eyebrow(eyebrow, color: .textSoft) }
            Text(title)
                .font(WFont.display(24))
                .foregroundStyle(Color.ink)
        }
        .legible()
        .padding(.horizontal, 24)
        .padding(.top, 36)
        .padding(.bottom, 14)
    }
}

struct DestinationTile: View {
    let destination: Destination

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Photo(id: destination.hero, width: 600)
                .frame(width: 168, height: 220)
                .clipShape(.rect(cornerRadius: 20))
            VStack(alignment: .leading, spacing: 3) {
                Text(destination.name)
                    .font(WFont.display(17))
                    .foregroundStyle(Color.ink)
                Text(destination.country)
                    .font(WFont.body(12))
                    .foregroundStyle(Color.ink.opacity(0.55))
            }
        }
        .frame(width: 168, alignment: .leading)
    }
}

struct StayTile: View {
    let stay: Stay
    let destination: Destination

    var body: some View {
        ZStack(alignment: .bottomLeading) {
            Photo(id: stay.photo, width: 800)
            Scrim(strength: 0.9)
            VStack(alignment: .leading, spacing: 4) {
                Text(stay.name)
                    .font(WFont.display(18))
                    .foregroundStyle(Color.ink)
                    .lineLimit(1)
                Text(stay.location)
                    .font(WFont.body(12))
                    .foregroundStyle(Color.ink.opacity(0.7))
                Text("\(Fmt.money(stay.nightly)) / night")
                    .font(WFont.body(11, weight: .medium))
                    .foregroundStyle(Color.ink)
                    .padding(.top, 2)
            }
            .padding(16)
        }
        .frame(width: 260, height: 180)
        .clipShape(.rect(cornerRadius: 20))
    }
}

/// Shows the agent working quietly in the background.
struct AgentPulseCard: View {
    @Environment(WonderStore.self) private var store

    var body: some View {
        Button {
            store.selectedTab = .trips
        } label: {
            HStack(alignment: .top, spacing: 14) {
                ZStack {
                    PulseRing(style: Color.ink.opacity(0.3), from: 0.9, to: 1.25)
                        .frame(width: 34, height: 34)
                    Circle().fill(.solidInk).frame(width: 30, height: 30)
                    Text("W").font(WFont.wordmark(16)).foregroundStyle(.solidInkInverse)
                }
                VStack(alignment: .leading, spacing: 5) {
                    HStack {
                        Eyebrow("Your agent is working", color: .ink, size: 9.5)
                        Spacer()
                        Image(systemName: "chevron.right")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundStyle(Color.ink.opacity(0.5))
                    }
                    Text(store.activity.first?.title ?? "Watching your journeys")
                        .font(WFont.body(15, weight: .medium))
                        .foregroundStyle(Color.ink)
                        .multilineTextAlignment(.leading)
                    Text("Monitoring 3 fares · holding 2 suites · \(store.upcomingTrips.count) journeys ahead")
                        .font(WFont.body(12))
                        .foregroundStyle(Color.textSoft)
                        .multilineTextAlignment(.leading)
                }
            }
            .padding(16)
            .glassPanel(cornerRadius: 22)
        }
        .buttonStyle(PressableStyle())
    }
}

struct BusinessBanner: View {
    @Environment(WonderStore.self) private var store

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Eyebrow("Wonder for Business", color: .textSoft)
                Spacer()
                Image(systemName: "airplane")
                    .font(.system(size: 14))
                    .foregroundStyle(Color.ink)
                    .frame(width: 36, height: 36)
                    .background(Color.well, in: .circle)
            }
            Text("Offsites, roadshows,\nboard retreats.")
                .font(WFont.display(26))
                .foregroundStyle(Color.ink)
            Text("One agent for your whole team — policy-aware, invoiced centrally, awake at 3am when a flight moves.")
                .font(WFont.body(13))
                .foregroundStyle(Color.textSoft)
                .lineSpacing(2)
            Button {
                store.ask("Plan a board offsite in Paris for 8 executives, 3 nights")
            } label: {
                HStack(spacing: 6) {
                    Text("Plan an offsite")
                    Image(systemName: "arrow.right").font(.system(size: 11, weight: .semibold))
                }
                .font(WFont.body(13, weight: .semibold))
                .foregroundStyle(.solidInkInverse)
                .padding(.horizontal, 16)
                .frame(height: 38)
                .background(.solidInk, in: .capsule)
            }
            .padding(.top, 6)
        }
        .padding(22)
        .glassPanel(cornerRadius: 28)
    }
}
