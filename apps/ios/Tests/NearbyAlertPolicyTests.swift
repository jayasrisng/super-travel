import Foundation

@main
struct NearbyAlertPolicyTests {
    static func main() {
        precondition(!NearbyAlertPolicy.canRefresh(enabled: false, interval: 300, foreground: true))
        precondition(!NearbyAlertPolicy.canRefresh(enabled: true, interval: 300, foreground: false))
        precondition(!NearbyAlertPolicy.canRefresh(enabled: true, interval: 0, foreground: true))
        precondition(!NearbyAlertPolicy.canRefresh(enabled: true, interval: -1, foreground: true))
        precondition(!NearbyAlertPolicy.canRefresh(enabled: true, interval: 1, foreground: true))
        precondition(NearbyAlertPolicy.canRefresh(enabled: true, interval: 300, foreground: true))
        precondition(NearbyAlertPolicy.phone("(415) 555-0123") == "+14155550123")
        precondition(NearbyAlertPolicy.phone("+34 612 345 678") == "+34612345678")
        precondition(NearbyAlertPolicy.phone("+0 612345678") == nil)
        precondition(NearbyAlertPolicy.phone("+1415555012345678") == nil)
        precondition(NearbyAlertPolicy.phone("4155550123 bad") == nil)
        precondition(NearbyAlertPolicy.phone("＋１４１５５５５０１２３") == nil)
        precondition(NearbyAlertPolicy.phone("++14155550123") == nil)
        precondition(NearbyAlertPolicy.phone("0123456789") == nil)
        var delivery = NearbyDeliveryLedger()
        precondition(delivery.shouldDeliver("pick-a"))
        delivery.record("pick-a", succeeded: false)
        precondition(delivery.shouldDeliver("pick-a"))
        delivery.record("pick-a", succeeded: true)
        precondition(!delivery.shouldDeliver("pick-a"))
        precondition(delivery.shouldDeliver("pick-b"))
        print("18 nearby alert policy assertions passed")
    }
}
