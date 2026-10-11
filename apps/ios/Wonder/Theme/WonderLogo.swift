import SwiftUI

/// Mark plus the bold sans wordmark, as on the logo sheet.
struct WonderLogo: View {
    var height: CGFloat = 28
    var color: Color = .ink
    var showsMark = true

    var body: some View {
        HStack(alignment: .center, spacing: height * 0.18) {
            if showsMark {
                WonderMark(color: color)
                    .frame(width: height * 1.6, height: height)
            }
            Text("Wonder")
                .font(.system(size: height * 0.92, weight: .bold))
                .tracking(-height * 0.02)
                .foregroundStyle(color)
                .offset(y: height * 0.12)
        }
        .accessibilityElement()
        .accessibilityLabel("Wonder")
    }
}

/// Black square with a white serif W — the app's compact monogram.
struct MonogramTile: View {
    var size: CGFloat = 42

    var body: some View {
        Text("W")
            .font(WFont.wordmark(size * 0.5))
            .foregroundStyle(.white)
            .frame(width: size, height: size)
            .background(.black, in: .rect(cornerRadius: size * 0.26))
    }
}
