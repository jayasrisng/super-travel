import SwiftUI

struct OnboardingView: View {
    @Environment(WonderStore.self) private var store
    @State private var page = 0
    @State private var appeared = false

    private let styles = [
        ("Slow & restorative", "leaf"),
        ("Culture & cuisine", "fork.knife"),
        ("Adventure", "mountain.2"),
        ("Family", "figure.2.and.child.holdinghands"),
        ("Island time", "sun.max"),
        ("Business & offsites", "briefcase"),
    ]

    var body: some View {
        ZStack {
            GeometryReader { geo in
                Photo(id: page == 0 ? Pic.nycDusk : Pic.aboveClouds, width: 1400)
                    .frame(width: geo.size.width, height: geo.size.height)
                    .scaleEffect(appeared ? 1.0 : 1.08)
                    .animation(.easeOut(duration: 6), value: appeared)
                    .id(page)
                    .transition(.opacity)
            }
            .ignoresSafeArea()

            LinearGradient(
                stops: [
                    .init(color: .black.opacity(0.4), location: 0),
                    .init(color: .black.opacity(0.0), location: 0.3),
                    .init(color: .black.opacity(0.2), location: 0.6),
                    .init(color: .black.opacity(0.7), location: 1),
                ],
                startPoint: .top, endPoint: .bottom
            )
            .ignoresSafeArea()

            Group {
                if page == 0 { welcome } else { preferences }
            }
            .transition(.asymmetric(insertion: .move(edge: .trailing).combined(with: .opacity), removal: .opacity))
        }
        .preferredColorScheme(.dark)
        .onAppear { appeared = true }
    }

    private var welcome: some View {
        VStack(alignment: .leading, spacing: 0) {
            VStack(alignment: .leading, spacing: 10) {
                WonderLogo(height: 46)
                Eyebrow("Your personal travel concierge", color: .ink.opacity(0.85))
            }
            .padding(.top, 24)

            Spacer()

            VStack(alignment: .leading, spacing: 18) {
                Text("The world,\neffortlessly.")
                    .font(WFont.display(44))
                    .foregroundStyle(Color.ink)
                    .lineSpacing(-4)
                Text("Intelligent planning. Extraordinary places.\nA more meaningful way to travel.")
                    .font(WFont.body(15))
                    .foregroundStyle(Color.ink.opacity(0.75))
                    .lineSpacing(4)
            }
            .opacity(appeared ? 1 : 0)
            .offset(y: appeared ? 0 : 18)
            .animation(.easeOut(duration: 1).delay(0.3), value: appeared)

            Button {
                withAnimation(.spring(duration: 0.6)) { page = 1 }
            } label: {
                HStack {
                    Text("Begin")
                    Image(systemName: "arrow.right").font(.system(size: 13, weight: .semibold))
                }
            }
            .buttonStyle(PrimaryButtonStyle())
            .padding(.top, 36)

            Text("By invitation · Wonder Private")
                .font(WFont.body(12))
                .foregroundStyle(Color.ink.opacity(0.5))
                .frame(maxWidth: .infinity)
                .padding(.top, 16)
        }
        .padding(.horizontal, 28)
        .padding(.bottom, 12)
    }

    private var preferences: some View {
        @Bindable var store = store
        return VStack(alignment: .leading, spacing: 0) {
            HStack {
                Button {
                    withAnimation(.spring(duration: 0.5)) { page = 0 }
                } label: {
                    Image(systemName: "chevron.left")
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundStyle(Color.ink)
                        .frame(width: 44, height: 44)
                        .glassCapsule()
                }
                Spacer()
                WonderLogo(height: 20)
                Spacer()
                Color.clear.frame(width: 44, height: 44)
            }
            .padding(.top, 8)

            Spacer()

            Eyebrow("Meet your agent", color: .ink)
            Text("How do you like\nto travel?")
                .font(WFont.display(38))
                .foregroundStyle(Color.ink)
                .padding(.top, 12)
            Text("Your Wonder agent learns your taste, then plans, books and watches over every journey — around the clock.")
                .font(WFont.body(15))
                .foregroundStyle(Color.ink.opacity(0.75))
                .lineSpacing(3)
                .padding(.top, 12)

            FlowLayout(spacing: 10) {
                ForEach(styles, id: \.0) { style in
                    let selected = store.travelStyles.contains(style.0)
                    Button {
                        withAnimation(.spring(duration: 0.3)) {
                            if selected { store.travelStyles.remove(style.0) } else { store.travelStyles.insert(style.0) }
                        }
                    } label: {
                        HStack(spacing: 8) {
                            Image(systemName: style.1).font(.system(size: 13))
                            Text(style.0).font(WFont.body(14, weight: .medium))
                        }
                        .foregroundStyle(SolidInk(inverse: selected))
                        .padding(.horizontal, 16)
                        .frame(height: 42)
                        .background {
                            if selected { Capsule().fill(.solidInk) }
                        }
                        .overlay(Capsule().strokeBorder(Color.ink.opacity(selected ? 0 : 0.35), lineWidth: 1))
                    }
                    .buttonStyle(PressableStyle())
                }
            }
            .padding(.top, 28)

            Button {
                store.hasOnboarded = true
            } label: {
                Text("Enter Wonder")
            }
            .buttonStyle(PrimaryButtonStyle())
            .padding(.top, 36)
            .padding(.bottom, 12)
        }
        .padding(.horizontal, 28)
    }
}

/// Simple wrapping layout for chips.
struct FlowLayout: Layout {
    var spacing: CGFloat = 8

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let rows = arrange(width: proposal.width ?? .infinity, subviews: subviews)
        let height = rows.last.map { $0.y + $0.height } ?? 0
        return CGSize(width: proposal.width ?? rows.map(\.width).max() ?? 0, height: height)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let rows = arrange(width: bounds.width, subviews: subviews)
        for row in rows {
            var x = bounds.minX
            for index in row.indices {
                let size = subviews[index].sizeThatFits(.unspecified)
                subviews[index].place(at: CGPoint(x: x, y: bounds.minY + row.y), proposal: ProposedViewSize(size))
                x += size.width + spacing
            }
        }
    }

    private struct Row { var indices: [Int] = []; var y: CGFloat = 0; var width: CGFloat = 0; var height: CGFloat = 0 }

    private func arrange(width: CGFloat, subviews: Subviews) -> [Row] {
        var rows: [Row] = [Row()]
        var y: CGFloat = 0
        for (i, sub) in subviews.enumerated() {
            let size = sub.sizeThatFits(.unspecified)
            if rows[rows.count - 1].width + size.width > width, !rows[rows.count - 1].indices.isEmpty {
                y += rows[rows.count - 1].height + spacing
                rows.append(Row(y: y))
            }
            rows[rows.count - 1].indices.append(i)
            rows[rows.count - 1].width += size.width + spacing
            rows[rows.count - 1].height = max(rows[rows.count - 1].height, size.height)
        }
        return rows
    }
}
