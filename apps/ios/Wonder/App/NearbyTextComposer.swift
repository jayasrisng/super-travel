import SwiftUI
import MessageUI

struct NearbyTextDraft: Identifiable {
    let id: String
    let recipient: String
    let body: String
}

struct NearbyTextComposer: UIViewControllerRepresentable {
    let draft: NearbyTextDraft
    let completion: () -> Void

    func makeCoordinator() -> Coordinator { Coordinator(completion: completion) }
    func makeUIViewController(context: Context) -> MFMessageComposeViewController {
        let controller = MFMessageComposeViewController()
        controller.messageComposeDelegate = context.coordinator
        controller.recipients = [draft.recipient]
        controller.body = draft.body
        return controller
    }
    func updateUIViewController(_ controller: MFMessageComposeViewController, context: Context) {}

    final class Coordinator: NSObject, MFMessageComposeViewControllerDelegate {
        let completion: () -> Void
        init(completion: @escaping () -> Void) { self.completion = completion }
        func messageComposeViewController(_ controller: MFMessageComposeViewController, didFinishWith result: MessageComposeResult) {
            // Closing the composer never fabricates a sent-message confirmation.
            completion()
        }
    }
}
