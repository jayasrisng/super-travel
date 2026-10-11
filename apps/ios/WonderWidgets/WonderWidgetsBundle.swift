import WidgetKit
import SwiftUI

@main
struct WonderWidgetsBundle: WidgetBundle {
    var body: some Widget {
        NearbyWidget()
        NearbyLiveActivityWidget()
    }
}
