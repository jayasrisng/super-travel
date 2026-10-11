import WidgetKit
import SwiftUI
import ActivityKit

/// Lock Screen and Dynamic Island card: the agent's pick on top, categories below.
struct NearbyLiveActivityWidget: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: NearbyActivityAttributes.self) { context in
            NearbyLockScreenView(state: context.state)
                .activityBackgroundTint(Color.black.opacity(0.55))
                .activitySystemActionForegroundColor(.white)
                .widgetURL(URL(string: "wonder://nearby"))
        } dynamicIsland: { context in
            let state = context.state
            return DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    WonderMark(color: .white)
                        .frame(width: 34, height: 21)
                        .padding(.leading, 4)
                }
                DynamicIslandExpandedRegion(.trailing) {
                    if let pick = state.pick {
                        Text("\(pick.walkMinutes) min")
                            .font(.system(size: 14, weight: .semibold))
                            .padding(.trailing, 4)
                    }
                }
                DynamicIslandExpandedRegion(.center) {
                    VStack(spacing: 1) {
                        Text(state.pick?.name ?? "Finding something nearby")
                            .font(.system(size: 16, design: .serif))
                            .lineLimit(1)
                        if let pick = state.pick {
                            Text(pick.kind).font(.system(size: 11)).opacity(0.7)
                        }
                    }
                }
                DynamicIslandExpandedRegion(.bottom) {
                    CategoryButtons(selected: state.category) { NearbyLiveCategoryIntent(category: $0) }
                        .padding(.top, 6)
                }
            } compactLeading: {
                WonderMark(color: .white)
                    .frame(width: 24, height: 15)
            } compactTrailing: {
                HStack(spacing: 3) {
                    Image(systemName: state.category.symbol)
                    if let pick = state.pick { Text("\(pick.walkMinutes)m") }
                }
                .font(.system(size: 12, weight: .semibold))
            } minimal: {
                Image(systemName: state.category.symbol)
            }
            .widgetURL(URL(string: "wonder://nearby"))
        }
    }
}

struct NearbyLockScreenView: View {
    let state: NearbyActivityAttributes.ContentState

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 7) {
                WonderMark(color: .white)
                    .frame(width: 28, height: 17)
                Text(["WONDER · NEARBY", state.locality?.uppercased()].compactMap { $0 }.joined(separator: " · "))
                    .font(.system(size: 10, weight: .semibold))
                    .tracking(1.6)
                    .lineLimit(1)
                    .opacity(0.8)
                Spacer(minLength: 0)
            }

            // The main recommendation the agent found.
            if let pick = state.pick {
                HStack(alignment: .center, spacing: 12) {
                    VStack(alignment: .leading, spacing: 3) {
                        Text("AGENT’S PICK · \(state.category.title.uppercased())")
                            .font(.system(size: 8.5, weight: .semibold))
                            .tracking(1.4)
                            .opacity(0.65)
                        Text(pick.name)
                            .font(.system(size: 21, design: .serif))
                            .lineLimit(1)
                            .minimumScaleFactor(0.8)
                        Text(pick.note)
                            .font(.system(size: 12))
                            .opacity(0.8)
                            .lineLimit(2)
                    }
                    Spacer(minLength: 0)
                    VStack(spacing: 0) {
                        Text("\(pick.walkMinutes)")
                            .font(.system(size: 24, design: .serif))
                        Text("MIN")
                            .font(.system(size: 8, weight: .semibold))
                            .tracking(1.2)
                            .opacity(0.7)
                    }
                    .frame(width: 52, height: 52)
                    .background(.white.opacity(0.14), in: .circle)
                }
            } else {
                VStack(alignment: .leading, spacing: 3) {
                    Text("Looking around you…")
                        .font(.system(size: 19, design: .serif))
                    Text("Your agent is checking what’s open nearby.")
                        .font(.system(size: 12))
                        .opacity(0.75)
                }
            }

            CategoryButtons(selected: state.category) { NearbyLiveCategoryIntent(category: $0) }
        }
        .padding(16)
        .foregroundStyle(.white)
    }
}
