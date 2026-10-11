import SwiftUI

struct DestinationDetailView: View {
    @Environment(WonderStore.self) private var store
    let destination: Destination

    @State private var backdrop: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                // Title sits low on the first screen, over the photograph.
                VStack(alignment: .leading, spacing: 10) {
                    Spacer()
                    Eyebrow(destination.country, color: .textSoft)
                    Text(destination.name)
                        .font(WFont.display(48))
                        .foregroundStyle(Color.ink)
                    Text(destination.tagline)
                        .font(WFont.display(18))
                        .italic()
                        .foregroundStyle(Color.ink)
                    facts.padding(.top, 18)
                }
                .legible()
                .containerRelativeFrame(.vertical) { height, _ in height - 40 }

                Text(destination.summary)
                    .font(WFont.display(19))
                    .foregroundStyle(Color.ink)
                    .lineSpacing(5)
                    .padding(22)
                    .glassPanel(cornerRadius: 24)

                gallery
                    .padding(.top, 20)

                SectionHeader(title: "Signature stays", eyebrow: "Wonder holds availability")
                    .padding(.horizontal, -24)
                VStack(spacing: 12) {
                    ForEach(destination.stays) { stay in StayRow(stay: stay) }
                }

                SectionHeader(title: "Moments we’d arrange", eyebrow: "Experiences")
                    .padding(.horizontal, -24)
                VStack(spacing: 0) {
                    ForEach(Array(destination.experiences.enumerated()), id: \.offset) { i, exp in
                        ExperienceRow(experience: exp)
                        if i < destination.experiences.count - 1 {
                            Hairline().padding(.leading, 56)
                        }
                    }
                }
                .padding(.horizontal, 18)
                .padding(.vertical, 4)
                .glassPanel(cornerRadius: 24)

                SectionHeader(title: "The lay of the land", eyebrow: destination.country)
                    .padding(.horizontal, -24)
                SatelliteMap(coordinate: destination.coordinate, title: destination.name)
                    .frame(height: 300)
                    .clipShape(.rect(cornerRadius: 24))
            }
            .padding(.horizontal, 20)
            .padding(.bottom, 24)
        }
        .statusBarScrim(.black.opacity(0.25))
        .background { Backdrop(photo: backdrop ?? destination.hero, veil: 0.38) }
        .toolbar(.visible, for: .navigationBar)
        .toolbar(.hidden, for: .tabBar)
        .toolbarBackground(.hidden, for: .navigationBar)
        .navigationBarTitleDisplayMode(.inline)
        .safeAreaInset(edge: .bottom) { planBar }
    }

    private var facts: some View {
        HStack(spacing: 0) {
            fact("Best season", destination.bestSeason)
            Rectangle().fill(Color.ink.opacity(0.2)).frame(width: 0.5, height: 34)
            fact("From JFK", destination.flightTime)
            Rectangle().fill(Color.ink.opacity(0.2)).frame(width: 0.5, height: 34)
            fact("From", Fmt.money(destination.fromPrice))
        }
        .padding(.vertical, 16)
        .glassPanel(cornerRadius: 18)
    }

    private func fact(_ label: String, _ value: String) -> some View {
        VStack(spacing: 6) {
            Eyebrow(label, color: .textSoft, size: 9)
            Text(value)
                .font(WFont.body(13, weight: .medium))
                .foregroundStyle(Color.ink)
                .lineLimit(1)
                .minimumScaleFactor(0.8)
        }
        .frame(maxWidth: .infinity)
    }

    private var gallery: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                ForEach([destination.hero] + destination.gallery, id: \.self) { id in
                    let current = (backdrop ?? destination.hero) == id
                    Button {
                        backdrop = id
                    } label: {
                        Photo(id: id, width: 900)
                            .frame(width: 150, height: 200)
                            .clipShape(.rect(cornerRadius: 18))
                            .overlay(
                                RoundedRectangle(cornerRadius: 18)
                                    .strokeBorder(Color.ink, lineWidth: current ? 2 : 0)
                            )
                    }
                    .buttonStyle(PressableStyle())
                }
            }
        }
        .scrollClipDisabled()
    }

    private var planBar: some View {
        HStack(spacing: 14) {
            VStack(alignment: .leading, spacing: 2) {
                Text("From \(Fmt.money(destination.fromPrice))")
                    .font(WFont.display(18))
                    .foregroundStyle(Color.ink)
                Text("per person, all-inclusive")
                    .font(WFont.body(11))
                    .foregroundStyle(Color.ink.opacity(0.55))
            }
            Spacer()
            Button {
                store.ask("Plan a week in \(destination.name) for two")
            } label: {
                HStack(spacing: 8) {
                    Image(systemName: "sparkles").font(.system(size: 13))
                    Text("Plan this journey")
                }
                .lineLimit(1)
                .fixedSize()
                .font(WFont.body(14, weight: .medium))
                .foregroundStyle(.solidInkInverse)
                .padding(.horizontal, 20)
                .frame(height: 48)
                .background(.solidInk, in: .capsule)
            }
            .buttonStyle(PressableStyle())
        }
        .padding(.leading, 22)
        .padding(.trailing, 8)
        .padding(.vertical, 8)
        .glassCapsule()
        .padding(.horizontal, 16)
        .padding(.bottom, 4)
    }
}

struct StayRow: View {
    let stay: Stay

    var body: some View {
        HStack(spacing: 14) {
            Photo(id: stay.photo, width: 400)
                .frame(width: 92, height: 92)
                .clipShape(.rect(cornerRadius: 14))
            VStack(alignment: .leading, spacing: 4) {
                Text(stay.name)
                    .font(WFont.display(18))
                    .foregroundStyle(Color.ink)
                Text(stay.location)
                    .font(WFont.body(12))
                    .foregroundStyle(Color.ink.opacity(0.6))
                HStack(spacing: 6) {
                    Text(stay.note)
                    Text("·")
                    Text("\(Fmt.money(stay.nightly))/night")
                }
                .font(WFont.body(11, weight: .medium))
                .foregroundStyle(Color.ink)
                .lineLimit(1)
                .minimumScaleFactor(0.8)
                .padding(.top, 2)
            }
            Spacer(minLength: 0)
        }
        .padding(10)
        .glassPanel(cornerRadius: 20)
    }
}

struct ExperienceRow: View {
    let experience: Experience

    var body: some View {
        HStack(alignment: .top, spacing: 16) {
            Image(systemName: experience.icon)
                .font(.system(size: 15))
                .foregroundStyle(Color.ink)
                .frame(width: 40, height: 40)
                .background(Color.well, in: .circle)
            VStack(alignment: .leading, spacing: 4) {
                Text(experience.title)
                    .font(WFont.body(15, weight: .medium))
                    .foregroundStyle(Color.ink)
                Text(experience.detail)
                    .font(WFont.body(13))
                    .foregroundStyle(Color.textSoft)
            }
            Spacer(minLength: 0)
        }
        .padding(.vertical, 14)
    }
}
