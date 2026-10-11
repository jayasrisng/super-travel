import SwiftUI
import MessageUI

struct ProfileView: View {
    @Environment(WonderStore.self) private var store
    @State private var alerts = NearbyAlertSettings.shared
    @State private var showAlertSettings = false
    @State private var textDraft: NearbyTextDraft?

    var body: some View {
        @Bindable var store = store
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 0) {
                    MembershipCard(name: store.memberFullName, memberSince: store.profile.memberSince)
                        .padding(.horizontal, 20)
                        .padding(.top, 12)

                    stats
                        .padding(.horizontal, 20)
                        .padding(.top, 14)

                    SectionHeader(title: "Your agent", eyebrow: "How Wonder acts for you")
                    VStack(alignment: .leading, spacing: 0) {
                        VStack(alignment: .leading, spacing: 10) {
                            ForEach(AgentAutonomy.allCases) { level in
                                autonomyOption(level)
                            }
                        }
                        .padding(16)

                        Hairline()

                        VStack(alignment: .leading, spacing: 10) {
                            HStack {
                                Text("Approve automatically up to")
                                    .font(WFont.body(14))
                                    .foregroundStyle(Color.ink)
                                Spacer()
                                Text(Fmt.money(Int(store.spendingLimit)))
                                    .font(WFont.display(16))
                                    .foregroundStyle(Color.ink)
                                    .contentTransition(.numericText())
                            }
                            Slider(value: $store.spendingLimit, in: 5_000...150_000, step: 5_000)
                                .tint(Color.verified)
                        }
                        .padding(16)

                        Hairline()
                        toggle("Proactive rebooking", "Switch to better flights automatically", $store.proactiveRebooking)
                        Hairline().padding(.leading, 16)
                        toggle("Upgrade watch", "Bid and clear upgrades for you", $store.upgradeWatch)
                        Hairline().padding(.leading, 16)
                        toggle("Quiet hours", "Only urgent messages 22:00 – 07:00", $store.quietHours)
                    }
                    .glassPanel(cornerRadius: 22)
                    .padding(.horizontal, 20)

                    SectionHeader(title: "Preferences", eyebrow: "Learned from 12 journeys")
                    VStack(spacing: 0) {
                        pickerRow("Cabin", selection: $store.cabin, options: ["First", "Business", "Private"])
                        Hairline().padding(.leading, 16)
                        pickerRow("Seat", selection: $store.seat, options: ["Window", "Aisle"])
                        Hairline().padding(.leading, 16)
                        infoRow("Hotel style", store.profile.hotelStyle)
                        Hairline().padding(.leading, 16)
                        infoRow("Dining", store.profile.dining)
                        Hairline().padding(.leading, 16)
                        infoRow("Loyalty", store.profile.loyalty.joined(separator: " · "))
                    }
                    .glassPanel(cornerRadius: 22)
                    .padding(.horizontal, 20)

                    SectionHeader(title: "Wonder for Business", eyebrow: store.company)
                    VStack(spacing: 0) {
                        infoRow("Travelers on account", "14")
                        Hairline().padding(.leading, 16)
                        infoRow("Travel policy", "Business class > 6h")
                        Hairline().padding(.leading, 16)
                        infoRow("Billing", "Consolidated monthly")
                        Hairline().padding(.leading, 16)
                        infoRow("Account director", "Your agent + Juliette R.")
                    }
                    .glassPanel(cornerRadius: 22)
                    .padding(.horizontal, 20)

                    SectionHeader(title: "Documents", eyebrow: "Stored securely on device")
                    VStack(spacing: 0) {
                        documentRow("Passport", "Verified · expires 2031")
                        Hairline().padding(.leading, 16)
                        documentRow("Global Entry", "Active")
                        Hairline().padding(.leading, 16)
                        documentRow("Travel insurance", "Annual · worldwide")
                    }
                    .glassPanel(cornerRadius: 22)
                    .padding(.horizontal, 20)

                    alertSettings
                        .padding(.horizontal, 20)
                        .padding(.top, 24)

                    Button("Replay introduction") { store.resetDemo() }
                        .font(WFont.body(13))
                        .foregroundStyle(Color.textSoft)
                        .frame(maxWidth: .infinity)
                        .padding(.top, 32)

                    Text("Go somewhere\nthat stays with you.")
                        .font(WFont.display(18))
                        .italic()
                        .multilineTextAlignment(.center)
                        .foregroundStyle(Color.textSoft.opacity(0.8))
                        .frame(maxWidth: .infinity)
                        .padding(.top, 24)
                        .padding(.bottom, 40)
                }
            }
            .statusBarScrim(.black.opacity(0.25))
            .background { Backdrop(photo: Pic.aboveClouds, veil: 0.5) }
            .toolbar(.hidden, for: .navigationBar)
        }
    }

    /// Tucked away: collapsed until opened.
    private var alertSettings: some View {
        @Bindable var alerts = alerts
        return DisclosureGroup(isExpanded: $showAlertSettings) {
            VStack(spacing: 0) {
                Hairline()
                toggle("Location updates", "Tell me when something good is nearby", $alerts.alertsEnabled)
                if alerts.alertsEnabled {
                    Hairline().padding(.leading, 16)
                    pickerRow("Send by", selection: Binding(
                        get: { alerts.channel.title },
                        set: { title in alerts.channel = AlertChannel.allCases.first { $0.title == title } ?? .push }
                    ), options: AlertChannel.allCases.map(\.title))
                    if alerts.channel == .text {
                        Hairline().padding(.leading, 16)
                        HStack {
                            Text("Number").font(WFont.body(14)).foregroundStyle(Color.ink)
                            Spacer()
                            TextField("(555) 555-5555", text: $alerts.phone)
                                .keyboardType(.phonePad)
                                .textContentType(.telephoneNumber)
                                .multilineTextAlignment(.trailing)
                                .font(WFont.body(14))
                                .foregroundStyle(Color.ink)
                        }
                        .padding(.horizontal, 16)
                        .padding(.vertical, 12)
                        if alerts.e164Phone == nil {
                            note("Enter a US number or an international number starting with + and the country code.")
                        }
                        note("Texts stay on your device until you review them and tap Send. No automatic SMS relay is used.")
                        if NearbyModel.shared.top != nil, alerts.e164Phone != nil {
                            Button("Review nearby text") { textDraft = NearbyModel.shared.makeTextDraft() }
                                .disabled(!MFMessageComposeViewController.canSendText())
                            if !MFMessageComposeViewController.canSendText() {
                                note("Text messaging is unavailable on this device. Nearby notifications still work when permitted.")
                            }
                        }
                    }
                }
                Hairline().padding(.leading, 16)
                HStack {
                    Text("New suggestions every").font(WFont.body(14)).foregroundStyle(Color.ink)
                    Spacer()
                    Menu {
                        ForEach(NearbyAlertSettings.intervals, id: \.seconds) { option in
                            Button(option.label) { alerts.intervalSeconds = option.seconds }
                        }
                    } label: {
                        Text(NearbyAlertSettings.intervals.first { $0.seconds == alerts.intervalSeconds }?.label ?? "Custom")
                            .font(WFont.body(14, weight: .medium))
                            .foregroundStyle(Color.verified)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
                note("Refreshes while Wonder is open.")
            }
        } label: {
            Text("Nearby alerts").font(WFont.body(14)).foregroundStyle(Color.ink)
        }
        .tint(Color.textSoft)
        .padding(16)
        .glassPanel(cornerRadius: 22)
        .onChange(of: alerts.intervalSeconds) { _, _ in NearbyModel.shared.configureAutoRefresh() }
        .onChange(of: alerts.alertsEnabled) { _, _ in
            NearbyModel.shared.configureAutoRefresh()
        }
        .sheet(item: $textDraft) { draft in
            NearbyTextComposer(draft: draft) { textDraft = nil }
        }
    }

    private func note(_ text: String) -> some View {
        Text(text)
            .font(WFont.body(12))
            .foregroundStyle(Color.textSoft)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 16)
            .padding(.bottom, 10)
    }

    private var stats: some View {
        HStack(spacing: 0) {
            stat("\(store.trips.count + 7)", "Journeys")
            stat("9", "Countries")
            stat("\(store.hoursSaved)h", "Saved")
        }
        .padding(.vertical, 16)
        .glassPanel(cornerRadius: 20)
    }

    private func stat(_ value: String, _ label: String) -> some View {
        VStack(spacing: 4) {
            Text(value).font(WFont.display(24)).foregroundStyle(Color.ink)
            Eyebrow(label, color: .textSoft, size: 9)
        }
        .frame(maxWidth: .infinity)
    }

    private func autonomyOption(_ level: AgentAutonomy) -> some View {
        let selected = store.autonomy == level
        return Button {
            withAnimation(.spring(duration: 0.3)) { store.autonomy = level }
        } label: {
            HStack(alignment: .top, spacing: 12) {
                Image(systemName: selected ? "checkmark.circle.fill" : "circle")
                    .font(.system(size: 18))
                    .foregroundStyle(selected ? Color.verified : Color.gray.opacity(0.6))
                VStack(alignment: .leading, spacing: 3) {
                    Text(level.rawValue)
                        .font(WFont.body(15, weight: .medium))
                        .foregroundStyle(Color.ink)
                    Text(level.detail)
                        .font(WFont.body(12))
                        .foregroundStyle(Color.textSoft)
                        .multilineTextAlignment(.leading)
                }
                Spacer(minLength: 0)
            }
            .padding(12)
            .background(selected ? Color.verified.opacity(0.12) : .clear, in: .rect(cornerRadius: 14))
            .contentShape(.rect)
        }
        .buttonStyle(.plain)
    }

    private func toggle(_ title: String, _ detail: String, _ isOn: Binding<Bool>) -> some View {
        Toggle(isOn: isOn) {
            VStack(alignment: .leading, spacing: 2) {
                Text(title).font(WFont.body(14)).foregroundStyle(Color.ink)
                Text(detail).font(WFont.body(12)).foregroundStyle(Color.textSoft)
            }
        }
        .tint(Color.verified)
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
    }

    private func pickerRow(_ title: String, selection: Binding<String>, options: [String]) -> some View {
        HStack {
            Text(title).font(WFont.body(14)).foregroundStyle(Color.ink)
            Spacer()
            HStack(spacing: 6) {
                ForEach(options, id: \.self) { option in
                    let on = selection.wrappedValue == option
                    Button {
                        withAnimation(.spring(duration: 0.25)) { selection.wrappedValue = option }
                    } label: {
                        Text(option)
                            .font(WFont.body(13, weight: on ? .semibold : .regular))
                            .foregroundStyle(on ? Color.white : Color.gray)
                            .padding(.horizontal, 12)
                            .frame(height: 32)
                            .background(on ? Color.verified : Color.gray.opacity(0.15), in: .capsule)
                    }
                    .buttonStyle(.plain)
                }
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 10)
    }

    private func infoRow(_ title: String, _ value: String) -> some View {
        HStack {
            Text(title).font(WFont.body(14)).foregroundStyle(Color.ink)
            Spacer()
            Text(value)
                .font(WFont.body(13))
                .foregroundStyle(Color.textSoft)
                .multilineTextAlignment(.trailing)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 14)
    }

    private func documentRow(_ title: String, _ value: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: "checkmark.shield.fill")
                .foregroundStyle(Color.verified)
            Text(title).font(WFont.body(14)).foregroundStyle(Color.ink)
            Spacer()
            Text(value).font(WFont.body(13)).foregroundStyle(Color.textSoft)
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 14)
    }
}

