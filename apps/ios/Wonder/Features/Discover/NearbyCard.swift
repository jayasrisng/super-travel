import SwiftUI

/// "Around you": the agent's pick near the traveler's live location, with category
/// switches and a way to pin it to the Lock Screen.
struct NearbyCard: View {
    @Environment(\.openURL) private var openURL
    private var nearby: NearbyModel { .shared }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack(spacing: 6) {
                Image(systemName: "location.fill")
                    .font(.system(size: 10, weight: .semibold))
                Eyebrow(["Around you", nearby.result?.locality].compactMap { $0 }.joined(separator: " · "), color: .ink, size: 10)
                Spacer()
                if nearby.status == .searching || nearby.status == .locating {
                    ProgressView().controlSize(.mini).tint(Color.ink)
                }
            }
            .foregroundStyle(Color.ink)

            recommendation
                .padding(.top, 14)
                .animation(.easeInOut(duration: 0.3), value: nearby.top)

            Hairline().padding(.vertical, 16)

            HStack(spacing: 8) {
                ForEach(NearbyCategory.allCases, id: \.self) { category in
                    categoryButton(category)
                }
            }

            lockScreenButton
                .padding(.top, 14)
        }
        .padding(20)
        .glassPanel(cornerRadius: 28)
        .task { await nearby.start() }
    }

    @ViewBuilder
    private var recommendation: some View {
        switch nearby.status {
        case .idle, .locating:
            placeholder("Finding places around you…", "Your agent is checking what’s close by.")
        case .needsPermission:
            VStack(alignment: .leading, spacing: 10) {
                placeholder("See what’s around you", "Share your location and your agent will pick places to eat, meet, stay and shop nearby.")
                Button("Share location") { Task { await nearby.start() } }
                    .buttonStyle(PrimaryButtonStyle())
            }
        case .denied:
            VStack(alignment: .leading, spacing: 10) {
                placeholder("Location is off", "Turn on location for Wonder in Settings to get nearby recommendations.")
                Button("Open Settings") {
                    if let url = URL(string: UIApplication.openSettingsURLString) { openURL(url) }
                }
                .buttonStyle(PrimaryButtonStyle())
            }
        case .empty:
            placeholder("Nothing close by", "No \(nearby.category.title.lowercased()) within a short walk. Try another category.")
        case .searching, .ready:
            if let pick = nearby.top {
                VStack(alignment: .leading, spacing: 4) {
                    Eyebrow("Agent’s pick · \(nearby.category.title)", color: .textSoft, size: 9.5)
                    Text(pick.name)
                        .font(WFont.display(26))
                        .foregroundStyle(Color.ink)
                        .padding(.top, 2)
                    Text("\(pick.kind) · \(pick.walkText)")
                        .font(WFont.body(13, weight: .medium))
                        .foregroundStyle(Color.textSoft)
                    Text(pick.note)
                        .font(WFont.body(14))
                        .foregroundStyle(Color.ink)
                        .lineSpacing(2)
                        .padding(.top, 6)
                    if let others = nearby.result?.picks.dropFirst(), !others.isEmpty {
                        Text("Also nearby: " + others.prefix(2).map(\.name).joined(separator: ", "))
                            .font(WFont.body(12))
                            .foregroundStyle(Color.textSoft)
                            .lineLimit(1)
                            .padding(.top, 6)
                    }
                }
                .id(pick.id)
                .transition(.opacity)
            } else {
                placeholder("Finding places around you…", "Your agent is checking what’s close by.")
            }
        }
    }

    private func placeholder(_ title: String, _ detail: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(WFont.display(22))
                .foregroundStyle(Color.ink)
            Text(detail)
                .font(WFont.body(13))
                .foregroundStyle(Color.textSoft)
        }
    }

    private func categoryButton(_ category: NearbyCategory) -> some View {
        let selected = nearby.category == category
        return Button {
            withAnimation(.spring(duration: 0.3)) { nearby.select(category) }
        } label: {
            VStack(spacing: 5) {
                Image(systemName: category.symbol)
                    .font(.system(size: 15, weight: .medium))
                Text(category.title)
                    .font(WFont.body(11, weight: .medium))
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
            }
            .foregroundStyle(SolidInk(inverse: selected))
            .frame(maxWidth: .infinity)
            .frame(height: 58)
            .background(selected ? AnyShapeStyle(.solidInk) : AnyShapeStyle(Color.well), in: .rect(cornerRadius: 16))
        }
        .buttonStyle(PressableStyle())
        .disabled(nearby.status == .needsPermission || nearby.status == .denied)
    }

    @ViewBuilder
    private var lockScreenButton: some View {
        if nearby.isOnLockScreen {
            HStack {
                Label("On your Lock Screen", systemImage: "checkmark.circle.fill")
                    .font(WFont.body(13, weight: .semibold))
                    .foregroundStyle(Color.verified)
                Spacer()
                Button("Remove") { Task { await nearby.removeFromLockScreen() } }
                    .font(WFont.body(13, weight: .medium))
                    .foregroundStyle(Color.textSoft)
            }
            .frame(height: 44)
        } else {
            Button {
                Task { await nearby.showOnLockScreen() }
            } label: {
                Label("Show on Lock Screen", systemImage: "lock.iphone")
            }
            .buttonStyle(PrimaryButtonStyle())
            .disabled(nearby.top == nil)
            .opacity(nearby.top == nil ? 0.4 : 1)
        }
    }
}
