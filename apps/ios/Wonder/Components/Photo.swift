import SwiftUI
import UIKit

/// Lightweight in-memory image pipeline with request de-duplication.
final class ImagePipeline {
    static let shared = ImagePipeline()

    private let cache = NSCache<NSURL, UIImage>()
    private var inFlight: [URL: Task<UIImage?, Never>] = [:]
    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.urlCache = URLCache(memoryCapacity: 32 << 20, diskCapacity: 256 << 20)
        config.requestCachePolicy = .returnCacheDataElseLoad
        return URLSession(configuration: config)
    }()

    func cached(_ url: URL) -> UIImage? {
        cache.object(forKey: url as NSURL)
    }

    func image(for url: URL) async -> UIImage? {
        if let hit = cached(url) { return hit }
        if let task = inFlight[url] { return await task.value }

        let session = self.session
        let task = Task<UIImage?, Never> {
            guard let (data, _) = try? await session.data(from: url),
                  let image = UIImage(data: data) else { return nil }
            return await image.byPreparingForDisplay() ?? image
        }
        inFlight[url] = task
        let image = await task.value
        inFlight[url] = nil
        if let image { cache.setObject(image, forKey: url as NSURL) }
        return image
    }

    func prefetch(_ ids: [String], width: Int = 1200) {
        for id in ids {
            let url = Photo.url(for: id, width: width)
            Task { _ = await image(for: url) }
        }
    }
}

/// Editorial photograph that fills whatever frame its parent gives it.
struct Photo: View {
    let id: String
    var width: Int = 1200

    @State private var image: UIImage?

    static func url(for id: String, width: Int) -> URL {
        URL(string: "https://images.unsplash.com/photo-\(id)?w=\(width)&q=80&auto=format&fit=crop")!
    }

    private var url: URL { Self.url(for: id, width: width) }

    var body: some View {
        Rectangle()
            .fill(
                LinearGradient(
                    colors: [Color(hex: 0x1C1C1E), Color.black],
                    startPoint: .top, endPoint: .bottom
                )
            )
            .overlay {
                if let image {
                    Image(uiImage: image)
                        .resizable()
                        .scaledToFill()
                        .transition(.opacity)
                }
            }
            .clipped()
            .task(id: url) {
                if let hit = ImagePipeline.shared.cached(url) {
                    image = hit
                    return
                }
                let loaded = await ImagePipeline.shared.image(for: url)
                withAnimation(.easeOut(duration: 0.45)) { image = loaded }
            }
    }
}

/// Bottom-weighted scrim to keep type legible over photography.
struct Scrim: View {
    var color: Color = .black
    var strength: Double = 0.85

    var body: some View {
        LinearGradient(
            stops: [
                .init(color: color.opacity(0), location: 0.35),
                .init(color: color.opacity(strength * 0.55), location: 0.7),
                .init(color: color.opacity(strength), location: 1),
            ],
            startPoint: .top, endPoint: .bottom
        )
    }
}