struct MembershipCard: View {
    let name: String
    let memberSince: Int

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            HStack {
                WonderLogo(height: 24, color: .white)
                Spacer()
                Eyebrow("Private", color: .ink.opacity(0.8))
            }
            Spacer()
            Text(name)
                .font(WFont.display(22))
                .foregroundStyle(Color.ink)
            HStack {
                Text("Member since \(String(memberSince))")
                Spacer()
                Text("Concierge 24/7")
            }
            .font(WFont.mono(10))
            .foregroundStyle(Color.ink.opacity(0.55))
            .padding(.top, 6)
        }
        .padding(22)
        .frame(maxWidth: .infinity, alignment: .leading)
        .frame(height: 210)
        .background {
            ZStack {
                Color.black.opacity(0.82)
                // Topographic flourish, echoing the brand board.
                ForEach(0..<7) { i in
                    Ellipse()
                        .stroke(Color.ink.opacity(0.1), lineWidth: 0.75)
                        .frame(width: 180 + CGFloat(i) * 46, height: 120 + CGFloat(i) * 30)
                        .offset(x: 110 - CGFloat(i) * 10, y: -10 - CGFloat(i) * 6)
                }
            }
        }
        .clipShape(.rect(cornerRadius: 24))
        .overlay(RoundedRectangle(cornerRadius: 24).strokeBorder(Color.ink.opacity(0.18), lineWidth: 0.5))
        .shadow(color: Color.black.opacity(0.4), radius: 24, y: 14)
    }
}
